from functools import lru_cache
from src.utils.book_downloader import download_gutenberg_book, split_into_chapters

@lru_cache(maxsize=32)
def get_book_text(book_id: int) -> str:
    """Cached download of raw Gutenberg text."""
    return download_gutenberg_book(book_id)


@lru_cache(maxsize=32)
def get_book_chapters(book_id: int):
    """Cached chapter extraction."""
    text = get_book_text(book_id)
    return split_into_chapters(text)