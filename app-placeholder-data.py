import streamlit as st
import weaviate
from weaviate.auth import AuthApiKey

# -----------------------
# Ollama embedding
# -----------------------
# We'll define a helper for generating embeddings
# You need nomic-embed-text:latest running locally or in Ollama service
def get_embedding(text):
    import subprocess, json
    # Call Ollama CLI to get embeddings
    cmd = ["ollama", "embed", "nomic-embed-text:latest", text, "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    embedding = json.loads(result.stdout)["embedding"]
    return embedding

# -----------------------
# Weaviate Cloud credentials
# -----------------------
WEAVIATE_URL = "https://cywukygmt0k0kyk3dzng.c0.asia-southeast1.gcp.weaviate.cloud"
WEAVIATE_API_KEY = "cXBHd2Z2Zm56NlE3S2xkUF90Y2xIRWF0aXNWdk9Wa29DLzQ1UjRnOGt1Q29ZWnlNY1RhRldpOFNWQXFRPV92MjAw"

client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(WEAVIATE_API_KEY)
)

# -----------------------
# Streamlit UI
# -----------------------
st.title("📚 Gutenberg Book Recommender")

search_tab, book_tab = st.tabs(["🔍 Search", "📖 Book details"])

# -----------------------
# SEMANTIC SEARCH TAB
# -----------------------
with search_tab:
    st.header("Search books")
    query = st.text_input("Type a topic, title, author, or any text")

    min_downloads = st.slider(
        "Minimum downloads",
        0, 50000, 0, step=500
    )

    if query:
        with st.spinner("Generating query embedding..."):
            try:
                # Attempt embedding
                query_vector = get_embedding(query)
                print(query_vector)
            except Exception as e:
                st.error(
                    "⚠️ Could not generate embedding. "
                    "It seems your Ollama CLI does not support embeddings. "
                    f"Error details: {e}"
                )
                st.stop()

# -----------------------
# BOOK DETAILS TAB
# -----------------------
with book_tab:
    st.header("Book details")
    book_title = st.text_input("Enter exact book title")

    if book_title:
        result = (
            client.query
            .get("Book", [
                "title", "authors", "subjects", "languages", "download_count", "summaries"
            ])
            .with_where({
                "path": ["title"],
                "operator": "Equal",
                "valueText": book_title
            })
            .with_limit(1)
            .do()
        )

        books = result.get("data", {}).get("Get", {}).get("Book", [])

        if not books:
            st.warning("Book not found.")
        else:
            book = books[0]
            st.subheader(book["title"])
            st.write(f"**Authors:** {book['authors']}")
            st.write(f"**Languages:** {book['languages']}")
            st.write(f"**Downloads:** {book['download_count']}")
            st.write(f"**Subjects:** {book['subjects']}")
            with st.expander("See summary"):
                st.write(book["summaries"])