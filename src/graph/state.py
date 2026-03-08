from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages
from src.schemas import BookQuery

# 1. Define the State
class AgentState(TypedDict):
    # 'add_messages' allows us to append new messages to history automatically
    messages: Annotated[list, add_messages]
    extraction: dict         # Stores our BookQuery result
    book_metadata: dict      # Stores Google Books data
    results: list            # Final Weaviate results
    loop_count: int          # Counter to close the loop after a number of attempts
    broad_query: str         # Description of user search when no book mentioned