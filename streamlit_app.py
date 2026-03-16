import sys
import os
import requests
import weaviate
import streamlit as st

# Ensure the app can find your local source modules
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# -------------------------
# Configuration & Connection
# -------------------------
WEAVIATE_URL = "http://localhost:8081"
OLLAMA_URL = "http://localhost:11434/api/embeddings"

client = weaviate.Client(url=WEAVIATE_URL)

# -------------------------
# Helper Functions (Aligned with your working script)
# -------------------------

def embed_query(text: str):
    """Generates embeddings using local Ollama instance."""
    payload = {
        "model": "mxbai-embed-large",
        "prompt": text
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json()["embedding"]

def semantic_search(query_text: str, k: int = 5):
    """Performs vector search by manually passing the Ollama embedding."""
    embedding = embed_query(query_text)
    result = (
        client.query
        .get("Book", ["title", "authors", "bookshelves", "subjects", "download_count", "summaries"])
        .with_near_vector({"vector": embedding})
        .with_limit(k)
        .with_additional(["certainty"])
        .do()
    )
    
    # Check for errors in the response
    if "errors" in result:
        raise Exception(result["errors"][0]["message"])
        
    return result.get("data", {}).get("Get", {}).get("Book", [])

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(
    page_title="Gutenberg Discovery Platform",
    page_icon="📚",
    layout="wide"
)

# Sidebar Status
if client.is_ready():
    st.sidebar.success("✅ Weaviate Connected")
else:
    st.sidebar.error("❌ Weaviate Disconnected")

st.title("📚 Project Gutenberg Discovery & Recommendation Platform")
st.markdown("""
Discover books using **Semantic AI Search** powered by **Ollama** and **Weaviate**.
""")

user_input = st.text_input(
    "Enter a book title, author, or describe a theme",
    placeholder="Example: stories about existential dread in industrial cities"
)

if st.button("Find Similar Books"):
    if not user_input.strip():
        st.warning("Please enter a query.")
        st.stop()

    with st.spinner("Searching for the best matches..."):
        try:
            books = semantic_search(user_input, k=5)

            if not books:
                st.info("No recommendations found for that query.")
            else:
                st.subheader("Top Recommendations")
                for book in books:
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        # Standard placeholder image
                        st.image(
                            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/480px-No-Image-Placeholder.svg.png",
                            width=120
                        )

                    with col2:
                        st.markdown(f"### {book.get('title', 'Unknown Title')}")
                        st.write(f"**Author(s):** {book.get('authors', 'Unknown')}")
                        st.write(f"**Downloads:** {book.get('download_count', 'N/A')}")
                        
                        if book.get("subjects"):
                            st.caption(f"**Subjects:** {book['subjects']}")
                        
                        if book.get("summaries"):
                            with st.expander("Read Summary"):
                                st.write(book["summaries"])
                    
                    st.markdown("---")

        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to Ollama. Make sure Ollama is running (`ollama serve`).")
        except Exception as e:
            st.error(f"❌ Error during search: {e}")