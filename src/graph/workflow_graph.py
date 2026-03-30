from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END

# Import your nodes
from src.graph.node_book_ingestion_pipeline import book_ingestion_pipeline_node
from src.graph.node_rag_qa import rag_qa_node


# ---------------------------------------------------------
# 1. Define the State Schema
# ---------------------------------------------------------
class BookState(TypedDict, total=False):
    book_id: Optional[int]
    question: Optional[str]
    answer: Optional[str]
    ingestion_status: Optional[str]
    chunks_ingested: Optional[int]
    chapters: Optional[int]
    summaries_cached: Optional[bool]
    retrieved_chunks: Optional[List[Dict[str, Any]]]


# ---------------------------------------------------------
# 2. Build the Graph
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

    # ---------------------------------------------------------
    # 3. Define Entry Points
    # ---------------------------------------------------------

    # Entry point for ingestion
    graph.set_entry_point("ingest_book")

    # After ingestion → END
    graph.add_edge("ingest_book", END)

    # Entry point for QA
    graph.add_edge("answer_question", END)

    return graph.compile()