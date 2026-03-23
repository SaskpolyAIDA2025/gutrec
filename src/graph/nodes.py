from langchain_core.messages import AIMessage, HumanMessage
from src.graph.state import AgentState
from src.llm_chain import structured_chain, chat_chain, broad_idea_prompt
from src.books_api import get_book_metadata
from src.search_query import semantic_search
from src.utils.book_downloader import get_gutenberg_id
from src.llm_chain import llm

# 2. Define the Nodes
def extraction_node(state: AgentState):
    user_input = state["messages"][-1].content
    
    res = structured_chain.invoke({"user_input": user_input})
    data = res.model_dump()
    
    if data.get("title"):
        return {
            "extraction": data,
            "messages": [
                AIMessage(content=f"Great, I found the title: **{data['title']}**.")
            ]
        }

    return {"extraction": data}

def clarification_node(state: AgentState):
    user_input = state["messages"][-1].content
    response = chat_chain.invoke({"user_input": user_input})
    return {
        "messages": [AIMessage(content=response.content)],
        "loop_count": state["loop_count"] + 1
    }

def broad_idea_node(state: AgentState):
    # Combine all user messages into one text block
    user_messages = [
        m.content for m in state["messages"] if isinstance(m, HumanMessage)
    ]
    conversation_text = "\n".join(user_messages)

    summary = llm.invoke(
        broad_idea_prompt.format(conversation=conversation_text)
    )

    return {
        "broad_query": summary.content,
        "messages": [
            AIMessage(
                content=(
                    "I couldn't identify a specific title, but based on what you described, "
                    "here's the type of book you're looking for:\n\n"
                    f"**{summary.content}**\n\n"
                    "I'll search for books that match this description."
                )
            )
        ]
    }

def enrichment_node(state: AgentState):
    ext = state["extraction"]
    meta = get_book_metadata(ext["title"], ext.get("author"))

    if not meta:
        return {
            "book_metadata": {},
            "messages": [
                AIMessage(content="I couldn't find metadata for that book, but I'll still try searching.")
            ]
        }

    return {
        "book_metadata": meta,
        "messages": [AIMessage(content=f"Found metadata for **{ext['title']}**. Searching for similar books...")
        ]
    }

def search_node(state: AgentState):
    if "broad_query" in state and state["broad_query"]:
        # We use the summary of  what user has mentioned
        query_text = state["broad_query"]
    else:
        # We use the description from Google Books as the query for Weaviate
        query_text = state["book_metadata"].get("description") or state["extraction"]["title"]

    hits = semantic_search(query_text)
    return {
        "results": hits,
    }


def responder_node(state: AgentState):
    results = state.get("results", [])
    
    if not results:
        return {"messages": [AIMessage(content="I couldn't find any matches in the Gutenberg library.")]}
    
    # Build a readable summary
    summary = "\n".join(
        f"{i}.- **{b.get('title', 'N/A')}** by {b.get('authors', 'N/A')} (certainty {b.get('certainty', 'N/A')})"
        for i, b in enumerate(results, start=1)
    )

    return {
        "messages": [
            AIMessage(
                content=(
                    "Here are some books I found that might interest you:\n\n"
                    f"{summary}\n\n"
                    f"If you want to see a summary by chapter of one of those books write its number (1-{len(results)}), or write X to continue with a different book reference."
                )
            )
        ],
        "reset_messages": True,
    }


def confirmation_node(state: AgentState):
    results = state.get("results", [])

    user_text = input("\nYou: ")
    i = int(user_text)
    
    if i > 0 and i < len(results) + 1:
        book_id = get_gutenberg_id(results[i - 1].get('title', 'N/A'))
        
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Preparing chapter-by-chapter summaries of this book...\n\n"
                    )
                )
            ],
            "book_id": book_id
        }
    else:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Ok. Let's try a recommendation related with another book.\nGive me a title and author as reference to look for one similar to it.\nType 'exit' to quit."
                    )
                )
            ],
            "book_id": None
        }
