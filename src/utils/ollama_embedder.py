import requests

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text" # "mxbai-embed-large". Must be the same that in parallel_embedder

def embed_text(text: str):
    """"Create an embedding for the given text."""
    response = requests.post(
        OLLAMA_URL,
        json={"model": EMBED_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]