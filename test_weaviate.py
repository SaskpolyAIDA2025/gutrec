import weaviate

client = weaviate.Client(url="http://localhost:8081")

if client.is_ready():
    print("Weaviate ready: True")
else:
    print("Weaviate ready: False")

try:
    result = client.query.get("Book", ["title", "authors"]).with_limit(1).do()
    print(result)
except Exception as e:
    print("No TestItem found or error:", e)