from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import extraction_node, enrichment_node, search_node, clarification_node, responder_node

# Define routing logic
def should_continue(state: AgentState):
    if not state["extraction"]["title"]:
        return "clarify"
    return "enrich"

workflow = StateGraph(AgentState)

# Add our Nodes
workflow.add_node("extract", extraction_node)
workflow.add_node("clarify", clarification_node)
workflow.add_node("enrich", enrichment_node)
workflow.add_node("search", search_node)
workflow.add_node("respond", responder_node)

# Connect them
workflow.add_edge(START, "extract")
workflow.add_conditional_edges("extract", should_continue, {
    "clarify": "clarify",
    "enrich": "enrich"
})
workflow.add_edge("clarify", END) # Wait for user to answer
workflow.add_edge("enrich", "search")
workflow.add_edge("search", "respond")
workflow.add_edge("respond", END)

app = workflow.compile()