import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_FILE = "vector.index"
METADATA_FILE = "vector_metadata.json"

model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

index = faiss.read_index(INDEX_FILE)

with open(METADATA_FILE) as f:
    metadata = json.load(f)


def search_ids(query, top_k=10, filters=None):

    query_embedding = model.encode([query]).astype("float32")
    faiss.normalize_L2(query_embedding)

    distances, indices = index.search(query_embedding, top_k)

    results = []

    for i, idx in enumerate(indices[0]):
        item = metadata[idx]

        # 🔹 Apply filters BEFORE returning ID
        if filters:
            skip = False
            for key, value in filters.items():
                if value and item["metadata"].get(key) != value:
                    skip = True
                    break
            if skip:
                continue

        results.append({
            "id": item["id"],
            "score": float(distances[0][i])
        })

    return results
