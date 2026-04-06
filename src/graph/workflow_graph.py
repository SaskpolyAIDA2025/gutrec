<<<<<<< HEAD
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
=======
from typing import TypedDict, Optional, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
>>>>>>> ui_update

# Import your nodes
from src.graph.node_book_ingestion_pipeline import book_ingestion_pipeline_node
from src.graph.node_rag_qa import rag_qa_node


# ---------------------------------------------------------
# 1. Define the State Schema
# ---------------------------------------------------------
class BookState(TypedDict, total=False):
<<<<<<< HEAD
=======
    rag_messages: Annotated[list, add_messages]
>>>>>>> ui_update
    book_id: Optional[int]
    question: Optional[str]
    answer: Optional[str]
    ingestion_status: Optional[str]
    chunks_ingested: Optional[int]
    chapters: Optional[int]
    summaries_cached: Optional[bool]
    retrieved_chunks: Optional[List[Dict[str, Any]]]


# ---------------------------------------------------------
# 2. Router Node
# ---------------------------------------------------------
<<<<<<< HEAD
def router_node(state: BookState):
    """
    Decide which branch to run based on the input.
    """
    if state.get("book_id") is not None:
        return {"next": "ingest_book"}

    if state.get("question") is not None:
        return {"next": "answer_question"}

    raise ValueError(
        "Router could not determine workflow path. "
        "Provide either 'book_id' for ingestion or 'question' for QA."
    )
=======
# def router_node(state: BookState):
#     """
#     Decide which branch to run based on the input.
#     """
#     if state.get("book_id") is not None:
#         return {"next": "ingest_book"}

#     if state.get("question") is not None:
#         return {"next": "answer_question"}

#     raise ValueError(
#         "Router could not determine workflow path. "
#         "Provide either 'book_id' for ingestion or 'question' for QA."
#     )
>>>>>>> ui_update



# ---------------------------------------------------------
# 2. Build the Graph
# ---------------------------------------------------------
def build_workflow_graph():
    graph = StateGraph(BookState)

    # -----------------------------
    # Router Node
    # -----------------------------
<<<<<<< HEAD
    graph.add_node("router", router_node)
=======
    # graph.add_node("router", router_node)
>>>>>>> ui_update

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

    # Entry point for router
<<<<<<< HEAD
    graph.set_entry_point("router")
=======
    # graph.set_entry_point("router")
    graph.set_entry_point("ingest_book")
>>>>>>> ui_update

    # ---------------------------------------------------------
    # Conditional routing
    # ---------------------------------------------------------
<<<<<<< HEAD
    graph.add_conditional_edges(
        "router",
        lambda state: state["next"],
        {
            "ingest_book": "ingest_book",
            "answer_question": "answer_question",
        }
    )

    # End edges
    graph.add_edge("ingest_book", END)
    graph.add_edge("answer_question", END)


    return graph.compile()
=======
    # graph.add_conditional_edges(
    #     "router",
    #     lambda state: state["next"],
    #     {
    #         "ingest_book": "ingest_book",
    #         "answer_question": "answer_question",
    #     }
    # )

    # End edges
    graph.add_edge("ingest_book", "answer_question")
    graph.add_edge("answer_question", END)


    return graph.compile()

# workflow.graph.py

def get_book_qa_app():
    return build_workflow_graph()
>>>>>>> ui_update
