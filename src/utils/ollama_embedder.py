import requests

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text" # "mxbai-embed-large" # or "nomic-embed-text" if you want faster

def embed_text(text: str):
    response = requests.post(
        OLLAMA_URL,
        json={"model": EMBED_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]