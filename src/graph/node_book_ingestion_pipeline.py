from typing import Dict, Any
from src.utils.book_cache import get_book_chapters
from src.graph.node_chapter_summarizer import load_summaries_from_json, save_summaries_to_json
from src.utils.summarizer import summarize_long
from src.utils.parallel_embedder import embed_batch
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter


client = weaviate.connect_to_local()
CLASS_NAME = "BookChunk"


# ---------------------------------------------------------
# Ensure collection exists (v4)
# ---------------------------------------------------------
def ensure_collection():
    existing = client.collections.list_all()

    if CLASS_NAME in existing:
        return

    client.collections.create(
        name=CLASS_NAME,
        properties=[
            Property(name="book_id", data_type=DataType.INT),
            Property(name="chapter", data_type=DataType.INT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="chunk_id", data_type=DataType.INT),
            Property(name="text", data_type=DataType.TEXT),
        ],
        vector_config=[
            {
                "name": "default",
                "vectorizer": Configure.Vectorizer.none(),   # we provide embeddings (nomic-embed-text)
                "dimensions": 768       # nomic-embed-text dimension
            }
        ]
    )


# ---------------------------------------------------------
# Check if book already ingested (v4)
# ---------------------------------------------------------
def book_already_ingested(book_id: int) -> bool:
    collection = client.collections.get(CLASS_NAME)

    result = collection.query.fetch_objects(
        filters=Filter.by_property("book_id").equal(book_id),
        limit=1
    )

    return len(result.objects) > 0


# ---------------------------------------------------------
# Chunk helper
# ---------------------------------------------------------
def chunk_tokens(tokens, chunk_size=180, overlap=40):
    i = 0
    while i < len(tokens):
        yield tokens[i:i + chunk_size]
        i += chunk_size - overlap


# ---------------------------------------------------------
# Full ingestion pipeline (v4)
# ---------------------------------------------------------
def book_ingestion_pipeline_node(state: Dict[str, Any]) -> Dict[str, Any]:
    book_id = state.get("book_id")
    if not book_id:
        return {"error": "Missing book_id in state."}

    ensure_collection()

    if book_already_ingested(book_id):
        return {
            "status": "already_ingested",
            "book_id": book_id
        }

    chapters = get_book_chapters(book_id)
    if not chapters:
        return {"error": "Could not load chapters."}

    summaries = load_summaries_from_json(book_id)
    if not summaries:
        summaries = []
        for idx, ch in enumerate(chapters, start=1):
            try:
                summary = summarize_long(ch["content"])
            except Exception as e:
                summary = f"Error summarizing chapter {idx}: {str(e)}"
            summaries.append({
                "chapter": idx,
                "title": ch["title"],
                "summary": summary
            })
        save_summaries_to_json(book_id, summaries)

    rag_chunks = []
    chunk_id = 0

    for idx, ch in enumerate(chapters, start=1):
        tokens = ch["content"].split()
        for chunk in chunk_tokens(tokens):
            rag_chunks.append({
                "book_id": book_id,
                "chapter": idx,
                "title": ch["title"],
                "chunk_id": chunk_id,
                "text": " ".join(chunk)
            })
            chunk_id += 1

    texts = [c["text"] for c in rag_chunks]
    embeddings = embed_batch(texts)

    collection = client.collections.get(CLASS_NAME)

    for chunk, emb in zip(rag_chunks, embeddings):
        collection.data.insert(
            properties={
                "book_id": chunk["book_id"],
                "chapter": chunk["chapter"],
                "title": chunk["title"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"]
            },
            vector=emb
        )

    return {
        "status": "success",
        "book_id": book_id,
        "chapters": len(chapters),
        "chunks_ingested": len(rag_chunks),
        "summaries_cached": True
    }