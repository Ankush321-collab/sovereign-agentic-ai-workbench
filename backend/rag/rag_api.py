"""
backend/rag/rag_api.py
Krishna's RAG Module — FastAPI Router

Exposes:
  POST /rag/search  — semantic search over knowledge base
  POST /rag/ingest  — add a document to knowledge base
  GET  /rag/status  — collection stats
  POST /rag/seed    — seed with all files from data/knowledge/

Follows the shared API contract from the team README (Section 9).
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.rag.retriever import search
from backend.rag.ingestor import ingest_text, ingest_knowledge_directory
from backend.rag.chroma_client import get_collection_stats

logger = logging.getLogger("rag.api")
router = APIRouter(prefix="/rag", tags=["RAG — Krishna"])

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge"


# ── Request / Response Schemas ────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4


class IngestRequest(BaseModel):
    text: str
    source: str
    page: Optional[int] = 1
    section: Optional[str] = "General"


class SearchResult(BaseModel):
    text: str
    source: str
    page: int
    section: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total_found: int
    query: str


class IngestResponse(BaseModel):
    success: bool
    chunks_added: int
    source: str


class StatusResponse(BaseModel):
    collection: str
    total_chunks: int
    status: str
    persist_path: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def rag_search(request: SearchRequest):
    """
    Semantic search over the local industrial knowledge base.
    Returns top-K relevant document chunks with source citations.

    Per README Section 9 — RAG API Contract.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        results = search(query=request.query.strip(), top_k=request.top_k)
        return SearchResponse(
            results=[SearchResult(**r) for r in results],
            total_found=len(results),
            query=request.query
        )
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/ingest", response_model=IngestResponse)
async def rag_ingest(request: IngestRequest):
    """
    Ingest a text document into the local ChromaDB knowledge base.
    Text is chunked, embedded locally, and stored persistently.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty")

    try:
        result = ingest_text(
            text=request.text,
            source=request.source,
            page=request.page,
            section=request.section
        )
        if not result.get("success"):
            raise HTTPException(status_code=422, detail=result.get("error", "Ingestion failed"))
        return IngestResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG ingest error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/status", response_model=StatusResponse)
async def rag_status():
    """
    Returns stats about the ChromaDB knowledge base collection.
    """
    try:
        stats = get_collection_stats()
        return StatusResponse(**stats)
    except Exception as e:
        logger.error(f"RAG status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed")
async def rag_seed():
    """
    Seeds the knowledge base by ingesting all .txt files from data/knowledge/.
    Safe to call multiple times — only adds new chunks each time.
    """
    try:
        result = ingest_knowledge_directory(KNOWLEDGE_DIR)
        return {
            "success": True,
            "files_ingested": result["files_ingested"],
            "total_chunks": result["total_chunks"],
            "knowledge_dir": str(KNOWLEDGE_DIR)
        }
    except Exception as e:
        logger.error(f"RAG seed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
