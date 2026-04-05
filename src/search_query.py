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
    #book_query = "Title: A Short History of Nearly Everything\nAuthor: Bill Bryson\nSubjects: Science\nSummary: This brand-new edition of the colossal bestseller is lavishly illustrated to convey, in pictures as in words, Bill Bryson's exciting, informative journey into the world of science. In this acclaimed bestseller, beloved author Bill Bryson confronts his greatest challenge yet: to understand — and, if possible, answer — the oldest, biggest questions we have posed about the universe and ourselves. Taking as territory everything from the Big Bang to the rise of civilization, Bryson seeks to understand how we got from there being nothing at all to there being us. The result is a sometimes profound, sometimes funny, and always supremely clear and entertaining adventure in the realms of human knowledge, as only Bill Bryson can render it. Now, in this handsome new edition, Bill Bryson's words are supplemented by full-colour artwork that explains in visual terms the concepts and wonder of science, at the same time giving face to the major players in the world of scientific study. Eloquently and entertainingly described, as well as lavishly illustrated, science has never been more involving or entertaining."

    #book_query = "Title: Momo\nAuthor: Michael Ende\nSubjects: Juvenile Fiction\nSummary: The Neverending Story is Michael Ende's best-known book, but Momo—published six years earlier—is the all-ages fantasy novel that first won him wide acclaim. After the sweet-talking gray men come to town, life becomes terminally efficient. Can Momo, a young orphan girl blessed with the gift of listening, vanquish the ashen-faced time thieves before joy vanishes forever? With gorgeous new drawings by Marcel Dzama and a new translation from the German by Lucas Zwirner, this all-new 40th anniversary edition celebrates the book's first U.S. publication in over 25 years."

    #semantic_search(book_query)
    #semantic_search("a story about adventure in the sea", k=10)
    #semantic_search("a book of algebra and mathematics", k=10)
    semantic_search("books about existential dread in industrial cities", k=5)

    close_weaviate()