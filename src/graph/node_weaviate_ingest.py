from typing import Dict, Any
import weaviate

client = weaviate.connect_to_local(
    port=8080,
    grpc_port=50051,
)
CLASS_NAME = "BookChunk"


def ensure_schema():
    """
    Create the class only if it does NOT already exist.
    """

    exists = client.schema.contains({"class": CLASS_NAME})
    if exists:
        return  # nothing to do

    client.schema.create_class({
        "class": CLASS_NAME,
        "vectorizer": "none",   # we provide our own vectors
        "properties": [
            {"name": "book_id", "dataType": ["int"]},
            {"name": "chapter", "dataType": ["int"]},
            {"name": "title", "dataType": ["text"]},
            {"name": "chunk_id", "dataType": ["int"]},
            {"name": "text", "dataType": ["text"]},
        ]
    })


def weaviate_ingest_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ingests RAG chunks into Weaviate.
    """

    rag_chunks = state.get("rag_chunks")
    if not rag_chunks:
        return {"error": "Missing rag_chunks in state."}

    ensure_schema()

    with client.batch as batch:
        batch.batch_size = 50

        for chunk in rag_chunks:
            client.batch.add_data_object(
                data_object={
                    "book_id": chunk["book_id"],
                    "chapter": chunk["chapter"],
                    "title": chunk["title"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"]
                },
                class_name=CLASS_NAME,
                vector=chunk["embedding"]
            )

    return {
        "status": "success",
        "ingested_chunks": len(rag_chunks)
    }