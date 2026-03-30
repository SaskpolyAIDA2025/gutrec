from typing import Dict, Any
import requests
import weaviate
from src.utils.ollama_embedder import embed_text

client = weaviate.connect_to_local(
    port=8080,
    grpc_port=50051,
)
CLASS_NAME = "BookChunk"

OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "gemma3:4b"   # or "mistral", "qwen", etc.


def ollama_generate(prompt: str):
    response = requests.post(
        OLLAMA_URL,
        json={"model": LLM_MODEL, "prompt": prompt, "stream": False}
    )
    response.raise_for_status()
    data = response.json()

    return data.get("response", "")


def rag_qa_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves relevant chunks and answers the user's question using Ollama.
    """

    question = state.get("question")
    if not question:
        return {"error": "Missing question in state."}

    # Embed question using Ollama
    q_embedding = embed_text(question)

    # Retrieve top chunks
    response = client.query.get(
        CLASS_NAME,
        ["text", "chapter", "title", "book_id"]
    ).with_near_vector({
        "vector": q_embedding
    }).with_limit(5).do()

    hits = response["data"]["Get"][CLASS_NAME]

    context = "\n\n".join([h["text"] for h in hits])

    prompt = f"""
You are a helpful assistant answering questions about a book.

Question:
{question}

Relevant context from the book:
{context}

Answer the question using ONLY the context above.
"""

    answer = ollama_generate(prompt)

    client.close()

    return {
        "question": question,
        "answer": answer,
        "retrieved_chunks": hits
    }