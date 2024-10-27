import streamlit as st
import mysql.connector
import re
from datetime import datetime

# Database connection parameters
DB_HOST = 'sql12.freesqldatabase.com'
DB_NAME = 'sql12741043'
DB_USER = 'sql12741043'
DB_PASS = 'NLzNvI2xMP'
DB_PORT = 3306  

def add_document(title, content):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cursor = conn.cursor()
        query = """
        INSERT INTO documents (title, content, uploaded_at)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (title, content, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# Function to find a word in the documents
def find_word_in_documents(documents, asked):
    found = False
    results = []

    for k, row in enumerate(documents):
        doc = row[2]  # Accessing the document content
        sentences = re.split(r'\r?\n', doc)

        for i, sentence in enumerate(sentences):
            for j, word in enumerate(sentence.split()):
                if word == asked:
                    results.append(f"Found at Document: {k + 1}, Sentence: {i + 1}, Word: {j + 1}")
                    found = True

    if not found:
        results.append("Word doesn't exist in this document.")
    
    return results

def prefix_function(p):
    m = len(p)             
    Pi = [0] * m            
    k = 0                   

    for q in range(1, m):
        while k > 0 and p[k] != p[q]:
            k = Pi[k - 1]

        if p[k] == p[q]:
            k += 1 

        Pi[q] = k  

    return Pi

def find_word_KMP(documents, word):
    Pi = prefix_function(word)
    wordLen = len(word)
    results = []

    for l, row in enumerate(documents):
        doc = row[2]
        docLen = len(doc)
        k = 0

        for i in range(docLen):
            while k > 0 and word[k] != doc[i]:
                k = Pi[k - 1]
            if word[k] == doc[i]:
                k += 1
            if k == wordLen:
                results.append((f"Document {l + 1} occurs at {i - wordLen + 1}"))
                k = Pi[k - 1]
    

# Streamlit UI
st.title("Document Management System")

# Option to select input method for documents
input_method = st.radio("Choose how to add your document:", ('Upload a File', 'Type Manually'))

# Input for document title
title = st.text_input("Document Title")

if input_method == 'Upload a File':
    # File upload widget
    uploaded_file = st.file_uploader("Choose a text file", type=["txt"])
    if uploaded_file is not None:
        # Read the content of the uploaded file
        content = uploaded_file.read().decode("utf-8")
else:
    # Text area for manual input
    content = st.text_area("Type your document here:")

# Button to add document
if st.button("Add Document"):
    if content:  # Ensure content is not empty
        if add_document(title, content):
            st.success("Document added successfully!")
        else:
            st.error("Failed to add document.")
    else:
        st.error("Please provide content for the document.")

# Search functionality
st.header("Search for a Word in Documents")
search_word = st.text_input("Enter a word to search for:")
if st.button("Search"):
    try:
        # Connect to the database and fetch documents
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cursor = conn.cursor()

        query = "SELECT * FROM documents;"
        cursor.execute(query)
        documents = cursor.fetchall()

# ------------AZEEM Idher saay time calculate krr laay---------------------------------
        search_results = find_word_in_documents(documents, search_word)
        
        find_word_KMP(documents, search_word)
        
        # Display search results
        for result in search_results:
            st.write(result)
        
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Error fetching documents: {e}")
