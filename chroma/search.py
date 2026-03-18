from chroma.client import collection
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


def search(query, filters=None, top_k=10):

    embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=embedding,
        n_results=top_k,
        where=filters  # 🔥 BUILT-IN FILTERING
    )

    return results
