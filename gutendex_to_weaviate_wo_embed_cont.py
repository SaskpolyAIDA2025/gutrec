import requests
import weaviate
from weaviate.auth import AuthApiKey
import os
import time

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
    additional_headers={}  # no OpenAI key needed, vectorizer=None
)

# -----------------------
# Ensure Book class exists with vectorizer:none
# -----------------------
book_class = {
    "class": "Book",
    "description": "A book from Project Gutenberg",
    "vectorizer": "none",  # no AI/vectorization needed
    "properties": [
        {"name": "title", "dataType": ["text"]},
        {"name": "authors", "dataType": ["text"]},
        {"name": "translators", "dataType": ["text"]},
        {"name": "subjects", "dataType": ["text"]},
        {"name": "bookshelves", "dataType": ["text"]},
        {"name": "languages", "dataType": ["text"]},
        {"name": "copyright", "dataType": ["text"]},
        {"name": "media_type", "dataType": ["text"]},
        {"name": "download_count", "dataType": ["int"]},
        {"name": "summaries", "dataType": ["text"]}
    ]
}

existing_classes = [c["class"] for c in client.schema.get()["classes"]]
if "Book" not in existing_classes:
    client.schema.create_class(book_class)
    print("✅ Book class created")
else:
    print("ℹ️ Book class already exists")

# -----------------------
# Fetch books from Gutendex
# -----------------------
API_URL = "https://gutendex.com/books"

def fetch_books(max_books=100, batch_size=20):
    next_url = API_URL
    books_inserted = 0
    books_to_batch = []

    while next_url and books_inserted < max_books:
        response = requests.get(next_url)
        data = response.json()

        for book in data.get("results", []):
            if books_inserted >= max_books:
                break

            properties = {
                "title": str(book.get("title", "")),
                "authors": "; ".join([str(a.get("name", "")) for a in book.get("authors", [])]),
                "translators": "; ".join([str(t.get("name", "")) for t in book.get("translators", [])]),
                "subjects": "; ".join([str(s) for s in book.get("subjects", [])]),
                "bookshelves": "; ".join([str(b) for b in book.get("bookshelves", [])]),
                "languages": "; ".join([str(l) for l in book.get("languages", [])]),
                "copyright": str(book.get("copyright")) if book.get("copyright") else "",
                "media_type": str(book.get("media_type", "")),
                "download_count": int(book.get("download_count", 0)),
                "summaries": "; ".join([str(s) for s in book.get("summaries", [])])
            }

            books_to_batch.append(properties)
            books_inserted += 1

            # Send batch if full
            if len(books_to_batch) >= batch_size:
                with client.batch as batch:
                    batch.batch_size = batch_size
                    for b in books_to_batch:
                        batch.add_data_object(b, "Book")
                books_to_batch = []

        next_url = data.get("next")

    # Insert any remaining books
    if books_to_batch:
        with client.batch as batch:
            batch.batch_size = batch_size
            for b in books_to_batch:
                batch.add_data_object(b, "Book")

    print(f"✅ Finished inserting {books_inserted} books into Weaviate.")

# -----------------------
# Main
# -----------------------
if __name__ == "__main__":
    fetch_books(max_books=100, batch_size=20)
    client.close()
    print("✅ Weaviate connection closed")