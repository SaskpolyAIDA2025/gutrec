from typing import Dict, Any
import weaviate

from src.utils.ollama_embedder import embed_text
from src.llm_chain import llm, rag_prompt

# Connect to weaviate
client = weaviate.connect_to_local(
    port=8080,
    grpc_port=50051,
)
CLASS_NAME = "BookChunk"


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
    collection = client.collections.get(CLASS_NAME)

    response = collection.query.near_vector(
        near_vector=q_embedding,
        limit=5,
        return_properties=["text", "chapter", "title", "book_id"]
    )

    results = []
    for obj in response.objects:
        results.append({
            "text": obj.properties.get("text"),
            "chapter": obj.properties.get("chapter"),
            "title": obj.properties.get("title"),
            "book_id": obj.properties.get("book_id"),
        })

    context = "\n\n".join([h["text"] for h in results])

    # Close connection to weaviate
    client.close()

    # Generate answer using the llm.
    answer = llm.invoke(
        rag_prompt.format(question=question, context=context)
    )

    return {
        "question": question,
        "answer": answer,
        "retrieved_chunks": results
    }