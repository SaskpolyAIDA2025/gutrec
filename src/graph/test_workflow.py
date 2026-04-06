from src.graph.workflow_graph import build_workflow_graph
import weaviate

def test_ingestion(graph, book_id):
    print("\n=== Running Book Ingestion ===")
    result = graph.invoke({"book_id": book_id})
    print("Ingestion Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")


def test_question_answering(graph, question):
    print("\n=== Running Question Answering ===")
    result = graph.invoke({"question": question})
    print("Answer:")
    print(result.get("answer", "No answer returned"))
    print("\nRetrieved Chunks:")
    for chunk in result.get("retrieved_chunks", []):
        print(f"- Chapter {chunk['chapter']}: {chunk['text'][:120]}...")


if __name__ == "__main__":
    graph = build_workflow_graph()
    
    # client = weaviate.connect_to_local(
    # port=8080,
    # grpc_port=50051,
    # )
    
    # try:
    #     client.collections.delete("BookChunk")
    # finally:
    #     client.close()

    # -------------------------------
    # 1. Test ingestion
    # -------------------------------
    test_ingestion(graph, book_id=84)   # Pride and Prejudice

    # -------------------------------
    # 2. Test QA
    # -------------------------------
    test_question_answering(
        graph,
        question="How was created the monster?"
    )
    