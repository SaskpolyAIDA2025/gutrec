import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text" #"mxbai-embed-large". Must be the same used in ollama_embedder.
MAX_WORKERS = 6   # safe default for Ollama


def embed_single(text: str):
    """Embed a single chunk using Ollama."""
    response = requests.post(
        OLLAMA_URL,
        json={"model": EMBED_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]


def embed_batch(texts):
    """
    Embed a list of texts in parallel.
    Returns a list of embeddings in the same order.
    """

    embeddings = [None] * len(texts)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(embed_single, text): idx
            for idx, text in enumerate(texts)
        }

        for future in as_completed(futures):
            idx = futures[future]
            embeddings[idx] = future.result()

    return embeddings