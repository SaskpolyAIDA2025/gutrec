import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from src.utils.chapter_summaries import get_all_chapter_summaries
from src.utils.sentiment_graph import build_emotion_arc_data, plot_emotion_arc
from src.graph.workflow import app
from src.graph.workflow_graph import get_book_qa_app


# Navigation state
if "ui_mode" not in st.session_state:
    st.session_state.ui_mode = "chat"   # or "detail"

if "selected_book" not in st.session_state:
    st.session_state.selected_book = None


# -------------------------------------------------------------------
# Helper functions
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


@st.cache_resource
def cached_emotion_data(book_id: int):
    return build_emotion_arc_data(book_id)


# -------------------------------------------------------------------
# Custom CSS for hover effects on title buttons
# -------------------------------------------------------------------
st.markdown("""
<style>
/* Make all Streamlit buttons look like clean text links */
div.stButton > button {
    background-color: transparent;
    color: #1f6feb;
    border: none;
    padding: 0;
    font-size: 1.1rem;
    text-align: left;
}

/* Hover effect */
div.stButton > button:hover {
    color: #d63384;        /* pink-ish hover color */
    text-decoration: underline;
    cursor: pointer;
}

/* Remove the focus outline */
div.stButton > button:focus {
    outline: none;
    box-shadow: none;
}
</style>
""", unsafe_allow_html=True)


st.set_page_config(
    layout="wide",
    page_title="Project Gutenberg Recommendation Platform",
    page_icon="📚",
)


# -------------------------------------------------------------------
# Initialize visible transcript
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
# Initialize LangGraph working state
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
st.title("Project Gutenberg Discovery & Recommendation Platform")

# Layout
left_col, main_col, right_col = st.columns([1, 2, 2])

# -------------------------------------------------------------------
# Clear Chat button
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


######################################################
# -------------------------------------------------------------------
# DETAIL PAGE (if a book is clicked)
# -------------------------------------------------------------------
if st.session_state.ui_mode == "detail":
    book = st.session_state.selected_book
    book_qa_app = get_book_qa_app()
    book_id = book.get("id_pg")

    if "book_chat_history" not in st.session_state:
        st.session_state.book_chat_history = {}    # {book_id: list[(q, a)]}

    # Ensure chat history exists for this book
    if book_id not in st.session_state.book_chat_history:
        st.session_state.book_chat_history[book_id] = []

    # Top button
    if st.button("⬅ Back to recommendations"):
        st.session_state.ui_mode = "chat"
        st.session_state.selected_book = None
        st.rerun()

    st.title(book.get("title", "Untitled"))

    # ===== TOP: TWO COLUMNS =====
    col_left, col_right = st.columns([1, 2])

    # ---------------- LEFT: cover, authors, downloads ----------------
    with col_left:
        # Cover
        cover_url = None
        if book_id:
            cover_url = get_gutenberg_cover_url(book["id_pg"])
        if cover_url:
            st.image(cover_url, width=300)

        # Authors
        authors = book.get("authors", "")
        if authors:
            st.subheader("Authors")
            st.write(authors)

        # Summary
        summaries = book.get("summaries", "")
        if summaries:
            with st.expander("Summary", expanded=True):
                st.write(summaries)
        
        # Download buttons
        if book_id:
            st.subheader("Download")
            st.markdown(f"[EPUB](https://www.gutenberg.org/ebooks/{book_id}.epub.images)")
            st.markdown(f"[Kindle](https://www.gutenberg.org/ebooks/{book_id}.kf8.images)")
            st.markdown(f"[Plain Text](https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt)") # (f"[Plain Text](https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt)")
        
        # Chatbot
        st.markdown("---")
        st.subheader("Chat about this book")

        if not book_id:
            st.info("No Project Gutenberg ID available for book Q&A.")
        else:
            # Show previous Q&A turns
            history = st.session_state.book_chat_history.get(book_id, [])
            for q, a in history:
                with st.chat_message("user"):
                    st.markdown(q)
                with st.chat_message("assistant"):
                    st.markdown(a)

            # New question input
            user_q = st.chat_input("Ask a question about this book...")
            if user_q:
                # Show user message immediately
                with st.chat_message("user"):
                    st.markdown(user_q)

                # Call LangGraph QA branch
                with st.spinner("Thinking..."):
                    result = book_qa_app.invoke({
                        "book_id": int(book_id),
                        "question": user_q
                    })

                answer = result.get("answer", "I couldn't generate an answer.")

                # Show assistant answer
                with st.chat_message("assistant"):
                    st.markdown(answer.content)

                # Save to history
                st.session_state.book_chat_history[book_id].append((user_q, answer.content))

    
    # ---------------- RIGHT: chapter summaries ----------------
    with col_right:
        # --- EMOTION ARC ---
        if book_id:
            st.subheader("Emotional Arc of the Book")
            with st.spinner("Computing emotional arc..."):
                smoothed_emotions, chapter_boundaries = cached_emotion_data(int(book_id))

            # Emotion toggles
            st.markdown("**Select emotions to display:**")
            col1, col2, col3, col4 = st.columns(4)

            show_joy = col1.checkbox("Joy", value=True)
            show_fear = col2.checkbox("Fear", value=True)
            show_anger = col3.checkbox("Anger", value=True)
            show_sadness = col4.checkbox("Sadness", value=True)

            visible = []
            if show_joy: visible.append("joy")
            if show_fear: visible.append("fear")
            if show_anger: visible.append("anger")
            if show_sadness: visible.append("sadness")

            if not visible:
                st.info("Select at least one emotion to display.")
            else:
                fig = plot_emotion_arc(smoothed_emotions, chapter_boundaries, visible)
                if fig is None:
                    st.info("Could not build emotional arc for this book.")
                else:
                    st.pyplot(fig)
        else:
            st.info("No Project Gutenberg ID available for emotion graph.")
        
        # --- CHAPTER SUMMARIES ---
        st.subheader("Chapters")

        if book_id:
            with st.spinner("Loading chapter summaries..."):
                chapters, err = get_all_chapter_summaries(int(book_id))

            if err:
                st.warning(err)
            elif not chapters:
                st.info("No chapters detected or no summaries available.")
            else:
                for ch in chapters:
                    label = f"{ch['title']}"
                    with st.expander(label, expanded=False):
                        st.write(ch["summary"])
        else:
            st.info("No Project Gutenberg ID available for chapter summaries.")

    st.stop()  # Prevents chat UI from rendering underneath
######################################################


# -------------------------------------------------------------------
# Main chat area
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
    # Render chat history (reverse order)
    # -------------------------------------------------------------------
    for i in range(1, len(st.session_state.message_history) + 1):
        this_message = st.session_state.message_history[-i]
        if isinstance(this_message, AIMessage):
            box = st.chat_message("assistant")
        else:
            box = st.chat_message("user")
        box.markdown(this_message.content)

# -------------------------------------------------------------------
# Sidebar: Book Recommendations
# -------------------------------------------------------------------
with right_col:
    st.header("📚 Recommendations")

    results = state.get("results", [])

    if not results:
        st.info("No recommendations yet.")
    else:
        # Number of columns
        num_cols = 2
        cols = st.columns(num_cols)

        for idx, book in enumerate(results):
            col = cols[idx % num_cols]  # rotate through columns

            with col:
                with st.container(border=True):
                    # --- COVER IMAGE ---
                    cover_url = None
                    if book.get("id_pg"):
                        cover_url = get_gutenberg_cover_url(book["id_pg"])

                    if cover_url:
                        st.image(cover_url, width="content") # stretch
                    else:
                        st.write("*(No cover available)*")
                    
                    # Title (clickable)
                    if st.button(book.get("title", "Untitled"), key=f"title_{book['id_pg']}"):
                        st.session_state.ui_mode = "detail"
                        st.session_state.selected_book = book
                        st.rerun()

                    # Authors
                    authors = book.get("authors", [])
                    if authors:
                        st.markdown(f"**Authors:** {authors}")

                    # Summary
                    summaries = (book.get("summaries", ""))
                    if summaries:
                        with st.expander("Summary", expanded=False):
                            st.write(summaries)

                    # Certainty
                    if book.get("certainty") is not None:
                        st.progress(book["certainty"])
                        st.caption(f"Match certainty: {book['certainty']:.2f}")
