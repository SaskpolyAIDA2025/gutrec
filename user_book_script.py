from dotenv import load_dotenv
import os

import requests

load_dotenv()  # loads .env into environment variables
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

# create getting started variables
title = input("Enter book's title: ").strip()
author = input("Enter author name: ").strip()
url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:'{title}'&author='{author}'&printType=books"
params = {
    #"q": "python programming",
    "key": API_KEY
}
#isbn = input("Enter 10 digit ISBN: ").strip()

# send a request and get a JSON response
resp = requests.get(url, params=params)
# parse JSON into Python as a dictionary
book_data = resp.json()
print(book_data)

# create additional variables for easy querying
volume_info = book_data["items"][0]["volumeInfo"]
author = volume_info["authors"]
# practice with conditional expressions!
prettify_author = author if len(author) > 1 else author[0]

# display title, author, page count, publication date
# fstrings require Python 3.6 or higher
# \n adds a new line for easier reading
print(f"\nTitle: {volume_info['title']}")
print(f"Author: {prettify_author}")
print(f"Page Count: {volume_info['pageCount']}")
print(f"Publication Date: {volume_info['publishedDate']}")
print(f"Summary: {volume_info['description']}")
print("\n***\n")