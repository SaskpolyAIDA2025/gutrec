import pandas as pd
import requests
import ast
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import weaviate
from weaviate.connect import ConnectionParams
from weaviate.classes.config import Property, DataType

# =========================================================
# Configuration
# =========================================================

CSV_PATH = "processed_books.csv"
WEAVIATE_URL = "http://localhost:8080"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "mxbai-embed-large"

MAX_WORKERS = 8          # Parallel embedding requests
BATCH_SIZE = 100         # Weaviate batch size
CLASS_NAME = "Book"

# =========================================================
# Weaviate v4 Connection
# =========================================================

client = weaviate.WeaviateClient(
    connection_params=ConnectionParams.from_url(
        WEAVIATE_URL,
        grpc_port=50051,  # default local gRPC port
    )
)

client.connect()
print("Connected to Weaviate v4")

# =========================================================
# Collection (Schema) Setup
# =========================================================

existing = client.collections.list_all()

if CLASS_NAME not in existing:
    client.collections.create(
        name=CLASS_NAME,
        vectorizer_config=None,  # we provide our own vectors
        properties=[
            Property(name="id_pg", data_type=DataType.TEXT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="authors", data_type=DataType.TEXT),
            Property(name="translators", data_type=DataType.TEXT),
            Property(name="subjects", data_type=DataType.TEXT),
            Property(name="bookshelves", data_type=DataType.TEXT),
            Property(name="languages", data_type=DataType.TEXT_ARRAY),  # filterable
            Property(name="copyright", data_type=DataType.TEXT),
            Property(name="download_count", data_type=DataType.INT),
            Property(name="summaries", data_type=DataType.TEXT),
        ],
    )
    print("Book collection created")
else:
    print("Book collection already exists")

books = client.collections.get(CLASS_NAME)

# =========================================================
# Utility Functions
# =========================================================

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.replace("\x00", "")
    text = re.sub(r"[\r\n\t]+", " ", text)
    return text.strip()

def safe_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)

# =========================================================
# Ollama Embedding
# =========================================================

def embed_text(text: str) -> list:
    response = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["embedding"]

# =========================================================
# Prepare a Single Book (Embedding + Object)
# =========================================================

def prepare_book(row):
    try:
        languages = ast.literal_eval(row.languages)
    except Exception:
        languages = []

    try:
        bookshelves = ast.literal_eval(row.bookshelves)
    except Exception:
        bookshelves = []

    try:
        subjects = ast.literal_eval(row.subjects)
    except Exception:
        subjects = []

    properties = {
        "id_pg": safe_str(row.id),
        "title": safe_str(row.title),
        "authors": safe_str(row.authors),
        "translators": safe_str(row.translators),
        "subjects": safe_str(row.subjects),
        "bookshelves": safe_str(row.bookshelves),
        "languages": languages,  # REAL ARRAY
        "copyright": safe_str(row.copyright),
        "download_count": int(row.download_count),
        "summaries": safe_str(row.summaries),
    }

    embedding_text = clean_text(
        f"Title: {row.title}. "
        f"Author: {row.authors}. "
        f"Languages: {' '.join(languages)}. "
        f"Bookshelves: {' '.join(bookshelves)}. "
        f"Subjects: {' '.join(subjects)}. "
        f"Summary: {row.summaries}"
    )

    vector = embed_text(embedding_text)
    return properties, vector

# =========================================================
# Main Ingestion Logic
# =========================================================

def ingest_books(csv_path: str):
    df = pd.read_csv(csv_path)
    total = len(df)

    print(f"Ingesting {total} books...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(prepare_book, row)
            for row in df.itertuples(index=False)
        ]

        with books.batch.dynamic() as batch:
            for i, future in enumerate(as_completed(futures), start=1):
                try:
                    properties, vector = future.result()

                    batch.add_object(
                        properties=properties,
                        vector=vector,
                    )

                    if i % 100 == 0 or i == total:
                        print(f"{i}/{total} books ingested")

                except Exception as e:
                    print(f"Failed to ingest row {i}: {e}")

    print("Ingestion completed successfully!")

# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":
    # ingest_books("processed_books.csv")

    try:
        ingest_books("processed_books.csv")
    finally:
        client.close()
        print("Weaviate connection closed")
