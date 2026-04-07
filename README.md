# Project Gutenberg Discovery & Recommendation Platform  
### *LangGraph‑Powered Conversational Recommendation + Streamlit UI*

A modern AI‑driven system that transforms how readers explore Project Gutenberg’s public‑domain library.
The platform combines:

- **LangGraph** for deterministic conversational workflows
- **Weaviate** for semantic vector search
- **Ollama** for local LLM inference
- **Streamlit** for a polished, interactive UI
- **RAG‑based book‑specific Q&A**
- **Emotion arc visualization**
- **Chapter‑level summarization**

Capstone Project for AIDA 2025 — Angie, Eladio, KNK  
---

## Overview

This project provides an end‑to‑end pipeline for transforming raw Project Gutenberg metadata into a fully searchable, vector‑powered discovery system.  
The updated version introduces a **LangGraph‑based conversational agent** that handles:

The system now includes:

- A **LangGraph conversational agent** for book identification
- A **Streamlit UI** for real‑time interaction
- A **book detail page** with summaries, emotional arcs, and RAG Q&A
- A **Weaviate vector database** for semantic search
- A **local inference stack** (Gemma 3 + mxbai‑embed‑large)

Everything runs **locally** for privacy, reproducibility, and full control.

---
## Architecture Overview

### High‑Level System Diagram

```
User
 │
 ▼
Streamlit UI
 │
 ▼
LangGraph Conversational Workflow
 │
 ├── Extraction Node (title/author)
 ├── Clarification Loop (max 2)
 ├── Broad-Idea Summarization
 ├── Google Books Enrichment
 └── Semantic Search (Weaviate)
 │
 ▼
Recommendations + Book Detail Page
 │
 ├── Chapter Summaries
 ├── Emotional Arc (Transformers)
 └── Book-Specific RAG QA (LangGraph)
 ```

## LangGraph Conversational Workflow

The main conversational agent is defined in src/graph/workflow.py.

### Node Responsibilities

- **Extraction Node**

Extracts structured title/author from user input.

- **Clarification Node**

Asks follow‑up questions when extraction fails.

- **Broad Idea Node**

Summarizes user intent after 2 failed attempts.

- **Enrichment Node**

Fetches metadata from Google Books.

- **Search Node**

Performs semantic search in Weaviate.

- **Responder Node**

Formats final recommendations.

### Routing Logic

```
def should_continue(state):
    title = state["extraction"].get("title", "")
    loops = state.get("loop_count", 0)

    if title:
        return "enrich"
    if loops < 2:
        return "clarify"
    return "broad"
```

### Graph Structure

```
START → extract
        │
        ├── title found → enrich → search → respond → END
        ├── no title + loops < 2 → clarify → END
        └── no title + loops ≥ 2 → broad → search → respond → END
```

## Book‑Specific RAG QA Workflow

Defined in src/graph/workflow_graph.py.

### Steps

**1. Ingestion Node**

- Downloads the book

- Splits into chapters

- Chunks text

- Embeds chunks

- Stores them in a temporary vector index

**2. QA Node**

- Retrieves relevant chunks

- Generates an answer using RAG

### Graph
```
ingest_book → answer_question → END
```

This workflow powers the **"Chat about this book"** section in the UI.

## Streamlit UI (Full Feature Breakdown)

The UI lives in streamlit_frontend.py and provides a polished, multi‑panel experience.

### UI Layout

The interface uses a **three‑column layout**:

```
[Left]     [Main Chat]     [Right Sidebar: Recommendations]
```

#### Left Column
- **Clear Chat** button

- Resets LangGraph state and transcript

#### Main Column

- **Chat interface** powered by LangGraph

- Persistent message history

- Automatic state synchronization

- Full multi‑turn conversation

#### Right Column

- **Live book recommendations**

- Cover images (auto‑detected via Gutenberg URLs)

- Clickable titles → open detail page

- Summaries + certainty score

### Book Detail Page (Streamlit)

When a user clicks a recommended book, the UI switches to **detail mode**.

#### Features

**1. Book Cover + Metadata**

- Auto‑fetched cover from Gutenberg

- Authors

- Summary

- Download links (EPUB, Kindle, Plain Text)

**2. Book‑Specific Chat (RAG QA)**

- Each book has its own chat history

- Uses the LangGraph RAG pipeline

- Answers grounded in the book's text

**3. Emotional Arc Visualization**

Powered by:

- j-hartmann/emotion-english-distilroberta-base

- Paragraph‑level emotion scoring

- Smoothed curves

- Chapter boundary markers

Users can toggle:

- Joy

- Fear

- Anger

- Sadness

**4. Chapter Summaries**

- Generated via node_chapter_summarizer

- Displayed in collapsible expanders

- One per chapter

## Sentiment & Chapter Summary Pipeline

### Emotion Arc

Defined in src/utils/sentiment_graph.py.

Pipeline:

1. Download book

2. Split into chapters

3. Chunk paragraphs

4. Run emotion classifier

5. Smooth curves

6. Plot with chapter boundaries

### Chapter Summaries

Defined in src/utils/chapter_summaries.py.

```
summaries = summarize_chapters_node({"book_id": book_id})
```

### Data Pipeline (End‑to‑End)

```
fetch_books.py
    ↓
dataset_process.py
    ↓
gutenindex_to_weaviate_embedding.py
    ↓
Weaviate Vector DB
    ↓
run_chat.py → LangGraph → Recommendations
    ↓
streamlit_frontend.py → UI
```
---

## Updated Project Structure

Reflecting your latest screenshot:

```
gutrec/
│
├── src/
│   ├── graph/
│   │   ├── node_rag_qa.py
│   │   ├── node_book_ingestion_pipeline.py
│   │   ├── node_chapter_summarizer.py
│   │   ├── nodes.py
│   │   ├── state.py
│   │   ├── workflow.py
│   │   └── workflow_graph.py
│   │
│   ├── utils/
│   │   ├── book_cache.py
│   │   ├── book_downloader.py
│   │   ├── book_downloaded.py
│   │   ├── chapter_summaries.py
│   │   ├── ollama_embedded.py
│   │   ├── parallel_embedded.py
│   │   ├── sentiment_graph.py
│   │   ├── summarizer.py
│   │   ├── books_api.py
│   │   ├── llm_chain.py
│   │   ├── run_chat.py
│   │   ├── schemas.py
│   │   └── search_query.py
│   │
│   ├── summaries/
│   │   ├── 11_summaries.json
│   │   ├── 84_summaries.json
│   │   ├── 1342_summaries.json
│   │   ├── 27400_summaries.json
│   │   └── 51060_summaries.json
│
├── streamlit_frontend.py
├── fetch_books.py
├── dataset_process.py
├── gutenindex_to_weaviate_embedding.py
├── books_metadata.csv
├── processed_books.csv
├── processed_books.zip
├── requirements.txt
├── .env
└── README.md
```

## Installation

### 1. Clone the repository

```
git clone https://github.com/SaskpolyAIDA2025/gutrec.git
cd <project-folder>
```

### 2. Create and activate a virtual environment

```
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

## Environment Setup

### 1. Install Ollama

Download from: https://ollama.com/download

Pull required models:

```
ollama pull gemma3:4b
ollama pull mxbai-embed-large
ollama pull nomic-embed-text
```

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

```
docker compose up -d
```

### 3. Configure Google Books API

Create a  .env file:

```
GOOGLE_BOOKS_API_KEY=your_key_here
```

## Usage

### Step 1 — Fetch raw metadata

```
python fetch_books.py
```

### Step 2 — Preprocess dataset

```
python dataset_process.py
```

### Step 3 — Ingest into Weaviate

```
python gutenindex_to_weaviate_embedding.py
```

### Step 4 — Run the Streamlit UI

```
streamlit run streamlit_frontend.py
```

### Roadmap

- Add RAG‑based summarization for recommendations
- Add user profiles for personalization
- Add multilingual search
- Add book‑to‑book similarity graph

### License

All rights reserved.
This project is not licensed for redistribution or commercial use.