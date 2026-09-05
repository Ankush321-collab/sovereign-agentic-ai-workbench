"""
backend/rag/retriever.py
Krishna's RAG Module — Semantic Retriever

Embeds the query, searches ChromaDB, returns top-K chunks
with full citation metadata (source, page, section, score).
"""

import logging
from typing import List, Dict, Any

from backend.rag.embedder import embed_query
from backend.rag.chroma_client import get_collection

logger = logging.getLogger("rag.retriever")

DEFAULT_TOP_K = 4
MIN_SCORE_THRESHOLD = 0.65   # Only return highly relevant grounded chunks (scores >= 0.65)


def search(query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Semantic search over the local ChromaDB knowledge base.

    Args:
        query:  Natural language question / query string
        top_k:  Number of top chunks to return

    Returns:
        List of result dicts, each with:
          - text:     chunk content
          - source:   filename (e.g. "Safety_SOP.txt")
          - page:     page number stored at ingest
          - section:  section label stored at ingest
          - score:    relevance score 0.0–1.0 (higher = more relevant)
    """
    collection = get_collection()

    if collection.count() == 0:
        logger.warning("Knowledge base is empty — no documents ingested yet")
        return []

    # Embed the query locally
    query_embedding = embed_query(query)

    # Query ChromaDB — returns distances (lower = more similar for cosine)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    output = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        # Convert cosine distance (0–2) to similarity score (0–1)
        score = round(max(0.0, 1.0 - (dist / 2.0)), 4)

        if score < MIN_SCORE_THRESHOLD:
            continue  # filter out low-relevance chunks

        output.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "page": meta.get("page", 1),
            "section": meta.get("section", "General"),
            "score": score,
            "chunk_index": meta.get("chunk_index", 0)
        })

    # Sort by score descending
    output.sort(key=lambda x: x["score"], reverse=True)

    logger.info(f"Query '{query[:60]}...' → {len(output)} relevant chunks found")
    return output
