import csv
from collections import defaultdict
from tqdm import tqdm
import time
import ast

from src.books_api import get_book_metadata
from src.search_query import semantic_search, close_weaviate

CSV_PATH = "Book_list.csv"


def parse_subjects(subjects_raw):
    if not subjects_raw:
        return []
    if isinstance(subjects_raw, list):
        return subjects_raw
    try:
        return ast.literal_eval(subjects_raw)
    except:
        return [subjects_raw]
    

def load_books(csv_path=CSV_PATH):
    books = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for genre, title, author in reader:
            books.append({
                "genre": genre.strip(),
                "title": title.strip(),
                "author": author.strip()
            })
    return books

books = load_books()
print(f"Loaded {len(books)} books.")
# print(sorted({b["genre"] for b in books}))


import re

GENRE_MAP = {
    "Literary Fiction": ["fiction", "literature"],
    "Science Fiction & Fantasy": ["science fiction", "fantasy", "speculative", "dragons", "dystopias", "androids", "science fiction; short stories", "extraterrestrial beings", "science fiction; utopias", "fiction; fantasy fiction; magic", "fiction; fantasy fiction, american", "speculative fiction; young men"],
    "Mystery/Thriller": ["mystery", "detective", "thriller", "crime", "detective and mystery stories; murder", "investigation", "fiction; private investigators", "20th century; detective and mystery stories, american", "fiction; suspense fiction", "fiction; horror tales; human experimentation in medicine", "juvenile fiction; mystery and detective stories; Teenage girls", "juvenile fiction; women detectives", "mystery fiction", "fiction; private investigators"],
    "Romance": ["romance", "love", "first loves", "fiction; love stories", "fiction; love stories; married people", "fiction; romance fiction", "fiction; man-woman relationships", "rriangles (interpersonal relations)", "courtship", "man-woman relationships", "fiction; love stories; musicians", "fiction; love stories; young women"],
    "Young Adult": ["young adult", "teen", "juvenile fiction", "juvenile fiction; youth", "juvenile fiction; family", "juvenile fiction; women detectives", "juvenile literature"],
    "Children's Literature": ["children", "juvenile", "children's literature", "juvenile literature", "juvenile fiction", "animals"],
    "Reference": ["reference", "manual", "guide", "handbooks, manuals, etc.", "english language", "art", "reporters and reporting", "dictionaries", "miscellanea", "encyclopedias and dictionaries", "military art and science"],
    "Travel": ["travel", "adventure", "social life and customs", "description and travel", "voyages around the world", "adventure and adventurers; voyages and travels"]
}

def map_subject_to_genre(subjects):
    subjects_text = " ".join(s.lower() for s in subjects)
    # print(subjects_text)

    matches = []
    for genre, keywords in GENRE_MAP.items():
        if any(kw in subjects_text for kw in keywords):
            matches.append(genre)

    return matches  # may be empty or multiple


def evaluate_top_k(books, k=5):
    results = []

    for book in tqdm(books, desc="Evaluating"):
        title = book["title"]
        author = book["author"]
        true_genre = book["genre"]

        print("Checking genre:", true_genre)

        # 1. Fetch metadata (summary)
        metadata = get_book_metadata(title, author)
        if not metadata or not metadata.get("description"):
            continue

        summary = metadata["description"]

        # 2. Run semantic search using the summary
        retrieved = semantic_search(summary[:2000], k=k)

        # 3. Map retrieved subjects to genres
        retrieved_genres = []
        for hit in retrieved:
            subjects = parse_subjects(hit.get("subjects")) or []
            print(subjects)
            mapped = map_subject_to_genre(subjects)
            retrieved_genres.append(mapped) # list of genres
        print(retrieved_genres)

        # 4. Compute metrics for this book
        correct_hits = sum(1 for g in retrieved_genres if true_genre in g)

        # Top-K Accuracy
        top_k_acc = 1 if correct_hits > 0 else 0

        # Precision@K
        precision = correct_hits / k

        # Recall@K (10 books per genre)
        recall = correct_hits / 10

        # MRR
        mrr = 0
        for rank, g in enumerate(retrieved_genres, start=1):
            if true_genre in g:
                mrr = 1 / rank
                break

        results.append({
            "title": title,
            "genre": true_genre,
            "precision": precision,
            "recall": recall,
            "top_k_acc": top_k_acc,
            "mrr": mrr
        })

    return results


def aggregate_metrics(results):
    n = len(results)
    avg_precision = sum(r["precision"] for r in results) / n
    avg_recall = sum(r["recall"] for r in results) / n
    avg_top_k_acc = sum(r["top_k_acc"] for r in results) / n
    avg_mrr = sum(r["mrr"] for r in results) / n

    return {
        "avg_precision@5": avg_precision,
        "avg_recall@5": avg_recall,
        "avg_top5_accuracy": avg_top_k_acc,
        "avg_mrr": avg_mrr
    }


results = evaluate_top_k(books, k=5)
metrics = aggregate_metrics(results)

print("\n=== Top-K Retrieval Quality ===")
for k, v in metrics.items():
    print(f"{k}: {v:.4f}")

close_weaviate()
