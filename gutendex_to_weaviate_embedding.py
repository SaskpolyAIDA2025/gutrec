import pandas as pd
import requests
import argparse
import weaviate
from weaviate.auth import AuthApiKey
import os
import ast
import math
import re

# -----------------------
# Weaviate Cloud credentials
# -----------------------
WEAVIATE_URL = "https://cywukygmt0k0kyk3dzng.c0.asia-southeast1.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "cXBHd2Z2Zm56NlE3S2xkUF90Y2xIRWF0aXNWdk9Wa29DLzQ1UjRnOGt1Q29ZWnlNY1RhRldpOFNWQXFRPV92MjAw"

# -----------------------
# Connect to Weaviate
# -----------------------
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(api_key=WEAVIATE_API_KEY),
    )

# Test connection
if client.is_ready():
    print("Weaviate is ready")
else:
    raise Exception("Could not connect to Weaviate")

client.schema.delete_class("Book2")

# -----------------------
# Define Book schema
# -----------------------
book2_class = {
    "class": "Book2",
    "description": "A book from Project Gutenberg",
    "vectorizer": "none",
    "properties": [
        {"name": "id_pg", "dataType": ["text"]},
        {"name": "title", "dataType": ["text"]},
        {"name": "authors", "dataType": ["text"]},
        {"name": "translators", "dataType": ["text"]},
        {"name": "subjects", "dataType": ["text"]},
        {"name": "bookshelves", "dataType": ["text"]},
        {"name": "languages", "dataType": ["text"]},
        {"name": "copyright", "dataType": ["text"]},
        #{"name": "media_type", "dataType": ["text"]},
        {"name": "download_count", "dataType": ["int"]},
        {"name": "summaries", "dataType": ["text"]}
    ]
}

# -----------------------
# Check if Book class exists
# -----------------------
try:
    existing_classes = [c["class"] for c in client.schema.get()["classes"]]
except Exception:
    existing_classes = []

if "Book" not in existing_classes:
    client.schema.create_class(book2_class)
    print("Book class created")
else:
    print("Book class already exists")

# -----------------------
# Ollama embedding function
# -----------------------
def embed_text(text):
    payload = {
        "model": "mxbai-embed-large", # "all-minilm", # "nomic-embed-text",
        "prompt": text
    }
    response = requests.post("http://localhost:11434/api/embeddings", json=payload)
    response.raise_for_status()
    return response.json()["embedding"]

# -----------------------
# Clean text
# -----------------------
def clean_text(t):
    if not isinstance(t, str):
        return ""
    t = t.replace("\x00", "")
    t = t.encode("utf-8", "ignore").decode("utf-8")
    t = re.sub(r"[\r\n\t]+", " ", t)
    return t

# -----------------------
# Set a safe string value
# -----------------------
def safe_str(value):
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)

# -----------------------
# Fetch books from Gutendex
# -----------------------
def fetch_books():
    df = pd.read_csv("processed_books.csv")

    books = []

    for i, row in df.iterrows():

        languages = ast.literal_eval(row["languages"])
        bookshelves = ast.literal_eval(row["bookshelves"])
        subjects = ast.literal_eval(row["subjects"])


        # Extract row as a dictionary
        book_dict = {
            "id_pg": safe_str(row["id"]),
            "title": safe_str(row["title"]),
            "authors": safe_str(row["authors"]),
            "translators": safe_str(row["translators"]),
            "subjects": safe_str(row["subjects"]),
            "bookshelves": safe_str(row["bookshelves"]),
            "languages": safe_str(row["languages"]),
            "copyright": safe_str(row["copyright"]),
            #"media_type": safe_str(row["media_type"]),
            "download_count": row["download_count"],
            "summaries": safe_str(row["summaries"])
        }

        # Build embedding text (you can customize this)
        embedding_text = (
            f"Title: {safe_str(row['title'])}. "
            f"Author: {safe_str(row['authors'])}. "
            f"Language: {safe_str(' '.join(languages))}. "
            f"Bookshelves: {safe_str(' '.join(bookshelves))}. "
            f"Subjects: {safe_str(' '.join(subjects))}. "
            f"Summary: {safe_str(row['summaries'])}"
        )

        MAX_LEN = 800
        embedding_text = clean_text(embedding_text)
        #embedding_text = embedding_text[:MAX_LEN]

        try:
            embedding = embed_text(embedding_text)

            client.data_object.create(
                data_object=book_dict,
                class_name="Book2",
                vector=embedding  # REQUIRED for WCS
            )
            print(f"Book number {i} added.")

        except Exception as e:
            print(f"Failed to insert book {row['title']}: {e}")
            print("Embedding text length:", len(embedding_text))
            print("Embedding text preview:", embedding_text[:300])
        
        if i == 5000:
            break

    print(f"Finished fetching books and pushing to Weaviate!")

# -----------------------
# Main script
# -----------------------
if __name__ == "__main__":
    fetch_books()
    print("Done!")
