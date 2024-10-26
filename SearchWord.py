import streamlit as st
import psycopg2
from datetime import datetime
import re

# Database connection parameters
DB_HOST = 'localhost'
DB_NAME = 'Algo_A3'
DB_USER = 'postgres'
DB_PASS = 'password'

# Function to create a database connection
def create_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# Function to insert document into the database
def add_document(title, content):
    if not title or not content:
        st.error("Title and content cannot be empty.")
        return False

    try:
        with create_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                INSERT INTO documents (title, content, uploaded_at)
                VALUES (%s, %s, %s)
                """
                cursor.execute(query, (title, content, datetime.now()))
                conn.commit()
        return True
    except Exception as e:
        st.error(f"Error while adding document: {e}")
        return False

def find_word_in_documents(documents, searched_word):
    results = []
    found = False

    for k, row in enumerate(documents):
        doc_content = row[2]  # Accessing the document content
        sentences = re.split(r'\r?\n', doc_content)

        for i, sentence in enumerate(sentences):
            if searched_word in sentence.split():  # Change to allow partial matches if needed
                results.append(f"Found at Document: {k + 1}, Sentence: {i + 1}")
                found = True

    if not found:
        results.append("Word doesn't exist in this document.")
    
    return results

# Streamlit UI
st.header("Search for a Word in Documents")
search_word = st.text_input("Enter a word to search for:")

if st.button("Search"):
    if not search_word.strip():
        st.error("Please enter a word to search.")
    else:
        try:
            with create_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM documents;")
                    documents = cursor.fetchall()

            # Find the word in the documents
            search_results = find_word_in_documents(documents, search_word)
            
            # Display search results
            if search_results:
                for result in search_results:
                    st.write(result)
            else:
                st.warning("No results found.")
                
        except Exception as e:
            st.error(f"Error fetching documents: {e}")

st.title("Search Documents")

# Option to select input method
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
    if add_document(title, content):
        st.success("Document added successfully!")
    else:
        st.error("Failed to add document.")
