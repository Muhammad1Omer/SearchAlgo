import streamlit as st
import os
from datetime import datetime

def add_document(title, content, doc_type):
    if not title or not content or not doc_type:
        st.error("Title, content, and document type cannot be empty.")
        return False
    
    try:
        # Ensure "Files" directory exists
        os.makedirs("Files", exist_ok=True)
        
        # Define the file path
        file_path = os.path.join("Files", f"{title}.txt")
        
        # Write content to the file with UTF-8 encoding
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"Title: {title}\n")
            file.write(f"Type: {doc_type}\n")
            file.write(f"Uploaded At: {datetime.now()}\n")
            file.write("\nContent:\n")
            file.write(content)
        
        st.success("Document saved successfully!")
        return True

    except Exception as e:
        st.error(f"Error while saving document: {e}")
        return False

# Streamlit UI
st.title("Add Documents")

input_method = st.radio("Choose how to add your document:", ('Upload a File', 'Type Manually'))

# Input for document title and type
title = st.text_input("Document Title")
doc_type = st.selectbox("Document Type", ["Report", "Memo", "Article", "Essay", "Other"])

# Content input based on chosen method
if input_method == 'Upload a File':
    uploaded_file = st.file_uploader("Choose a text file", type=["txt"])
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8", errors="replace")
else:
    content = st.text_area("Type your document here:")

# Button to add document
if st.button("Add Document"):
    if add_document(title, content, doc_type):
        st.success("Document added successfully!")
    else:
        st.error("Failed to add document.")
