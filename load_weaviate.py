import pandas as pd
import weaviate
from tqdm import tqdm

# Load processed CSV
df = pd.read_csv("processed_books.csv")

# Replace NaN with None
df = df.where(pd.notnull(df), None)

client = weaviate.Client("http://localhost:8080")

for _, row in tqdm(df.iterrows(), total=len(df)):
    # Convert row to dict and remove any NaN
    data = row.to_dict()
    
    # Optional: make sure lists are lists
    for key in ["authors", "translators", "subjects", "bookshelves", "languages", "summaries"]:
        if isinstance(data.get(key), str):
            data[key] = [data[key]]  # wrap single string as list
        elif data.get(key) is None:
            data[key] = []

    client.data_object.create(data, "Book")
