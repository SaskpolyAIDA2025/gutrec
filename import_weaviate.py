import weaviate
import numpy as np
import pandas as pd

client = weaviate.Client("http://localhost:8081")

books = pd.read_csv("processed_books.csv")
for idx, row in books.iterrows():
    vector = np.load(f'vectors/{row["id_pg"]}.npy')  # example path
    client.data_object.create(
        data_object=row.to_dict(),
        class_name="Book",
        vector=vector
    )