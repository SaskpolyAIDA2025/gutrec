from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import extraction_node, enrichment_node, search_node, clarification_node, responder_node, broad_idea_node, confirmation_node
from .node_chapter_summarizer import summarize_chapters_node

# Define routing logic
def should_continue(state: AgentState):
    title = state["extraction"].get("title", "")
    loops = state.get("loop_count", 0)

    if title:  
        return "enrich"

    if loops < 2:
        return "clarify"
    
    return "broad"

def should_summarize(state: AgentState):
    if state.get("book_id"):
        return "summarize"
    else:
        return END

workflow = StateGraph(AgentState)

# Add our Nodes
workflow.add_node("extract", extraction_node)
workflow.add_node("clarify", clarification_node)
workflow.add_node("broad", broad_idea_node)
workflow.add_node("enrich", enrichment_node)
workflow.add_node("search", search_node)
workflow.add_node("respond", responder_node)
workflow.add_node("confirm", confirmation_node)
workflow.add_node("summarize", summarize_chapters_node)

# Connect them
workflow.add_edge(START, "extract")
workflow.add_conditional_edges("extract", should_continue, {
    "clarify": "clarify",
    "enrich": "enrich",
    "broad": "broad"
})
workflow.add_edge("clarify", END)
workflow.add_edge("broad", "search")
workflow.add_edge("enrich", "search")
workflow.add_edge("search", "respond")
# workflow.add_edge("respond", END)
# workflow.add_edge("respond", "summarize")
workflow.add_edge("respond", "confirm")
workflow.add_conditional_edges(
    "confirm",
    should_summarize,
    {
        "summarize": "summarize",
        END: END
    }
)

workflow.add_edge("summarize", END)

app = workflow.compile()