from dotenv import load_dotenv
import os
import requests

load_dotenv()
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

def get_book_metadata(title: str, author: str | None = None) -> dict | None:
    title = title.strip()
    author = author.strip() if author else None

    # Build query
    query = f"intitle:'{title}'"
    if author:
        query += f"+inauthor:'{author}'"

    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "printType": "books",
        "key": API_KEY
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if "items" not in data or not data["items"]:
        return None

    volume_info = data["items"][0]["volumeInfo"]
    access_info = data["items"][0]["accessInfo"]

    # Safely extract fields
    authors = volume_info.get("authors", [])
    prettify_author = authors if len(authors) > 1 else (authors[0] if authors else "Unknown")

    metadata = {
        "title": volume_info.get("title"),
        "authors": prettify_author,
        "publishedDate": volume_info.get("publishedDate"),
        "categories": volume_info.get("categories", []),
        "language": volume_info.get("language"),
        #"publicDomain": access_info.get("publicDomain"),
        "printType": volume_info.get("printType"),
        "pageCount": volume_info.get("pageCount"),
        "description": volume_info.get("description"),
    }
    return metadata