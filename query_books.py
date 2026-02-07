import weaviate
from weaviate.auth import AuthApiKey

# -----------------------
# Weaviate credentials
# -----------------------
WEAVIATE_URL = "https://cywukygmt0k0kyk3dzng.c0.asia-southeast1.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "cXBHd2Z2Zm56NlE3S2xkUF90Y2xIRWF0aXNWdk9Wa29DLzQ1UjRnOGt1Q29ZWnlNY1RhRldpOFNWQXFRPV92MjAw"

# -----------------------
# Connect to Weaviate
# -----------------------
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(api_key=WEAVIATE_API_KEY)
)

# -----------------------
# Query: get first 20 books
# -----------------------
query_limit = 100

result = client.query.get(
    "Book",
    ["title", "authors", "download_count"]
).with_limit(query_limit).do()

books = result.get("data", {}).get("Get", {}).get("Book", [])

if books:
    for i, book in enumerate(books, start=1):
        title = book.get("title", "Unknown Title")
        authors = book.get("authors", "Unknown Author")
        downloads = book.get("download_count", 0)
        print(f"{i}. {title} by {authors} (downloads: {downloads})")
else:
    print("No books found in Weaviate.")