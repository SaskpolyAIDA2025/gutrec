from langchain_core.messages import AIMessage, HumanMessage
from src.graph.state import AgentState
from src.llm_chain import structured_chain, chat_chain
from src.books_api import get_book_metadata
from src.search_query import semantic_search
from src.llm_chain import llm

# 2. Define the Nodes
def extraction_node(state: AgentState):
    user_input = state["messages"][-1].content
    
    res = structured_chain.invoke({"user_input": user_input})
    return {"extraction": res.dict()}

def clarification_node(state: AgentState):
    user_input = state["messages"][-1].content
    response = chat_chain.invoke({"user_input": user_input})
    return {"messages": [response]}

def enrichment_node(state: AgentState):
    ext = state["extraction"]
    meta = get_book_metadata(ext["title"], ext.get("author"))
    return {"book_metadata": meta or {}}

def search_node(state: AgentState):
    # We use the description from Google Books as the query for Weaviate
    query_text = state["book_metadata"].get("description") or state["extraction"]["title"]
    hits = semantic_search(query_text)
    
    return {"results": hits}

def responder_node(state: AgentState):
    results = state.get("results", [])
    
    if not results:
        return {"messages": [AIMessage(content="I couldn't find any matches in the Gutenberg library.")]}

    # Format the results into a string for the LLM to see
    # context = "\n".join([f"- {b['title']} by {b['authors']}: {b['summaries'][:200]}..." for b in results])
    
    # response = llm.invoke(f"The user is looking for a book. Based on these search results, recommend the best matches:\n{context}")

    print("\n=== Semantic Search Results ===")
    for i, book in enumerate(results, start=1):
        print(f"\n--- Result {i} ---")
        print(f"Title: {book.get('title', 'N/A')}")
        print(f"Authors: {book.get('authors', 'N/A')}")
        print(f"Bookshelves: {book.get('bookshelves', 'N/A')}")
        print(f"Subjects: {book.get('subjects', 'N/A')}")
        print(f"Download Count: {book.get('download_count', 'N/A')}")
        print(f"Summary: {book.get('summaries', 'N/A')}")
        print(f"Certainty: {book.get('certainty', 'N/A')}")

    print("\n===============================\n")
    
    return {"messages": [AIMessage(content="I could find some matches in the Gutenberg library.")]}
