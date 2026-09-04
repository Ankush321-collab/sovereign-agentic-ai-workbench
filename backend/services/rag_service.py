import logging
import httpx
from pathlib import Path
from backend.config import KNOWLEDGE_DIR, ENABLE_SERVICE_FALLBACKS

logger = logging.getLogger("rag_service")

# RAG is now integrated directly into the main backend (port 8000)
# No external service needed — calls the /rag/search endpoint on self
RAG_ENDPOINT = "http://localhost:8000/rag/search"

class RAGService:
    @staticmethod
    async def search_knowledge_base(query: str) -> list[dict]:
        """
        Calls Krishna's integrated RAG endpoint (POST /rag/search).
        Returns document chunks with citation metadata (source, page, score).
        Falls back to local file scan if RAG service unavailable.
        """
        payload = {"query": query, "top_k": 4}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(RAG_ENDPOINT, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("results", [])
        except Exception as e:
            logger.warning(f"RAG endpoint unavailable ({e}) — using fallback")

        if ENABLE_SERVICE_FALLBACKS:
            return RAGService._fallback_search(query)
        return []

    @staticmethod
    def _fallback_search(query: str) -> list[dict]:
        stopwords = {
            "the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "of", "to",
            "for", "with", "by", "from", "who", "what", "where", "when", "how", "why",
            "tell", "me", "about", "this", "that", "these", "those", "are", "was", "were"
        }
        query_words = {w for w in query.lower().split() if len(w) > 2 and w not in stopwords}
        if not query_words:
            return []

        results = []

        # Scan text files in knowledge directory
        if KNOWLEDGE_DIR.exists():
            for file_path in KNOWLEDGE_DIR.glob("*.txt"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if any(w in content.lower() for w in query_words):
                        results.append({
                            "text": content[:400] + "...",
                            "source": file_path.name,
                            "page": 1,
                            "section": "Standard Operating Procedure",
                            "score": 0.85
                        })
                except Exception as ex:
                    logger.error(f"Error reading local knowledge file {file_path}: {ex}")

        return results
