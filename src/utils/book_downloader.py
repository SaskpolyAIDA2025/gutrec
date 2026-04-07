import requests
import re

CHAPTER_HEADING_PATTERN = re.compile(
    r"(?P<title>^(CHAPTER|Chapter|LETTER|SECTION|BOOK|PART|ACT)\s+"
    r"([IVXLC0-9]+|[A-Z]+|\d+)\.?\s*$)",
    re.IGNORECASE | re.MULTILINE
)


def get_gutenberg_id(title):
    """
    Find a Project Gutenberg book ID by its title.
    Returns the ID.
    """
    url = "https://gutendex.com/books"
    response = requests.get(url, params={"search": title})
    data = response.json()
    return data["results"][0]["id"] if data["results"] else None


def download_gutenberg_book(book_id):
    """
    Download a Project Gutenberg book by its numeric ID.
    Returns the raw text.
    """
    url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
    response = requests.get(url)

    # Fallback if "-0" version doesn't exist
    if response.status_code != 200:
        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt" #f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"
        response = requests.get(url)
        response.raise_for_status()

    text = clean_gutenberg_text(response.text)
    return text


def clean_gutenberg_text(text: str):
    """Remove Gutenberg header/footer."""
    start = text.find("*** START")
    end = text.find("*** END")
    if start != -1 and end != -1:
        return text[start:end]
    return text


def extract_toc(text):
    """Extract Gutenberg Content table."""
    toc_start = re.search(r"\n\s*contents\s*\n", text, re.IGNORECASE | re.MULTILINE)
    if not toc_start:
        return None

    start_idx = toc_start.end()

    # Heuristic: TOC usually ends before the first real chapter heading
    next_heading = re.search(
        r"^\s*(chapter|letter|section|book|part)\s+[IVXLC\d]+",
        text[start_idx:], 
        re.IGNORECASE | re.MULTILINE
    )

    end_idx = start_idx + next_heading.start() if next_heading else len(text)

    toc_block = text[start_idx:end_idx]
    entries = toc_start.findall(toc_block)

    return entries if entries else None


def split_into_chapters(text: str):
    """
    Chapter splitter using finditer instead of split().
    Returns a list of dicts: [{title, content}, ...]
    """

    text = clean_gutenberg_text(text)

    matches = list(CHAPTER_HEADING_PATTERN.finditer(text))

    if not matches:
        return []

    chapters = []

    for i, match in enumerate(matches):
        title = match.group("title").strip()
        start = match.end()

        # Determine end of chapter
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        content = text[start:end].strip()

        chapters.append({
            "title": title,
            "content": content
        })

    return chapters


def get_chapter(book_id, chapter_number):
    """
    Download a Gutenberg book and return a specific chapter.
    """
    text = download_gutenberg_book(book_id)
    chapters = split_into_chapters(text)

    if 1 <= chapter_number <= len(chapters):
        return chapters[chapter_number - 1]
    else:
        return f"Chapter {chapter_number} not found. This book has {len(chapters)} chapters."