import logging
from pathlib import Path
from backend.config import KNOWLEDGE_DIR, ENABLE_SERVICE_FALLBACKS

logger = logging.getLogger("rag_service")

class RAGService:
    @staticmethod
    async def search_knowledge_base(query: str) -> list[dict]:
        """
        Retrieves top-K semantic chunks from ChromaDB knowledge base in-process.
        Falls back to local file keyword search across knowledge files if needed.
        """
        # 1. Direct in-process ChromaDB vector search (fastest, no network overhead)
        try:
            from backend.rag.retriever import search as chroma_search
            results = chroma_search(query, top_k=4)
            if results:
                return results
        except Exception as ex:
            logger.debug(f"In-process Chroma retrieval skipped/empty ({ex})")

        # 2. Local knowledge files dynamic scanning
        return RAGService._scan_knowledge_files(query)

    @staticmethod
    def _scan_knowledge_files(query: str) -> list[dict]:
        stopwords = {
            "the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "of", "to",
            "for", "with", "by", "from", "who", "what", "where", "when", "how", "why",
            "tell", "me", "about", "this", "that", "these", "those", "are", "was", "were", "please"
        }
        query_words = {w.lower() for w in query.split() if len(w) > 2 and w.lower() not in stopwords}
        if not query_words:
            return []

        results = []
        if KNOWLEDGE_DIR.exists():
            for file_path in sorted(KNOWLEDGE_DIR.glob("*.*")):
                if file_path.is_dir() or file_path.name.startswith("."):
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    content_lower = content.lower()
                    matches = [w for w in query_words if w in content_lower]
                    if matches or any(w in file_path.name.lower() for w in query_words):
                        # Find best snippet
                        snippet = content[:500]
                        if matches:
                            first_idx = content_lower.find(matches[0])
                            if first_idx > 0:
                                start_idx = max(0, first_idx - 100)
                                end_idx = min(len(content), first_idx + 400)
                                snippet = content[start_idx:end_idx].strip()

                        results.append({
                            "text": snippet + ("..." if len(content) > 500 else ""),
                            "source": file_path.name,
                            "page": 1,
                            "section": "Standard Operating Procedure",
                            "score": round(min(0.95, 0.70 + 0.05 * len(matches)), 2)
                        })
                except Exception as ex:
                    logger.error(f"Error reading knowledge file {file_path.name}: {ex}")

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:4]
