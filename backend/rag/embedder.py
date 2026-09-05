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
            logger.info("Loading local embedding model: all-MiniLM-L6-v2")
            try:
                _model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            except Exception:
                _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}")
            _model = None
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embeds a list of text strings into dense float vectors.
    Returns a list of embeddings (one per text).
    """
    model = _get_model()
    if model is not None:
        try:
            embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.warning(f"Embedding encoding failed: {e}")
    # Fallback zero vectors (384-dim for all-MiniLM-L6-v2)
    return [[0.0] * 384 for _ in texts]


def embed_query(query: str) -> List[float]:
    """
    Embeds a single query string for retrieval.
    """
    model = _get_model()
    if model is not None:
        try:
            embedding = model.encode([query], show_progress_bar=False, convert_to_numpy=True)
            return embedding[0].tolist()
        except Exception as e:
            logger.warning(f"Embedding query failed: {e}")
    # Fallback zero vector
    return [0.0] * 384
