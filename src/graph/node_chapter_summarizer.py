
import os
import json
from typing import Dict, Any

from src.utils.book_cache import get_book_chapters
from src.utils.summarizer import summarize_long

SUMMARY_DIR = "summaries"
os.makedirs(SUMMARY_DIR, exist_ok=True)

# ---------------------------------------------------------
# Helper functions to save and reuse summaries
# ---------------------------------------------------------
def summary_json_path(book_id: int) -> str:
    return os.path.join(SUMMARY_DIR, f"{book_id}_summaries.json")


def load_summaries_from_json(book_id: int):
    path = summary_json_path(book_id)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_summaries_to_json(book_id: int, summaries):
    path = summary_json_path(book_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)


def summarize_chapters_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    - Downloads a Gutenberg book
    - Splits into chapters
    - Summarizes one or all chapters
    """

    book_id = state.get("book_id")
    chapter_number = state.get("chapter_number")

    if not book_id:
        return {
            "error": "Missing book_id in state.",
            "summaries": None
        }

    # Try loading cached summaries
    cached = load_summaries_from_json(book_id)

    if cached:
        if chapter_number:
            for item in cached:
                if item["chapter"] == chapter_number:
                    return {
                        "book_id": book_id,
                        "chapter_number": chapter_number,
                        "chapter_title": item["title"],
                        "summary": item["summary"]
                    }
            return {"error": f"Chapter {chapter_number} not found in cached summaries."}

        return {
            "book_id": book_id,
            "total_chapters": len(cached),
            "summaries": cached
        }
    
    # ---------------------------------------------------------
    # No cached summaries, then compute them
    # ---------------------------------------------------------

    # Download full book text
    # Load chapters from cache (fast, no re-download)
    chapters = get_book_chapters(book_id)

    if not chapters:
        return {
            "error": "Could not detect chapters in this book.",
            "summaries": None
        }

    # If a specific chapter is requested
    if chapter_number:
        if chapter_number < 1 or chapter_number > len(chapters):
            return {
                "error": f"Chapter {chapter_number} does not exist. This book has {len(chapters)} chapters.",
                "summaries": None
            }

        chapter_obj = chapters[chapter_number - 1]
        chapter_title = chapter_obj["title"]
        chapter_text = chapter_obj["content"]

        summary = summarize_long(chapter_text)

        return {
            "book_id": book_id,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "summary": summary
        }

    # Otherwise summarize all chapters
    summaries = []

    for i, ch in enumerate(chapters, start=1):
        try:
            summary = summarize_long(ch["content"])
        except Exception as e:
            summary = f"Error summarizing chapter {i}: {str(e)}"

        summaries.append({
            "chapter": i,
            "title": ch["title"],
            "summary": summary
        })

    # Save to JSON for future instant access
    save_summaries_to_json(book_id, summaries)

    # Return results
    return {
        "book_id": book_id,
        "total_chapters": len(chapters),
        "summaries": summaries
    }