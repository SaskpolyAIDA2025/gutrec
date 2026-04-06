from src.graph.node_chapter_summarizer import summarize_chapters_node

def get_all_chapter_summaries(book_id: int):
    """
    Convenience wrapper for UI: returns list of chapter summaries.
    Each item: {chapter, title, summary}
    """
    result = summarize_chapters_node({"book_id": book_id})
    if result.get("error"):
        return None, result["error"]
    return result.get("summaries", []), None