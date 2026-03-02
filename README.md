# Project Gutenberg Discovery & Recommendation Platform

*A modern AI‑powered system designed to enhance how readers explore Project Gutenberg’s vast public‑domain library. By combining semantic search, intelligent recommendations, and user‑centric discovery tools, the platform transforms classic literature browsing into a richer, more intuitive experience.*

Capstone Project for AIDA 2025: Angie, Eladio and KNK
---

## Overview
This platform provides an end‑to‑end pipeline for transforming raw Project Gutenberg metadata into a fully searchable, vector‑powered discovery system. It integrates:

- Data fetching from the Gutendex API  
- Metadata preprocessing 
- Local embedding generation using Ollama
- Vector storage and semantic search using Weaviate
- Structured LLM extraction for book identification
- Google Books metadata enrichment
- A conversational interface for natural book queries

The system is designed to run entirely on local infrastructure, ensuring privacy, reproducibility, and full control over the data and models.

---

## Features
- Fetch raw metadata from the **Gutendex API**  
- Clean and normalize metadata (languages, subjects, bookshelves) 
- Generate high‑quality embeddings using **mxbai‑embed‑large** (Ollama)  
- Store vectorized book objects in **Weaviate**  
- Perform semantic search using near‑vector queries  
- Extract book titles/authors from natural language using **Gemma 3 (4B)**  
- Enrich results with Google Books metadata  
- Provide a conversational interface for iterative book identification  

---

## Data Flow Diagram
            ┌──────────────────────────┐
            │   fetch_books.py          │
            │   (Gutendex API → CSV)    │
            └──────────────┬───────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │  dataset_process.py       │
            │  - clean languages        │
            │  - normalize subjects     │
            │  - output processed CSV   │
            └──────────────┬───────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │ gutenindex_to_weaviate   │
            │ - define schema          │
            │ - embed with Ollama      │
            │ - ingest into Weaviate   │
            └──────────────┬───────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │      Weaviate DB         │
            │  (vector search engine)  │
            └──────────────┬───────────┘
                           │
                           ▼
    ┌────────────────────────────────────────────────┐
    │ run_chat.py                                     │
    │ - extract title/author (Gemma 3)                │
    │ - fetch metadata (Google Books API)             │
    │ - semantic search (search_query.py)             │
    └────────────────────────────────────────────────┘

---

## Architecture

### Components
- **Data fetching**: `fetch_books.py`
- **Preprocessing**: `dataset_process.py`  
- **Embedding + ingestion**: `gutenindex_to_weaviate_embedding.py`  
- **Semantic search**: `search_query.py`  
- **LLM chains**: `llm_chain.py`  
- **Metadata enrichment**: `books_api.py`  
- **Chat interface**: `run_chat.py`  
- **Pydantic schema**: `schemas.py`

### Technologies
- Python 3.10+  
- Weaviate (local Docker)  
- Ollama (Gemma 3 + mxbai‑embed‑large)  
- LangChain  
- Google Books API  
- Pandas  

---

## Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <project-folder>

### 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows

### 3. Install dependencies
pip install -r requirements.
---

## Environment Setup

### 1. Install Ollama
Download from: https://ollama.com/download
Pull required models:

ollama pull gemma3:4b
ollama pull mxbai-embed-large

### 2. Start Weaviate (Docker)
Example docker-compose.yml:
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: './data'

Run:
docker compose up -d

### 3. Configure Google Books API
Create a .env file:
GOOGLE_BOOKS_API_KEY=your_key_here

## Usage

### Step 1 - Fetch raw metadata from Gutendex
python fetch_books.py --pages 50

Outputs: books_metadata.csv
(Use --pages to limit API calls; omit to fetch all pages.)

### Step 2 - Preprocess the dataset
python dataset_process.py

Outputs: processed_books.csv

### Step 3 - Ingest into Weaviate
python gutenindex_to_weaviate_embedding.py

### Step 4 - Run the chatbot
python run_chat.py

Example interaction:
Chatbot: Tell me the title of your reference book and, if possible, its author.
You: I'm looking for the book about time thieves by Michael Ende.
Chatbot: Searching Google Books for 'Momo'...
...

## Project Structure

project/
│
├── src/
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

## Roadmap
- Add RAG‑based summarization
- Add user profiles for personalized recommendations
- Add web UI (FastAPI + React)
- Add multilingual search
- Add book‑to‑book similarity graph

License
All rights reserved.
This project is not licensed for redistribution or commercial use.