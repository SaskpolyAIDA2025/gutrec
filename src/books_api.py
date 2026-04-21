from dotenv import load_dotenv
import os
import requests
import random, time
from requests.exceptions import RequestException, HTTPError

load_dotenv()
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")


def get_with_retry(url, params=None, max_retries=3, backoff_seconds=1):
    """
    Perform GET with simple retry on transient errors (e.g., 5xx).
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=10)
            # If status is 4xx/5xx, this will raise HTTPError
            resp.raise_for_status()
            return resp  # success

        except HTTPError as e:
            status = e.response.status_code if e.response is not None else None

            # Retry only on 5xx (server-side) errors
            if status is not None and 500 <= status < 600 and attempt < max_retries:
                sleep_time = backoff_seconds * attempt  # simple linear backoff
                print(f"HTTP {status} on attempt {attempt}, retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                continue
            # Non-retriable or last attempt
            raise

        except RequestException as e:
            # Network issues, timeouts, etc. – you can choose to retry these too
            if attempt < max_retries:
                sleep_time = backoff_seconds * attempt
                print(f"Request error on attempt {attempt}: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                continue
            raise


def get_book_metadata(title: str, author: str | None = None) -> dict | None:
    """
        Given a title and (possibly) an author, a request is sent to Google Books Api to get its information.
        Return: Metadata of the book as a dict.
    """
    title = title.strip()
    author = author.strip() if author else None

    # Add a delay to avoid hitting API rate limits
    # time.sleep(3 + random.random())   # Uncomment for evaluation

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

    # resp = requests.get(url, params=params)
    # resp.raise_for_status()
    resp = get_with_retry(url, params=params, max_retries=3, backoff_seconds=1)
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
        "printType": volume_info.get("printType"),
        "pageCount": volume_info.get("pageCount"),
        "description": volume_info.get("description"),
    }
    
    return metadata