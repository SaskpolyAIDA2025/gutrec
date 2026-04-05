from typing import Dict, Any
from src.utils.book_cache import get_book_chapters
from src.utils.ollama_embedder import embed_text


def chunk_tokens(tokens, chunk_size=180, overlap=40):
    i = 0
    while i < len(tokens):
        yield tokens[i:i + chunk_size]
        i += chunk_size - overlap


def rag_chunker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates RAG-ready chunks with embeddings using Ollama.
    """

    book_id = state.get("book_id")
    if not book_id:
        return {"error": "Missing book_id in state."}

    chapters = get_book_chapters(book_id)
    if not chapters:
        return {"error": "No chapters found for this book."}

    rag_chunks = []
    chunk_id = 0

    for idx, ch in enumerate(chapters, start=1):
        tokens = ch["content"].split()

        for chunk in chunk_tokens(tokens):
            text = " ".join(chunk)
            embedding = embed_text(text)

            rag_chunks.append({
                "book_id": book_id,
                "chapter": idx,
                "title": ch["title"],
                "chunk_id": chunk_id,
                "text": text,
                "embedding": embedding
            })

            chunk_id += 1

    return {
        "book_id": book_id,
        "rag_chunks": rag_chunks
    }