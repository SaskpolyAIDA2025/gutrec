import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
from src.books_api import get_book_metadata
import weaviate

# -------------------------
# Connect to local Weaviate (v3 client)
# -------------------------
client = weaviate.Client(url="http://localhost:8081")

if client.is_ready():
    st.sidebar.success("✅ Connected to Weaviate")
else:
    st.sidebar.error("❌ Weaviate not ready")

# -------------------------
# Page Config
# -------------------------
st.set_page_config(
    page_title="Gutenberg Discovery Platform",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Project Gutenberg Discovery & Recommendation Platform")
st.markdown("""
Discover books from **Project Gutenberg** using **semantic AI search**.

Enter a **book title**, **author**, or **describe a theme** and the system will find similar books.
""")

# -------------------------
# User Input
# -------------------------
user_input = st.text_input(
    "Enter a book title, author, or theme",
    placeholder="Example: Books like Moby Dick or stories about sea adventures"
)

# -------------------------
# Search Button
# -------------------------
if st.button("Find Similar Books"):

    if not user_input.strip():
        st.warning("Please enter a query.")
        st.stop()

    # -------------------------
    # Query Weaviate for similar books
    # -------------------------
    try:
        query_result = (
            client.query
            .get("Book", ["title", "authors", "download_count", "subjects", "bookshelves", "summaries"])
            .with_near_text({"concepts": [user_input]})  # Semantic search
            .with_limit(5)
            .do()
        )

        books = query_result.get("data", {}).get("Get", {}).get("Book", [])

        if not books:
            st.warning("No recommendations found.")
            st.stop()

        # -------------------------
        # Display results
        # -------------------------
        st.subheader("Recommended Books")

        for book in books:
            col1, col2 = st.columns([1,4])

            with col1:
                st.image(
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/480px-No-Image-Placeholder.svg.png",
                    width=120
                )

            with col2:
                st.markdown(f"### {book.get('title', 'Unknown')}")
                st.write(f"**Author:** {book.get('authors', 'Unknown')}")
                st.write(f"**Downloads:** {book.get('download_count', 'N/A')}")
                if book.get("subjects"):
                    st.write(f"**Subjects:** {book['subjects']}")
                if book.get("bookshelves"):
                    st.write(f"**Bookshelves:** {book['bookshelves']}")
                if book.get("summaries"):
                    with st.expander("Summary"):
                        st.write(book["summaries"])

            st.markdown("---")

    except Exception as e:
        st.error(f"Error querying Weaviate: {e}")