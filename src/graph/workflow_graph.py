from typing import TypedDict, Optional, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from src.graph.node_book_ingestion_pipeline import book_ingestion_pipeline_node
from src.graph.node_rag_qa import rag_qa_node


# ---------------------------------------------------------
# Define the State Schema
# ---------------------------------------------------------
class BookState(TypedDict, total=False):
    rag_messages: Annotated[list, add_messages]
    book_id: Optional[int]
    question: Optional[str]
    answer: Optional[str]
    ingestion_status: Optional[str]
    chunks_ingested: Optional[int]
    chapters: Optional[int]
    summaries_cached: Optional[bool]
    retrieved_chunks: Optional[List[Dict[str, Any]]]


# ---------------------------------------------------------
# Build the Graph
# ---------------------------------------------------------
def build_workflow_graph():
    graph = StateGraph(BookState)

    # -----------------------------
    # Ingestion Node
    # -----------------------------
    graph.add_node(
        "ingest_book",
        lambda state: {
            **state,
            **book_ingestion_pipeline_node(state)
        }
    )

    # -----------------------------
    # QA Node
    # -----------------------------
    graph.add_node(
        "answer_question",
        lambda state: {
            **state,
            **rag_qa_node(state)
        }
    )

    # Entry point for ingest_book
    graph.set_entry_point("ingest_book")

    # Addd edges
    graph.add_edge("ingest_book", "answer_question")
    graph.add_edge("answer_question", END)

    return graph.compile()

# Function to be used in ui
def get_book_qa_app():
    return build_workflow_graph()
