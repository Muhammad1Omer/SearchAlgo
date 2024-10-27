import streamlit as st
import time
import re
import mysql.connector
import matplotlib.pyplot as plt
import numpy as np


# Database connection parameters
DB_HOST = 'sql12.freesqldatabase.com'
DB_NAME = 'sql12741043'
DB_USER = 'sql12741043'
DB_PASS = 'NLzNvI2xMP'
DB_PORT = 3306

# Add custom CSS for styling
st.markdown("""<style>
.stButton>button {
    font-size: 18px;
    padding: 8px 20px;
    margin: 5px;
}
.result-container {
    border: 1px solid #ddd;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    background-color: #f4f4f4;
    font-size: 16px;
}
.highlight {
    color: #e74c3c;
    font-weight: bold;
}
.info-container {
    font-size: 16px;
    margin-bottom: 10px;
}
</style>""", unsafe_allow_html=True)

# Initialize session state variables for navigation
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.results = []
    st.session_state.matched_word_index = 0
    st.session_state.show_summary = True  # To control summary visibility

# Function to highlight search term
def highlight_term(sentence, term, whole_word=False):
    if whole_word:
        pattern = rf"\b(?:{re.escape(term)})\b"
    else:
        pattern = rf"({re.escape(term)})"
    
    highlighted_sentence = re.sub(pattern, r"<span class='highlight'>\g<0></span>", sentence, flags=re.IGNORECASE)
    return highlighted_sentence

# Brute Force Search
def brute_force_search(content, term, whole_word=False, case_sensitive=False):
    results = {}
    term_length = len(term)  # Length of the term being searched

    for line_num, line in enumerate(content):
        line_to_check = line if case_sensitive else line.lower()
        term_to_check = term if case_sensitive else term.lower()
        
        match_count = 0  # Initialize match count for the current line

        # Check for whole word match if specified
        if whole_word:
            words = line_to_check.split()
            for word in words:
                if word == term_to_check:
                    match_count += 1
        else:
            n = len(line_to_check)  # Length of the line
            # Compare letter by letter
            for i in range(n - term_length + 1):
                match = True
                for j in range(term_length):
                    if line_to_check[i + j] != term_to_check[j]:
                        match = False
                        break
                if match:
                    match_count += 1  # Increment match count if a match is found

        if match_count > 0:
            results[line] = {"line_num": line_num + 1, "match_count": match_count}
    return results

# KMP Search Algorithm
def kmp_search(content, term, whole_word=False, case_sensitive=False):
    results = {}
    term_len = len(term)

    def build_kmp_table(term):
        table = [0] * term_len
        j = 0
        for i in range(1, term_len):
            while j > 0 and term[i] != term[j]:
                j = table[j - 1]
            if term[i] == term[j]:
                j += 1
                table[i] = j
        return table

    def search_kmp(line, term, table):
        line_len = len(line)
        j = 0
        count = 0
        i = 0
        while i < line_len:
            if line[i] == term[j]:
                i += 1
                j += 1
            if j == term_len:
                count += 1
                j = table[j - 1]  # reset j using KMP table to find next match
            elif i < line_len and line[i] != term[j]:
                if j != 0:
                    j = table[j - 1]
                else:
                    i += 1
        return count

    for line_num, line in enumerate(content):
        line_to_check = line if case_sensitive else line.lower()
        term_to_check = term if case_sensitive else term.lower()
        table = build_kmp_table(term_to_check)

        if whole_word:
            matches = re.findall(r'\b' + re.escape(term_to_check) + r'\b', line_to_check)
            match_count = len(matches)
        else:
            match_count = search_kmp(line_to_check, term_to_check, table)

        if match_count > 0:
            results[line] = {"line_num": line_num + 1, "match_count": match_count}
    return results

# Connect to the database and fetch content
def fetch_database_content():
    conn = mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM documents")
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]

def upload_to_database(title, content):
    conn = mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cursor = conn.cursor()
    # Insert the title and content into the documents table
    cursor.execute("INSERT INTO documents (title, content) VALUES (%s, %s)", (title, content))
    conn.commit()
    cursor.close()
    conn.close()


# Streamlit GUI
st.title("Word Search Application")
st.write("Search for a specific word across multiple text files or within stored database entries.")



input_method = st.radio("Choose Input Method:", ("Upload Text Files", "Type Your Own Text"))

if input_method == "Upload Text Files":
    uploaded_files = st.file_uploader("Upload Text Files", accept_multiple_files=True, type=["txt"])
    user_input_text = ""
elif input_method == "Type Your Own Text":
    user_input_text = st.text_area("Or, type your own text below:", "")
    uploaded_files = []


# After checking the input method and processing uploaded files
if st.button("Save to Database"):
    if input_method == "Upload Text Files":
        if uploaded_files:
            for file in uploaded_files:
                title = file.name  # Using the file name as the title
                file_content = file.read().decode("utf-8")
                upload_to_database(title, file_content)
            st.success("Files uploaded successfully!")
        else:
            st.error("No files uploaded.")
    elif input_method == "Type Your Own Text":
        if user_input_text.strip():
            title = "User Input Text"  # Title for user input
            upload_to_database(title, user_input_text)
            st.success("Text uploaded successfully!")
        else:
            st.error("No text entered.")

use_database = st.checkbox("Use Database Content")



search_term = st.text_input("Enter search term")
whole_word = st.checkbox("Whole Word Match")
case_sensitive = st.checkbox("Case Sensitive Match")

# Initialization before search
brute_force_time = 0
kmp_time = 0
total_matched_words = 0
unified_results = {}




if st.button("Search"):
    if (not uploaded_files and not use_database and not user_input_text.strip()) or not search_term:
        st.error("Please upload files, use the database, type text, and enter a search term.")
    else:
        st.session_state.current_index = 0
        st.session_state.matched_word_index = 0
        st.session_state.results = []

        # Initialize timing variables here
        brute_force_time = 0
        kmp_time = 0
        total_matched_words = 0
        unified_results = {}

        # Combine user input text into content list
        content = []
        if user_input_text.strip():
            content.extend(user_input_text.splitlines())

        # Process uploaded files
        if uploaded_files:
            for file in uploaded_files:
                file_content = file.read().decode("utf-8").splitlines()
                content.extend(file_content)  # Add file content to the main content list

        # Brute Force Search
        start_time = time.time()
        brute_force_results = brute_force_search(content, search_term, whole_word, case_sensitive)
        brute_force_time += time.time() - start_time

        # KMP Search
        start_time = time.time()
        kmp_results = kmp_search(content, search_term, whole_word, case_sensitive)
        kmp_time += time.time() - start_time

        # Combine results
        for line, details in {**brute_force_results, **kmp_results}.items():
            print(details)
            file_identifier = details.get("file", "User Input Text")
            
            # if details["line_num"] == 0 and user_input_text.strip():
            #     file_identifier = "User Input Text"

            if line not in unified_results:
                unified_results[line] = {
                    "file": file_identifier,
                    "line": details["line_num"],
                    "match_count": details["match_count"],
                    "algorithms": []
                }
            if line in brute_force_results:
                unified_results[line]["algorithms"].append("Brute Force")
            if line in kmp_results:
                unified_results[line]["algorithms"].append("KMP")
            total_matched_words += details["match_count"]


        occurrences_basic = []
        occurrences_kmp = []
        
        search_times_basic = []
        search_times_kmp = []
        
        doc_indices = []
        # Search in database content if selected
        if use_database:
            database_content = fetch_database_content()
            for doc_index, (title, content) in enumerate(database_content):
                doc_indices.append(doc_index)
                
                content_lines = content.splitlines()

                # Brute Force Search
                start_time = time.time()
                brute_force_results = brute_force_search(content_lines, search_term, whole_word, case_sensitive)
                brute_force_time += time.time() - start_time
                search_times_basic.append(time.time() - start_time)
                
                occurrences_basic.append(sum(result["match_count"] for result in brute_force_results.values()))


                # KMP Search
                start_time = time.time()
                kmp_results = kmp_search(content_lines, search_term, whole_word, case_sensitive)
                kmp_time += time.time() - start_time
                search_times_kmp.append(time.time() - start_time)
                
                occurrences_kmp.append(sum(result["match_count"] for result in kmp_results.values()))


                for line, details in {**brute_force_results, **kmp_results}.items():
                    if line not in unified_results:
                        unified_results[line] = {
                            "file": title,
                            "line": details["line_num"],
                            "match_count": details["match_count"],
                            "algorithms": []
                        }
                    if line in brute_force_results:
                        unified_results[line]["algorithms"].append("Brute Force")
                    if line in kmp_results:
                        unified_results[line]["algorithms"].append("KMP")
                    total_matched_words += details["match_count"]

        st.session_state.results = sorted(
            [
                (line, details)
                for line, details in unified_results.items()
            ],
            key=lambda x: (x[1]["file"], x[1]["line"])
        )

        # Store the summary for future display
        st.session_state.search_summary = {
            "search_term": search_term,
            "whole_word": whole_word,
            "case_sensitive": case_sensitive,
            "total_matches": total_matched_words,
            "brute_force_time": brute_force_time,
            "kmp_time": kmp_time
        }

# Display the summary at all times with a button to hide it
if st.session_state.show_summary:
    summary = st.session_state.search_summary
    st.markdown(f"*Search Term:* {summary['search_term']}")
    st.markdown(f"Whole Word Match: *{summary['whole_word']}*")
    st.markdown(f"Case Sensitive Match: *{summary['case_sensitive']}*")
    st.markdown(f"Total Matches: *{summary['total_matches']}*")
    st.markdown(f"Total Brute Force Time: *{summary['brute_force_time']:.4f} seconds*")
    st.markdown(f"Total KMP Time: *{summary['kmp_time']:.4f} seconds*")
    if st.button("Hide Summary"):
        st.session_state.show_summary = False
else:
    if st.button("Show Summary"):
        st.session_state.show_summary = True

# Display the results
if st.session_state.results:
    matched_lines = st.session_state.results
    if st.session_state.current_index < len(matched_lines):
        line, details = matched_lines[st.session_state.current_index]
        highlighted_line = highlight_term(line, search_term, whole_word)

        # Display file title and current matched word number
        current_word_number = st.session_state.current_index + 1
        total_matched = len(matched_lines)

        # Display the match info above the sentence box
        st.markdown(f"""
        <div class='info-container'>
            Current Match: <strong>{current_word_number}/{total_matched}</strong><br>
            Title: <strong>{details['file']}</strong><br>
            Line No: <strong>{details['line']}</strong>
        </div>
        """, unsafe_allow_html=True)

        # Well formatted box containing the sentence
        st.markdown(f"""
        <div class='result-container'>
            {highlighted_line}
        </div>
        """, unsafe_allow_html=True)

        # Navigation buttons in a single row
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.session_state.current_index > 0:
                if st.button("Previous"):
                    st.session_state.current_index -= 1
            else:
                st.button("Previous", disabled=True)  # Disable if at the first result

        with col2:
            if st.session_state.current_index < len(matched_lines) - 1:
                if st.button("Next"):
                    st.session_state.current_index += 1
            else:
                st.button("Next", disabled=True)  # Disable if at the last result
    else:
        st.write("No more results.")
                

if occurrences_basic and occurrences_kmp and  doc_indices:
    fig, ax = plt.subplots(figsize=(12, 8))  # Increased size

    # Determine the maximum occurrences for bubble size calculation
    max_occurrences = max(max(occurrences_basic, default=1), max(occurrences_kmp, default=1))

    # Set x-axis and y-axis labels
    ax.set_xlabel("Document Index")
    ax.set_ylabel("Occurrences", color="gray")
    ax.tick_params(axis="y", labelcolor="gray")

    # Calculate bubble sizes as a fraction of the max occurrences
    bubble_size_basic = (np.array(occurrences_basic) / max_occurrences) * 800
    bubble_size_kmp = (np.array(occurrences_kmp) / max_occurrences) * 800

    # Create bubble scatter plots
    ax.scatter(doc_indices, search_times_basic, s=bubble_size_basic, 
            color='blue', alpha=0.6, edgecolor='black', label="Basic Search Occurrences")
    ax.scatter(doc_indices, search_times_kmp, s=bubble_size_kmp, 
            color='red', alpha=0.6, edgecolor='black', label="KMP Search Occurrences")

    # Add grid, legend, and titles
    ax.set_title("Performance of Basic vs. KMP Search", fontsize=18)
    ax.legend(loc="upper left")
    ax.grid(True)

    # Set y-axis limits dynamically based on the maximum occurrences
    max_occurrence_value = max(max(search_times_basic, default=0), max(search_times_kmp, default=0))
    ax.set_ylim(0, max_occurrence_value * 1.1)  # Add some padding (10%)

    try:
        st.pyplot(fig)
    except ValueError as e:
        st.error(f"An error occurred while plotting: {str(e)}")
else:
    st.error("No data available for plotting.")