"""
tests/test_rag.py
Krishna's RAG Module — Full Test Suite

Tests (in order — must ALL pass before integration):
  1.  Embedder loads locally (no internet required)
  2.  Embedding produces correct vector dimensions
  3.  ChromaDB collection creates successfully
  4.  Ingestor chunks text correctly
  5.  Ingestor preserves metadata (source, page, section)
  6.  Ingestor returns correct chunk count
  7.  Search returns results after ingestion
  8.  Search results contain citation metadata
  9.  Search correctly ranks more relevant results higher
  10. Low-relevance queries return empty or filtered results
  11. FastAPI /rag/status returns 200 with collection stats
  12. FastAPI /rag/ingest ingests a document via API
  13. FastAPI /rag/search returns results via API
  14. FastAPI /rag/search validates empty query (400)
  15. /rag/seed ingests all files from data/knowledge/
"""

import pytest
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

# ─── Test client ─────────────────────────────────────────────────────────────
from backend.main import app
client = TestClient(app)

# ─── Test ChromaDB collection (isolated per test run using unique name) ───────
TEST_COLLECTION = f"test_kb_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module", autouse=True)
def isolated_collection():
    """
    Override ChromaDB collection name for tests to avoid polluting the real KB.
    Uses direct attribute mutation (monkeypatch only works at function scope).
    Cleans up the test collection after all tests in this module finish.
    """
    import backend.rag.chroma_client as cc
    original_name = cc.COLLECTION_NAME
    original_collection = cc._collection

    # Redirect to isolated test collection
    cc.COLLECTION_NAME = TEST_COLLECTION
    cc._collection = None

    yield  # run all tests

    # Teardown: delete test collection and restore
    try:
        c = cc.get_client()
        c.delete_collection(TEST_COLLECTION)
    except Exception:
        pass
    cc.COLLECTION_NAME = original_name
    cc._collection = original_collection


# ═══════════════════════════════════════════════════════════════════
# TEST 1 — Embedder: model loads locally
# ═══════════════════════════════════════════════════════════════════
def test_embedder_loads_locally():
    """Embedding model must load without any internet/cloud dependency."""
    from backend.rag.embedder import _get_model
    model = _get_model()
    assert model is not None, "Embedding model failed to load"


# ═══════════════════════════════════════════════════════════════════
# TEST 2 — Embedder: vector dimensionality
# ═══════════════════════════════════════════════════════════════════
def test_embedder_produces_correct_dimensions():
    """all-MiniLM-L6-v2 produces 384-dimensional vectors."""
    from backend.rag.embedder import embed_texts, embed_query

    texts = ["Valve P-101 requires immediate inspection.", "Corrosion detected."]
    embeddings = embed_texts(texts)

    assert len(embeddings) == 2, "Should return one embedding per text"
    assert len(embeddings[0]) == 384, "all-MiniLM-L6-v2 produces 384-dim vectors"

    query_emb = embed_query("safety inspection procedure")
    assert len(query_emb) == 384, "Query embedding must also be 384-dim"


# ═══════════════════════════════════════════════════════════════════
# TEST 3 — ChromaDB: collection creates successfully
# ═══════════════════════════════════════════════════════════════════
def test_chroma_collection_creates():
    """ChromaDB persistent collection must be created or retrieved successfully."""
    from backend.rag.chroma_client import get_collection
    collection = get_collection()
    assert collection is not None
    assert collection.name == TEST_COLLECTION


# ═══════════════════════════════════════════════════════════════════
# TEST 4 — Ingestor: text chunking
# ═══════════════════════════════════════════════════════════════════
def test_ingestor_chunks_text():
    """Long text should be split into multiple chunks."""
    from backend.rag.ingestor import _chunk_text

    # 1200 chars → should produce at least 2 chunks with CHUNK_SIZE=400
    long_text = "A" * 1200
    chunks = _chunk_text(long_text, chunk_size=400, overlap=80)
    assert len(chunks) >= 2, f"Expected ≥2 chunks, got {len(chunks)}"

    # Short text → single chunk
    short_text = "Short safety note."
    chunks_short = _chunk_text(short_text)
    assert len(chunks_short) == 1


# ═══════════════════════════════════════════════════════════════════
# TEST 5 & 6 — Ingestor: metadata preservation and chunk count
# ═══════════════════════════════════════════════════════════════════
def test_ingestor_preserves_metadata_and_returns_chunk_count():
    """Ingestor must store source, page, section in ChromaDB metadata."""
    from backend.rag.ingestor import ingest_text
    from backend.rag.chroma_client import get_collection

    sample_text = (
        "Emergency Procedure EP-04: Valve Isolation. "
        "Step 1: Close upstream block valve BV-101A. "
        "Step 2: Verify zero pressure on PI-101. "
        "Step 3: Apply lockout-tagout (LOTO) on all isolation points. "
        "Step 4: Log isolation in the Maintenance Management System with timestamp. "
        "Step 5: Schedule valve replacement within 48 hours for corrosion-related isolations. "
        "All isolation activities must be authorized by the Process Control Room (PCR) before proceeding."
    )

    result = ingest_text(
        text=sample_text,
        source="Test_EP04.txt",
        page=12,
        section="Emergency Isolation Procedure"
    )

    assert result["success"] is True, f"Ingest failed: {result}"
    assert result["chunks_added"] >= 1, "Must add at least 1 chunk"
    assert result["source"] == "Test_EP04.txt"

    # Verify metadata stored in ChromaDB
    collection = get_collection()
    stored = collection.get(where={"source": "Test_EP04.txt"}, include=["metadatas"])
    assert len(stored["metadatas"]) >= 1, "Metadata not found in ChromaDB"

    meta = stored["metadatas"][0]
    assert meta["source"] == "Test_EP04.txt"
    assert meta["page"] == 12
    assert meta["section"] == "Emergency Isolation Procedure"


# ═══════════════════════════════════════════════════════════════════
# TEST 7 — Retriever: search returns results after ingestion
# ═══════════════════════════════════════════════════════════════════
def test_retriever_returns_results():
    """After ingesting a document, semantic search must return results."""
    from backend.rag.ingestor import ingest_text
    from backend.rag.retriever import search

    # Ingest some domain content first
    ingest_text(
        text=(
            "Corrosion on Valve P-101 requires immediate attention. "
            "Per Emergency Procedure EP-04, isolate the valve and schedule "
            "replacement within 48 hours. Ultrasonic thickness reading was 4.2mm, "
            "below the minimum acceptable value of 4.5mm for Class 300 valves."
        ),
        source="Inspection_Report_P101.txt",
        page=3,
        section="Findings and Recommendations"
    )

    results = search("valve P-101 corrosion inspection", top_k=3)
    assert len(results) >= 1, "Search returned no results — retriever not working"


# ═══════════════════════════════════════════════════════════════════
# TEST 8 — Retriever: results contain citation metadata
# ═══════════════════════════════════════════════════════════════════
def test_retriever_results_have_citations():
    """Every search result must include source, page, section, and score."""
    from backend.rag.retriever import search

    results = search("isolate valve emergency procedure", top_k=4)
    assert len(results) >= 1, "No results found"

    for r in results:
        assert "text" in r and r["text"], "Result missing text"
        assert "source" in r and r["source"], "Result missing source"
        assert "page" in r, "Result missing page"
        assert "section" in r, "Result missing section"
        assert "score" in r, "Result missing score"
        assert 0.0 <= r["score"] <= 1.0, f"Invalid score: {r['score']}"


# ═══════════════════════════════════════════════════════════════════
# TEST 9 — Retriever: ranking — more relevant results rank higher
# ═══════════════════════════════════════════════════════════════════
def test_retriever_ranking_is_correct():
    """Results must be sorted by descending score (most relevant first)."""
    from backend.rag.retriever import search

    results = search("emergency valve isolation procedure", top_k=4)
    if len(results) >= 2:
        for i in range(len(results) - 1):
            assert results[i]["score"] >= results[i + 1]["score"], \
                f"Results not sorted: score[{i}]={results[i]['score']} < score[{i+1}]={results[i+1]['score']}"


# ═══════════════════════════════════════════════════════════════════
# TEST 10 — Retriever: irrelevant query returns empty or low-scored
# ═══════════════════════════════════════════════════════════════════
def test_retriever_filters_irrelevant_query():
    """Completely unrelated query should return empty or very-low-score results."""
    from backend.rag.retriever import search

    results = search("quantum physics neutron star black hole galaxy", top_k=3)
    # Either no results, or all scores should be low (< 0.55)
    for r in results:
        assert r["score"] < 0.55, \
            f"Irrelevant query returned high-confidence result: {r['score']:.3f} — '{r['text'][:60]}'"


# ═══════════════════════════════════════════════════════════════════
# TEST 11 — FastAPI: GET /rag/status returns 200 with stats
# ═══════════════════════════════════════════════════════════════════
def test_api_rag_status():
    """GET /rag/status must return 200 with collection name and chunk count."""
    response = client.get("/rag/status")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "collection" in data
    assert "total_chunks" in data
    assert isinstance(data["total_chunks"], int)
    assert data["total_chunks"] >= 0


# ═══════════════════════════════════════════════════════════════════
# TEST 12 — FastAPI: POST /rag/ingest indexes a document
# ═══════════════════════════════════════════════════════════════════
def test_api_rag_ingest():
    """POST /rag/ingest must chunk and store the document, returning chunk count."""
    payload = {
        "text": (
            "Safety Standard Operating Procedure — Valve Isolation. "
            "When corrosion is detected on valve P-101, immediately notify the Process Control Room. "
            "Follow Emergency Procedure EP-04: close upstream block valve BV-101A, "
            "verify zero pressure, apply LOTO locks, and raise a maintenance work order. "
            "Replacement must be scheduled within 48 hours of isolation."
        ),
        "source": "API_Test_SOP.txt",
        "page": 7,
        "section": "Valve Isolation Protocol"
    }
    response = client.post("/rag/ingest", json=payload)
    assert response.status_code == 200, f"Ingest failed: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["chunks_added"] >= 1
    assert data["source"] == "API_Test_SOP.txt"


# ═══════════════════════════════════════════════════════════════════
# TEST 13 — FastAPI: POST /rag/search returns results
# ═══════════════════════════════════════════════════════════════════
def test_api_rag_search():
    """POST /rag/search must return relevant results from the knowledge base."""
    payload = {"query": "valve corrosion emergency isolation procedure", "top_k": 3}
    response = client.post("/rag/search", json=payload)
    assert response.status_code == 200, f"Search failed: {response.text}"
    data = response.json()
    assert "results" in data
    assert "total_found" in data
    assert isinstance(data["results"], list)
    assert data["total_found"] >= 1, "Expected at least 1 result"

    # Verify citation fields present in first result
    first = data["results"][0]
    assert "text" in first and first["text"]
    assert "source" in first
    assert "page" in first
    assert "score" in first


# ═══════════════════════════════════════════════════════════════════
# TEST 14 — FastAPI: empty query returns 400
# ═══════════════════════════════════════════════════════════════════
def test_api_rag_search_empty_query_rejected():
    """POST /rag/search with empty query must return HTTP 400."""
    response = client.post("/rag/search", json={"query": "   "})
    assert response.status_code == 400, \
        f"Expected 400 for empty query, got {response.status_code}"


# ═══════════════════════════════════════════════════════════════════
# TEST 15 — FastAPI: POST /rag/seed indexes all knowledge files
# ═══════════════════════════════════════════════════════════════════
def test_api_rag_seed():
    """POST /rag/seed must ingest all .txt files from data/knowledge/."""
    knowledge_dir = Path("data/knowledge")
    txt_files = list(knowledge_dir.glob("*.txt"))
    assert len(txt_files) >= 1, "No .txt files found in data/knowledge/"

    response = client.post("/rag/seed")
    assert response.status_code == 200, f"Seed failed: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["files_ingested"] >= 1
    assert data["total_chunks"] >= 1
