import streamlit as st
from src.graph.workflow import app
from langchain_core.messages import AIMessage, HumanMessage


# -------------------------------------------------------------------
# Helper function
# -------------------------------------------------------------------
def get_gutenberg_cover_url(book_id):
    """
    Returns the best available Project Gutenberg cover URL.
    Falls back to None if no cover exists.
    """
    base = f"https://www.gutenberg.org/cache/epub/{book_id}"

    # Try medium, small, then full
    candidates = [
        f"{base}/pg{book_id}.cover.medium.jpg",
        f"{base}/pg{book_id}.cover.small.jpg",
        f"{base}/pg{book_id}.cover.jpg",
    ]

    import requests
    for url in candidates:
        try:
            r = requests.head(url, timeout=2)
            if r.status_code == 200:
                return url
        except Exception:
            pass

    return None


st.set_page_config(
    layout="wide",
    page_title="Project Gutenberg Recommendation Platform",
    page_icon="📚",
)


# -------------------------------------------------------------------
# 1. Initialize visible transcript
# -------------------------------------------------------------------
if "message_history" not in st.session_state:
    st.session_state.message_history = [
        AIMessage(
            content=(
                "Welcome to the Gutenberg Book Recommendation system.\n"
                "Give me a title and author as reference to look for one similar to it.\n"
                "Type 'exit' to quit."
            )
        )
    ]

# -------------------------------------------------------------------
# 2. Initialize LangGraph working state
# -------------------------------------------------------------------
if "graph_state" not in st.session_state:
    st.session_state.graph_state = {
        "messages": st.session_state.message_history.copy(),
        "loop_count": 0,
        "reset_messages": False,
        "broad_query": "",
        "results": []
    }

state = st.session_state.graph_state

# Layout
left_col, main_col, right_col = st.columns([1, 2, 1])

# -------------------------------------------------------------------
# 3. Clear Chat button
# -------------------------------------------------------------------
with left_col:
    if st.button("Clear Chat"):
        st.session_state.message_history = []
        st.session_state.graph_state = {
            "messages": [],
            "loop_count": 0,
            "reset_messages": False,
            "broad_query": "",
            "results": []
        }
        state = st.session_state.graph_state

# -------------------------------------------------------------------
# 4. Main chat area
# -------------------------------------------------------------------
with main_col:
    user_input = st.chat_input("Type here...")

    # Reset graph memory only
    if state.get("reset_messages", False):
        state["messages"] = []
        state["loop_count"] = 0
        state["reset_messages"] = False
        state["broad_query"] = state.get("broad_query", "")

    if user_input:
        # A. Add user message to transcript + graph state
        user_msg = HumanMessage(content=user_input)
        st.session_state.message_history.append(user_msg)
        state["messages"].append(user_msg)

        # B. Invoke LangGraph
        response = app.invoke(state)

        # C. Update graph state
        state["messages"] = response.get("messages", state["messages"])
        state["loop_count"] = response.get("loop_count", state["loop_count"])
        state["reset_messages"] = response.get("reset_messages", False)
        state["broad_query"] = response.get("broad_query", state.get("broad_query", ""))

        # NEW: update recommendations
        state["results"] = response.get("results", state.get("results", []))

        # D. Sync transcript
        st.session_state.message_history = state["messages"]

    # -------------------------------------------------------------------
    # 5. Render chat history (reverse order)
    # -------------------------------------------------------------------
    for i in range(1, len(st.session_state.message_history) + 1):
        this_message = st.session_state.message_history[-i]
        if isinstance(this_message, AIMessage):
            box = st.chat_message("assistant")
        else:
            box = st.chat_message("user")
        box.markdown(this_message.content)

# -------------------------------------------------------------------
# 6. Sidebar: Book Recommendations
# -------------------------------------------------------------------
with right_col:
    st.header("📚 Recommendations")

    results = state.get("results", [])

    if not results:
        st.info("No recommendations yet.")
    else:
        for book in results:
            with st.container(border=True):
                # --- COVER IMAGE ---
                cover_url = None
                if book.get("id_pg"):
                    cover_url = get_gutenberg_cover_url(book["id_pg"])

                if cover_url:
                    st.image(cover_url, width="content") # "stretch"
                else:
                    st.write("*(No cover available)*")
                
                # Title
                st.subheader(book.get("title", "Untitled"))

                # Authors
                authors = book.get("authors", [])
                if authors:
                    st.markdown(f"**Authors:** {authors}")

                # # Subjects / Bookshelves
                # subjects = book.get("subjects", "")
                # if subjects:
                #     st.markdown(f"**Subjects:** {subjects}")

                # shelves = book.get("bookshelves", "")
                # if shelves:
                #     st.markdown(f"**Bookshelves:** {shelves}")

                # # Download count
                # if book.get("download_count") is not None:
                #     st.markdown(f"**Downloads:** {book['download_count']}")

                # Summary
                summaries = (book.get("summaries", ""))
                if summaries:
                    with st.expander("Summary", expanded=False):
                        st.write(summaries)

                # Certainty
                if book.get("certainty") is not None:
                    st.progress(book["certainty"])
                    st.caption(f"Match certainty: {book['certainty']:.2f}")
