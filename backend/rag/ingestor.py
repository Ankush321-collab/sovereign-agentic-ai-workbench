"""
backend/rag/ingestor.py
Krishna's RAG Module — Document Ingestion Pipeline

Pipeline:
  Text/file → Clean → Chunk (with overlap) → Embed → ChromaDB

Each chunk stores metadata: source, page, section, chunk_index.
"""

import logging
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any

from backend.rag.embedder import embed_texts
from backend.rag.chroma_client import get_collection

logger = logging.getLogger("rag.ingestor")

# Chunking config (per README: meaningful chunk size for industrial SOPs)
CHUNK_SIZE = 400      # characters per chunk
CHUNK_OVERLAP = 80    # overlap to preserve context across boundaries


def _clean_text(text: str) -> str:
    """Remove excessive whitespace, normalize line breaks."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Splits text into overlapping character chunks.
    Tries to break at sentence/paragraph boundaries when possible.
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to find a clean sentence break near the end
        if end < text_len:
            for sep in ["\n\n", "\n", ". ", "! ", "? "]:
                idx = text.rfind(sep, start + chunk_size // 2, end)
                if idx != -1:
                    end = idx + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if (end - overlap) > start else end

    return chunks


def ingest_text(
    text: str,
    source: str,
    page: int = 1,
    section: str = "General"
) -> Dict[str, Any]:
    """
    Ingests a raw text string into ChromaDB.
    Chunks the text, embeds each chunk, stores with full metadata.

    Returns: {"success": True, "chunks_added": N, "source": source}
    """
    collection = get_collection()
    cleaned = _clean_text(text)
    chunks = _chunk_text(cleaned)

    if not chunks:
        return {"success": False, "chunks_added": 0, "source": source, "error": "No content after cleaning"}

    # Embed all chunks at once (batch)
    embeddings = embed_texts(chunks)

    ids = []
    metadatas = []
    documents = []

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        doc_id = str(uuid.uuid4())
        ids.append(doc_id)
        documents.append(chunk)
        metadatas.append({
            "source": source,
            "page": page,
            "section": section,
            "chunk_index": i,
            "total_chunks": len(chunks)
        })

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    logger.info(f"Ingested '{source}' → {len(chunks)} chunks added to ChromaDB")
    return {"success": True, "chunks_added": len(chunks), "source": source}


def ingest_file(file_path: str, section: str = "General") -> Dict[str, Any]:
    """
    Reads a .txt file from disk and ingests it.
    Uses filename as source, reads page from filename if available.
    """
    path = Path(file_path)
    if not path.exists():
        return {"success": False, "chunks_added": 0, "source": str(file_path), "error": "File not found"}

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"success": False, "chunks_added": 0, "source": path.name, "error": str(e)}

    return ingest_text(text=text, source=path.name, page=1, section=section)


def ingest_knowledge_directory(knowledge_dir: Path) -> Dict[str, Any]:
    """
    Bulk-ingests all .txt files in the knowledge directory.
    Returns summary of all ingestion results.
    """
    results = []
    total_chunks = 0
    files_ingested = 0

    for txt_file in sorted(knowledge_dir.glob("*.txt")):
        result = ingest_file(str(txt_file), section=txt_file.stem.replace("_", " ").title())
        results.append(result)
        if result.get("success"):
            total_chunks += result.get("chunks_added", 0)
            files_ingested += 1

    logger.info(f"Bulk ingestion complete: {files_ingested} files, {total_chunks} total chunks")
    return {
        "files_ingested": files_ingested,
        "total_chunks": total_chunks,
        "results": results
    }
