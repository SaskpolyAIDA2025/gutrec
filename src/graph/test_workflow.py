from src.graph.workflow_graph import build_workflow_graph

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

    # -------------------------------
    # 1. Test ingestion
    # -------------------------------
    test_ingestion(graph, book_id=1342)   # Pride and Prejudice

    # -------------------------------
    # 2. Test QA
    # -------------------------------
    test_question_answering(
        graph,
        question="What is the main conflict in the early chapters?"
    )
    