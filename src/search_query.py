import weaviate

import requests
import json

# -----------------------
# Connect to Weaviate
# -----------------------
client = weaviate.connect_to_local(
    port=8080,
    grpc_port=50051,
)

if not client.is_ready():
    raise Exception("Could not connect to Weaviate Cloud")

print("Connected to Weaviate Cloud")

# -----------------------
# Close Weaviate function
# -----------------------
def close_weaviate():
    client.close()

# -----------------------
# Ollama embedding function
# -----------------------
def embed_query(text: str):
    """
    Create and return an embedding of the given text.
    """
    payload = {
        "model": "mxbai-embed-large", # "all-minilm", # "nomic-embed-text",
        "prompt": text
    }
    response = requests.post("http://localhost:11434/api/embeddings", json=payload)
    response.raise_for_status()
    return response.json()["embedding"]

# -----------------------
# Semantic search function
# -----------------------
def semantic_search(query_text: str, k: int = 5):
    """
    Serch for similar books in Project Gutenberg based in tue query text.
    Returns k books metadata as a list of dict.
    """
    # 1. Embed the query using Ollama
    embedding = embed_query(query_text)

    # 2. Query Weaviate using nearVector
    collection = client.collections.get("Book")

    result = collection.query.near_vector(
        near_vector=embedding,
        limit=k,
        return_metadata=["distance", "certainty"]
    )

    hits = []
    for obj in result.objects:
        hits.append({
            "id_pg": obj.properties.get("id_pg"),
            "title": obj.properties.get("title"),
            "authors": obj.properties.get("authors"),
            "bookshelves": obj.properties.get("bookshelves"),
            "subjects": obj.properties.get("subjects"),
            "download_count": obj.properties.get("download_count"),
            "summaries": obj.properties.get("summaries"),
            "certainty": obj.metadata.certainty,
        })

    # Return the data
    return hits


# -----------------------
# Run a test query
# -----------------------
if __name__ == "__main__":

    semantic_search("books about existential dread in industrial cities", k=5)

    close_weaviate()