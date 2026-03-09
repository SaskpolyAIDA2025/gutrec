# Project Gutenberg Discovery & Recommendation Platform  
### *LangGraph‑Powered Conversational Book Search & Recommendation Engine*

A modern AI‑driven system that transforms how readers explore Project Gutenberg’s public‑domain library.  
The platform now uses **LangGraph** to orchestrate a deterministic, multi‑node conversational workflow for book identification, metadata enrichment, and semantic search.

Capstone Project for AIDA 2025 — Angie, Eladio, KNK  
---

## Overview

This project provides an end‑to‑end pipeline for transforming raw Project Gutenberg metadata into a fully searchable, vector‑powered discovery system.  
The updated version introduces a **LangGraph‑based conversational agent** that handles:

- Structured extraction of book titles/authors  
- Clarification loops when extraction fails  
- Fallback “broad idea” summarization  
- Google Books metadata enrichment  
- Semantic search over a local Weaviate vector database  
- Multi‑turn conversation with persistent state  

The entire system runs locally for privacy, reproducibility, and full control over data and models.

---

## Key Features

### Data Pipeline
- Fetch raw metadata from the **Gutendex API**
- Clean and normalize metadata (languages, subjects, bookshelves)
- Generate embeddings using **mxbai‑embed‑large** (Ollama)
- Store vectorized book objects in **Weaviate**
- Perform semantic search using near‑vector queries

### Conversational Intelligence (LangGraph)
- Deterministic multi‑node workflow
- Structured extraction using Gemma 3 (4B)
- Automatic clarification loop (max 3 turns)
- Fallback “broad idea” summarization when no title is found
- Google Books metadata enrichment
- Final recommendation generation
- Persistent message history using `add_messages`

---

## Updated Architecture (LangGraph)

### High‑Level LangGraph Flow
User Input │ ▼ [Extraction Node] │ ├── title found → [Enrichment Node] │ ├── no title + loops < 3 → [Clarification Node] │ └── no title + loops ≥ 3 → [Broad Idea Node] │ ▼ [Search Node] │ ▼ [Respond Node]


### Node Responsibilities (Short Descriptions)

- **Extraction Node**  
  Uses a structured LLM chain to extract title/author from user input.

- **Clarification Node**  
  Asks follow‑up questions when extraction fails.

- **Broad Idea Node**  
  Summarizes the user’s intent after 3 failed clarification attempts.

- **Enrichment Node**  
  Fetches metadata from Google Books (description, categories, etc.).

- **Search Node**  
  Performs semantic search in Weaviate using either:
  - extracted title/metadata, or  
  - broad‑idea summary  

- **Responder Node**  
  Formats and returns final recommendations.

---

## LangGraph Implementation

### Example: Workflow Definition (`workflow.py`)

```python
workflow = StateGraph(AgentState)

workflow.add_node("extract", extraction_node)
workflow.add_node("clarify", clarification_node)
workflow.add_node("broad", broad_idea_node)
workflow.add_node("enrich", enrichment_node)
workflow.add_node("search", search_node)
workflow.add_node("respond", responder_node)

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
workflow.add_edge("respond", END)

app = workflow.compile()
```

How the Conversation Loop Works
- run_chat.py maintains a persistent state dictionary across turns
- Messages are appended automatically using add_messages
- Each user turn triggers a full LangGraph execution
- After each turn, extraction‑related fields are cleared:
  - extraction
  - book_metadata
  - results
- The loop ends when the user types exit or quit
- On shutdown, Weaviate and Ollama connections are closed cleanly

## Data Flow (End‑to‑End)
fetch_books.py
    ↓
dataset_process.py
    ↓
gutenindex_to_weaviate_embedding.py
    ↓
Weaviate Vector DB
    ↓
run_chat.py → LangGraph → Recommendations

## Installation

### 1. Clone the repository

git clone <your-repo-url>
cd <project-folder>

### 2. Create and activate a virtual environment

python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows

### 3. Install dependencies

pip install -r requirements.txt

## Environment Setup

### 1. Install Ollama

Download from: https://ollama.com/download
Pull required models:

ollama pull gemma3:4b
ollama pull mxbai-embed-large

### 2. Start Weaviate (Docker)

Example docker-compose.yml:

```YAML
version: '4.0'
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - ./weaviate_data:/var/lib/weaviate
```

Run:

docker compose up -d

### 3. Configure Google Books API

Create a  .env file:

GOOGLE_BOOKS_API_KEY=your_key_here

## Usage

### Step 1 — Fetch raw metadata

python fetch_books.py

### Step 2 — Preprocess dataset

python dataset_process.py

### Step 3 — Ingest into Weaviate

python gutenindex_to_weaviate_embedding.py

### Step 4 — Run the chatbot

python run_chat.py

Example:
You: I'm looking for the book about time thieves by Michael Ende.
AI: Great, I found the title: Momo.
AI: Found metadata for Momo. Searching for similar books...
AI: Here are some books I found...

## Project Structure

```
project/
│
├── src/
│   ├── graph/
│   │   ├── nodes.py
│   │   ├── state.py
│   │   └── workflow.py
│   ├── books_api.py
│   ├── llm_chain.py
│   ├── run_chat.py
│   ├── schemas.py
│   ├── search_query.py
│   └── __pycache__/
│
├── fetch_books.py
├── gutenindex_to_weaviate_embedding.py
├── dataset_process.py
├── books_metadata.csv
├── processed_books.csv
├── requirements.txt
├── .env
└── README.md
```

### Roadmap

- Add RAG‑based summarization
- Add user profiles for personalized recommendations
- Add web UI (streamline or FastAPI + React)
- Add multilingual search
- Add book‑to‑book similarity graph

### License

All rights reserved.
This project is not licensed for redistribution or commercial use.