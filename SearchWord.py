import streamlit as st
import psycopg2
from datetime import datetime
import re

# Database connection parameters
DB_HOST = 'localhost'
DB_NAME = 'Algo_A3'
DB_USER = 'postgres'
DB_PASS = 'password'


# Function to insert document into the database
def add_document(title, content):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
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



st.header("Search for a Word in Documents")
search_word = st.text_input("Enter a word to search for:")
if st.button("Search"):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()

        query = "SELECT * FROM documents;"
        cursor.execute(query)
        documents = cursor.fetchall()

        # Find the word in the documents
        search_results = find_word_in_documents(documents, search_word)
        
        # Display search results
        for result in search_results:
            st.write(result)
        
        cursor.close()
        conn.close()
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
    if content:  # Ensure content is not empty
        if add_document(title, content):
            st.success("Document added successfully!")
        else:
            st.error("Failed to add document.")
    else:
        st.error("Please provide content for the document.")
