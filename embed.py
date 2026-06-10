"""
Milestone 4: Embed chunks with all-MiniLM-L6-v2, store in ChromaDB, and retrieve.

Run directly to (re)build the vector store and test retrieval:
    python embed.py
"""
import chromadb
from sentence_transformers import SentenceTransformer

from ingest import load_all_chunks

MODEL_NAME = "all-MiniLM-L6-v2"
DB_PATH = "./chroma_db"
COLLECTION_NAME = "unofficial_guide"

# Load the embedding model once (downloads on first run, then cached locally).
_model = SentenceTransformer(MODEL_NAME)

# Persistent on-disk Chroma client so we don't re-embed on every query.
_client = chromadb.PersistentClient(path=DB_PATH)


def build_store():
    """Load + chunk all docs, embed them, and (re)populate the Chroma collection."""
    chunks = load_all_chunks()

    # Start fresh each build so re-running doesn't create duplicates.
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    # Use cosine distance (MiniLM embeddings are meant for cosine, not L2).
    collection = _client.create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    texts = [c["text"] for c in chunks]
    embeddings = _model.encode(texts, show_progress_bar=False).tolist()

    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {"source": c["source"], "position": i, "length": c["length"]}
            for i, c in enumerate(chunks)
        ],
    )

    print(f"Embedded and stored {len(chunks)} chunks in '{COLLECTION_NAME}'.")
    return collection


def get_collection():
    """Return the existing collection, building it if it doesn't exist yet."""
    try:
        return _client.get_collection(COLLECTION_NAME)
    except Exception:
        return build_store()


def retrieve(query, k=4):
    """Return the top-k chunks for a query as a list of dicts with source + distance."""
    collection = get_collection()
    q_emb = _model.encode([query]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=k)

    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append({"text": doc, "source": meta["source"], "distance": dist})
    return results


if __name__ == "__main__":
    build_store()

    test_queries = [
        "What do students say about Dell Jensen's organic chemistry lectures?",
        "Is Paul Croll's class hard, and what's his reputation?",
        "What are the main complaints about Ruby Auf's epidemiology class?",
    ]

    for q in test_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {q}")
        print("=" * 70)
        for rank, r in enumerate(retrieve(q, k=4), 1):
            print(f"\n[{rank}] source={r['source']}  distance={r['distance']:.3f}")
            snippet = r["text"][:240].replace("\n", " ")
            print(f"    {snippet}...")
