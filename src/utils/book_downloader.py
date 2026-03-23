import requests
import re

CHAPTER_HEADING_PATTERN = re.compile(
    r"(?P<title>^(CHAPTER|Chapter|LETTER|SECTION|BOOK|PART)\s+"
    r"([IVXLC0-9]+|[A-Z]+|\d+)\.?\s*$)",
    re.IGNORECASE | re.MULTILINE
)

# CHAPTER_HEADING_PATTERN = re.compile(
#     r"^\s*(?P<title>(chapter|letter|section|book|part)\s+([IVXLC]+|\d+))\b.*$",
#     re.IGNORECASE | re.MULTILINE
# )


def get_gutenberg_id(title):
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
        url = f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"
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
    entries = TOC_ENTRY_PATTERN.findall(toc_block)

    return entries if entries else None


# def split_into_chapters(text):
#     """
#     More robust Gutenberg chapter splitter.
#     Handles multiple chapter heading formats.
#     Returns a list of chapter texts.
#     """

#     # A more comprehensive set of chapter heading patterns
#     chapter_patterns = [
#         r"(?:^|\n)(CHAPTER\s+[IVXLC0-9]+\.?\s*\n)",          # CHAPTER I
#         r"(?:^|\n)(CHAPTER\s+[A-Z]+\.?\s*\n)",               # CHAPTER ONE
#         r"(?:^|\n)(Chapter\s+\d+\.?\s*\n)",                  # Chapter 1
#         r"(?:^|\n)(LETTER\s+[IVXLC0-9]+\.?\s*\n)",           # LETTER I
#         r"(?:^|\n)(SECTION\s+[IVXLC0-9]+\.?\s*\n)",          # SECTION I
#         r"(?:^|\n)(BOOK\s+[IVXLC0-9]+\.?\s*\n)",             # BOOK I
#         r"(?:^|\n)(PART\s+[IVXLC0-9]+\.?\s*\n)",             # PART I
#     ]

#     # Combine all patterns into one big OR-pattern
#     combined_pattern = "|".join(chapter_patterns)

#     # Split while keeping the chapter titles
#     parts = re.split(combined_pattern, text, flags=re.IGNORECASE)

#     chapters = []
#     i = 1
#     while i < len(parts):
#         # Find the first non-None match among the OR groups
#         title = next((p for p in parts[i:i+len(chapter_patterns)] if p), None)
#         content_index = i + len(chapter_patterns)
#         content = parts[content_index] if content_index < len(parts) else ""

#         if title:
#             chapters.append(f"{title.strip()}\n{content.strip()}")

#         i += len(chapter_patterns) + 1

#     return chapters

def split_into_chapters(text: str):
    """
    Robust chapter splitter using finditer instead of split().
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