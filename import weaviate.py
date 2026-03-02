import requests
import argparse
import weaviate
from weaviate.auth import AuthApiKey

# -----------------------
# Weaviate Cloud credentials
# -----------------------
WEAVIATE_URL = "https://cywukygmt0k0kyk3dzng.c0.asia-southeast1.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "cXBHd2Z2Zm56NlE3S2xkUF90Y2xIRWF0aXNWdk9Wa29DLzQ1UjRnOGt1Q29ZWnlNY1RhRldpOFNWQXFRPV92MjAw"

# -----------------------
# Define Book schema
# -----------------------
book_class = {
    "class": "Book",
    "description": "A book from Project Gutenberg",
    "vectorizer": "text2vec-openai",
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
# Fetch books from Gutendex
# -----------------------
API_URL = "https://gutendex.com/books"

def fetch_books(client, max_pages=None):
    next_url = API_URL
    page_count = 0

    while next_url:
        if max_pages and page_count >= max_pages:
            print(f"Reached page limit of {max_pages}.")
            break

        page_count += 1
        print(f"Fetching page {page_count}...")

        try:
            response = requests.get(next_url)
            response.raise_for_status()
            data = response.json()

            for book in data.get('results', []):
                properties = {
                    "title": book.get('title'),
                    "authors": "; ".join([a.get('name', '') for a in book.get('authors', [])]),
                    "translators": "; ".join([t.get('name', '') for t in book.get('translators', [])]),
                    "subjects": "; ".join(book.get('subjects', [])),
                    "bookshelves": "; ".join(book.get('bookshelves', [])),
                    "languages": "; ".join(book.get('languages', [])),
                    "copyright": book.get('copyright'),
                    "media_type": book.get('media_type'),
                    "download_count": book.get('download_count'),
                    "summaries": "; ".join(book.get('summaries', []))
                }

                # Push to Weaviate using Gutenberg ID as UUID
                client.data_object.create(
                    data_object=properties,
                    class_name="Book",
                    uuid=str(book.get("id"))
                )

            next_url = data.get('next')

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page_count}: {e}")
            break

    print(f"✅ Finished fetching {page_count} pages and pushing to Weaviate!")

# -----------------------
# Main script
# -----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch books from Gutendex and push to Weaviate.")
    parser.add_argument("--pages", type=int, help="Number of pages to fetch (default: all)")
    args = parser.parse_args()

    # -----------------------
    # Connect to Weaviate with auto-close
    # -----------------------
    with weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=AuthApiKey(api_key=WEAVIATE_API_KEY)
    ) as client:

        # Test connection
        if client.is_ready():
            print("✅ Weaviate is ready")
        else:
            raise Exception("❌ Could not connect to Weaviate")

        # Create Book schema if it doesn't exist
        existing_classes = [c["class"] for c in client.schema.get_all()]
        if "Book" not in existing_classes:
            client.schema.create_class(book_class)
            print("✅ Book class created in Weaviate")
        else:
            print("ℹ️ Book class already exists")

        # Fetch and push books
        fetch_books(client, max_pages=args.pages)

    print("✅ Weaviate connection closed")