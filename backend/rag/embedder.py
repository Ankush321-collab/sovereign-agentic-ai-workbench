"""
backend/rag/embedder.py
Krishna's RAG Module — Local Embedding Engine

Uses sentence-transformers (all-MiniLM-L6-v2) for 100% local embeddings.
No cloud API. No internet. Air-gapped compatible.
"""

import logging
from typing import List

logger = logging.getLogger("rag.embedder")

_model = None  # lazy-loaded singleton


def _get_model():
    """Lazy-loads the embedding model once and reuses it."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading local embedding model: all-MiniLM-L6-v2 (offline)")
            try:
                _model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            except Exception:
                _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embeds a list of text strings into dense float vectors.
    Returns a list of embeddings (one per text).
    """
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """
    Embeds a single query string for retrieval.
    """
    model = _get_model()
    embedding = model.encode([query], show_progress_bar=False, convert_to_numpy=True)
    return embedding[0].tolist()
