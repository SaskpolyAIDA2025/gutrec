import requests
import argparse
import weaviate
from weaviate.auth import AuthApiKey
import os

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

# -----------------------
# Define Book schema
# -----------------------
book_class = {
    "class": "Book",
    "description": "A book from Project Gutenberg",
    "vectorizer": "none",
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

# -----------------------
# Check if Book class exists
# -----------------------
try:
    existing_classes = [c["class"] for c in client.schema.get()["classes"]]
except Exception:
    existing_classes = []

if "Book" not in existing_classes:
    client.schema.create_class(book_class)
    print("Book class created")
else:
    print("Book class already exists")

# -----------------------
# Ollama embedding function
# -----------------------
def embed_text(text):
    payload = {
        "model": "nomic-embed-text",
        "prompt": text
    }
    response = requests.post("http://localhost:11434/api/embeddings", json=payload)
    response.raise_for_status()
    return response.json()["embedding"]

# -----------------------
# Fetch books from Gutendex
# -----------------------
API_URL = "https://gutendex.com/books"

def fetch_books(max_pages=5):
    next_url = API_URL
    page_count = 0

    with client.batch as batch:
        batch.batch_size = 20

        while next_url:
            if max_pages and page_count >= max_pages:
                print(f"Reached page limit of {max_pages}. Stopping fetch.")
                break

            page_count += 1
            print(f"Fetching page {page_count}...")

            try:
                response = requests.get(next_url)
                response.raise_for_status()
                data = response.json()

                for book in data.get('results', []):
                    properties = {
                        "title": str(book.get('title', "")),
                        "authors": "; ".join([str(a.get('name', '')) for a in book.get('authors', [])]),
                        "translators": "; ".join([str(t.get('name', '')) for t in book.get('translators', [])]),
                        "subjects": "; ".join([str(s) for s in book.get('subjects', [])]),
                        "bookshelves": "; ".join([str(b) for b in book.get('bookshelves', [])]),
                        "languages": "; ".join([str(l) for l in book.get('languages', [])]),
                        "copyright": str(book.get('copyright')) if book.get('copyright') is not None else "",
                        "media_type": str(book.get('media_type', "")),
                        "download_count": int(book.get('download_count', 0)),
                        "summaries": "; ".join([str(s) for s in book.get('summaries', [])])
                    }

                    # Create text to embed
                    text_for_embedding = (
                        "Title: "+ properties["title"] + "\n" +
                        "Author: " + properties["authors"] + "\n" +
                        "Subjects: "+ properties["subjects"] + "\n" +
                        "Summary: " + properties["summaries"]
                    )

                    try:

                        embedding = embed_text(text_for_embedding)

                        batch.add_data_object(
                            data_object=properties,
                            class_name="Book",
                            vector=embedding  # REQUIRED for WCS
                        )

                        #client.data_object.create(
                        #    data_object=properties,
                        #    class_name="Book",
                        #)
                    except Exception as e:
                        print(f"Failed to insert book '{book.get('title')}': {e}")

                next_url = data.get('next')

            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page_count}: {e}")
                break

    print(f"Finished fetching {page_count} pages and pushing to Weaviate!")

# -----------------------
# Main script
# -----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch books from Gutendex and push to Weaviate.")
    parser.add_argument("--pages", type=int, help="Number of pages to fetch (default: 5)")
    args = parser.parse_args()

    max_pages_to_fetch = args.pages if args.pages else 5
    fetch_books(max_pages=max_pages_to_fetch)
    print("Done!")
