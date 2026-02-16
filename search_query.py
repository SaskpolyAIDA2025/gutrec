import weaviate
from weaviate.auth import AuthApiKey

import requests
import json

# -----------------------
# Weaviate Cloud credentials
# -----------------------
WEAVIATE_URL = "https://cywukygmt0k0kyk3dzng.c0.asia-southeast1.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "cXBHd2Z2Zm56NlE3S2xkUF90Y2xIRWF0aXNWdk9Wa29DLzQ1UjRnOGt1Q29ZWnlNY1RhRldpOFNWQXFRPV92MjAw"

# -----------------------
# Connect to Weaviate
# -----------------------
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(api_key=WEAVIATE_API_KEY),
    )

if not client.is_ready():
    raise Exception("Could not connect to Weaviate Cloud")

print("Connected to Weaviate Cloud")

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
    print(f"\nSearching for:\n {query_text}")

    # 1. Embed the query using Ollama
    embedding = embed_query(query_text)

    # 2. Query Weaviate using nearVector
    result = (
        client.query
        .get(
            "Book",
            ["title", "authors", "subjects", "summaries"]
        )
        .with_near_vector({"vector": embedding})
        .with_limit(k)
        .with_additional(["certainty"])
        .do()
    )

    print("\nResults:")
    print(json.dumps(result, indent=2))

# -----------------------
# Run a test query
# -----------------------
if __name__ == "__main__":
    #book_query = "Title: Una breve historia de casi todo\nAuthor: Bill Bryson\nSubjects: Science\nSummary: Bill Bryson se describe como un viajero renuente, pero ni siquiera cuando está en su casa, en la seguridad de su estudio, puede contener esa curiosidad que siente por el mundo que le rodea. En Una breve historia de casi todo intenta entender qué ocurrió entre la Gran Explosión y el surgimiento de la civilización, cómo pasamos de la nada a lo que ahora somos. El autor aborda materias tan terriblemente aburridas como geología, química y física, pero lo hace de forma tal que resultan comprensibles y amenas. La cuestión es cómo sabemos lo que sabemos. En sus viajes a través del tiempo y del espacio Bryson se topa con una espléndida colección de científicos asombradamente excéntricos, competitivos, obsesivos e insensatos."

    #book_query = "Title: Momo\nAuthor: Michael Ende\nSubjects: Juvenile Fiction\nSummary: The Neverending Story is Michael Ende's best-known book, but Momo—published six years earlier—is the all-ages fantasy novel that first won him wide acclaim. After the sweet-talking gray men come to town, life becomes terminally efficient. Can Momo, a young orphan girl blessed with the gift of listening, vanquish the ashen-faced time thieves before joy vanishes forever? With gorgeous new drawings by Marcel Dzama and a new translation from the German by Lucas Zwirner, this all-new 40th anniversary edition celebrates the book's first U.S. publication in over 25 years."

    #semantic_search(book_query)
    #semantic_search("a story about adventure in the sea", k=5)
    semantic_search("a book of algebra and mathematics", k=5)

