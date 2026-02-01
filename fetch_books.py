import requests
import csv
import sys
import time
import argparse

API_URL = "https://gutendex.com/books"
OUTPUT_FILE = "books_metadata.csv"

def fetch_books(max_pages=None):
    """
    Fetches books from Gutendex API and writes metadata to a CSV file.
    Args:
        max_pages (int): Maximum number of pages to fetch. If None, fetch all.
    """
    fieldnames = [
        "id", "title", "authors", "translators", "subjects", 
        "bookshelves", "languages", "copyright", "media_type", "download_count",
        "summaries"
    ]
    
    try:
        with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            next_url = API_URL
            page_count = 0
            
            print(f"Starting fetch from {API_URL}...")
            if max_pages:
                print(f"Limit set to {max_pages} pages.")
            
            while next_url:
                if max_pages and page_count >= max_pages:
                    print(f"Reached limit of {max_pages} pages.")
                    break

                page_count += 1
                if page_count % 1 == 0: # Print every page for better feedback
                    print(f"Fetching page {page_count}...")
                
                try:
                    response = requests.get(next_url)
                    response.raise_for_status()
                    data = response.json()
                    
                    for book in data.get('results', []):
                        # Extract and format fields
                        authors = "; ".join([a.get('name', '') for a in book.get('authors', [])])
                        translators = "; ".join([t.get('name', '') for t in book.get('translators', [])])
                        subjects = "; ".join(book.get('subjects', []))
                        bookshelves = "; ".join(book.get('bookshelves', []))
                        languages = "; ".join(book.get('languages', []))
                        summaries = "; ".join(book.get('summaries', []))
                        
                        writer.writerow({
                            "id": book.get('id'),
                            "title": book.get('title'),
                            "authors": authors,
                            "translators": translators,
                            "subjects": subjects,
                            "bookshelves": bookshelves,
                            "languages": languages,
                            "copyright": book.get('copyright'),
                            "media_type": book.get('media_type'),
                            "download_count": book.get('download_count'),
                            "summaries": summaries
                        })
                        
                    next_url = data.get('next')
                    
                    # Be nice to the API
                    # time.sleep(0.5) 
                    
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching page {page_count}: {e}")
                    break
                    
            print(f"Finished fetching books. Data saved to {OUTPUT_FILE}")
            
    except IOError as e:
        print(f"Error opening file {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch books from Gutendex API.")
    parser.add_argument("--pages", type=int, help="Number of pages to fetch (default: all)")
    args = parser.parse_args()
    
    fetch_books(max_pages=args.pages)
