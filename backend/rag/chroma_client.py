"""
backend/rag/chroma_client.py
Krishna's RAG Module — ChromaDB Persistent Client

Singleton ChromaDB client + collection.
Persists to data/knowledge/chroma_db/ so embeddings survive restarts.
"""

import logging
from pathlib import Path

logger = logging.getLogger("rag.chroma_client")

COLLECTION_NAME = "sovereign_kb"

# Persistence path: data/knowledge/chroma_db/
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_PERSIST_DIR = str(_BASE_DIR / "data" / "knowledge" / "chroma_db")

_client = None
_collection = None


def get_client():
    """Returns (or creates) the singleton ChromaDB persistent client."""
    global _client
    if _client is None:
        import chromadb
        Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        logger.info(f"ChromaDB client initialized at: {CHROMA_PERSIST_DIR}")
    return _client


def get_collection():
    """Returns (or creates) the sovereign_kb collection."""
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}   # cosine similarity for semantic search
        )
        logger.info(f"ChromaDB collection '{COLLECTION_NAME}' ready — {_collection.count()} chunks stored")
    return _collection


def get_collection_stats() -> dict:
    """Returns stats about the knowledge base collection."""
    try:
        collection = get_collection()
        count = collection.count()
        return {
            "collection": COLLECTION_NAME,
            "total_chunks": count,
            "persist_path": CHROMA_PERSIST_DIR,
            "status": "ready"
        }
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return {"collection": COLLECTION_NAME, "total_chunks": 0, "status": "error", "error": str(e)}


def reset_collection():
    """Deletes and recreates the collection (for testing only)."""
    global _collection
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    return get_collection()
