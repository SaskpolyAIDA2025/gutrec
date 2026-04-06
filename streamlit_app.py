from langchain_core import messages
import streamlit as st
import os
import re
import math
import requests
import weaviate
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from src.graph.stategraph import StateGraph
from src.utils.book_downloader import (
    download_gutenberg_book,
    split_into_chapters,
    prepare_chapter_chunks,
    get_gutenberg_id
)
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# -----------------------
# Load environment variables
# -----------------------
load_dotenv()
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
if not GOOGLE_BOOKS_API_KEY:
    st.error("Please set GOOGLE_BOOKS_API_KEY in your .env file.")
    st.stop()

# -----------------------
# Weaviate
# -----------------------
@st.cache_resource
def init_weaviate_client():
    try:
        client = weaviate.connect_to_local(
            port=8081,
            grpc_port=50051
        )
        client.connect()

        if client.is_ready():
            print("✅ Weaviate is ready")
        else:
            print("❌ Weaviate not ready")

        return client
    except Exception as e:
        st.error(f"Weaviate init error: {e}")
        return None

client = init_weaviate_client()

# -----------------------
# Ollama LLM & Embedding
# -----------------------
embedding_model = "mxbai-embed-large"
llm_model = "gemma3:4b"
ollama_llm = OllamaLLM(model=llm_model)

def embed_text(text):
    payload = {"model": embedding_model, "prompt": text}
    with requests.post("http://localhost:11434/api/embeddings", json=payload) as response:
        response.raise_for_status()
        return response.json()["embedding"]

# -----------------------
# Summarization Model
# -----------------------
tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")

def summarize_chunk(text, max_len=200, min_len=50):
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=max_len,
        min_length=min_len,
        num_beams=4
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def chunk_text(text, max_tokens=900, overlap=100):
    tokens = tokenizer.tokenize(text)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i:i + max_tokens]
        chunks.append(tokenizer.convert_tokens_to_string(chunk))
        i += max_tokens - overlap
    return chunks

def summarize_long(text):
    chunks = chunk_text(text)
    partial = [summarize_chunk(c) for c in chunks]
    return summarize_chunk(" ".join(partial))

# -----------------------
# Nodes
# -----------------------
import json
import re

def extraction_node(state):
    user_input = state.get("user_input", "")

    prompt = f"""
Extract the book title and author from this input.

Input: {user_input}

Return ONLY JSON like this:
{{"title": "...", "author": "..."}}
"""

    try:
        res = ollama_llm.invoke(prompt)

        print("DEBUG raw LLM response:", res)

        # Extract JSON using regex (VERY IMPORTANT)
        match = re.search(r"\{.*\}", res, re.DOTALL)

        if not match:
            raise ValueError("No JSON found in LLM response")

        extracted = json.loads(match.group())

        print("DEBUG extracted:", extracted)

        state["extraction"] = extracted

        if extracted.get("title"):
            state["query"] = extracted["title"]
        else:
            state["clarification_turns"] = 0

    except Exception as e:
        print("Extraction error:", e)
        state["clarification_turns"] = 0

    return state

def clarification_node(state):
    state["clarification_turns"] += 1
    state["awaiting_clarification"] = True
    state["clarification_msg"] = f"❓ Clarify your book (attempt {state['clarification_turns']})"
    return state

def broad_idea_node(state):
    res = ollama_llm.invoke(f"Summarize intent: {state.get('user_input','')}")
    state["broad_idea"] = res
    return state

def enrichment_node(state):
    query = state.get("query")
    if not query:
        return state

    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={GOOGLE_BOOKS_API_KEY}&maxResults=3"
    try:
        data = requests.get(url).json()
        books = []
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            books.append({
                "title": info.get("title", ""),
                "authors": ", ".join(info.get("authors", [])),
                "categories": ", ".join(info.get("categories", [])),
                "description": info.get("description", ""),
                "publishedDate": info.get("publishedDate", ""),
                "previewLink": info.get("previewLink", "")
            })
        state["enriched_books"] = books
    except Exception as e:
        st.warning(f"Google Books error: {e}")
        state["enriched_books"] = []

    return state

def search_node(state):
    print("DEBUG: entering search_node")

    if client is None:
        state["results"] = []
        return state

    query = state.get("query") or state.get("broad_idea")
    print("DEBUG query:", query)

    if not query:
        state["results"] = []
        return state

    try:
        vector = embed_text(query)
        collection = client.collections.get("Book")

        response = collection.query.near_vector(
            near_vector=vector,
            limit=5
        )

        state["results"] = [obj.properties for obj in response.objects]

    except Exception as e:
        st.warning(f"Weaviate error: {e}")
        state["results"] = []

    return state

def responder_node(state):
    print("DEBUG: entering responder_node")

    messages = []

    if state.get("enriched_books"):
        messages.append("📖 Google Books:")
        for b in state["enriched_books"]:
            messages.append(f"**{b['title']}** by {b['authors']}")

    if state.get("results"):
        messages.append("🔍 Recommendations:")
        for b in state["results"]:
            messages.append(f"**{b.get('title')}** by {b.get('authors')}")

    if not messages:
        messages.append("⚠️ No results found. Try another query.")

    print("DEBUG messages:", messages)

    state["messages"] = messages
    state["awaiting_clarification"] = False
    return state


# -----------------------
# Workflow
# -----------------------
workflow = StateGraph(state_name="conversation")
START, END = "START", "END"

workflow.add_node("extract", extraction_node)
workflow.add_node("clarify", clarification_node)
workflow.add_node("broad", broad_idea_node)
workflow.add_node("enrich", enrichment_node)
workflow.add_node("search", search_node)
workflow.add_node("respond", responder_node)

workflow.add_edge(START, "extract")
workflow.add_conditional_edges(
    "extract",
    lambda s: "query" not in s,
    {"clarify": "clarify", "broad": "broad"}
)
workflow.add_edge("clarify", "broad")
workflow.add_edge("broad", "search")
workflow.add_edge("extract", "enrich")
workflow.add_edge("enrich", "search")
workflow.add_edge("search", "respond")
workflow.add_edge("respond", END)

# -----------------------
# Streamlit UI
# -----------------------
st.title("📚 Project Gutenberg Recommendation Platform and AI Chat")

if "history" not in st.session_state:
    st.session_state.history = []

if "state" not in st.session_state:
    st.session_state.state = {"clarification_turns": 0}

def process_user_input(user_input):
    state = st.session_state["state"]
    state["user_input"] = user_input

    state = workflow.run(state)  # ✅ reassign

    if state.get("awaiting_clarification"):
        st.session_state["awaiting_clarification"] = True
        st.session_state["state"] = state
        return state.get("clarification_msg", "Please clarify.")

    if state.get("messages"):
        for msg in state["messages"]:
            st.session_state["history"].append(msg)

    # Clear messages after displaying
    state["messages"] = []

    st.session_state["state"] = state
    return None

# Input
user_input = st.text_input("Give me a title and author as reference to look for one similar to it:")

if st.button("Send") and user_input:
    msg = process_user_input(user_input)
    if msg:
        st.session_state.history.append(msg)

# Output
for msg in st.session_state.history:
    st.markdown(msg)