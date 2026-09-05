import logging
import httpx
from backend.config import ROUTER_SERVICE_URL, ENABLE_SERVICE_FALLBACKS

logger = logging.getLogger("router_service")

class RouterService:
    @staticmethod
    async def route_task(query: str, uploaded_file: str | None = None) -> dict:
        """
        Interfaces with Aarav's Model Router service.
        Classifies task as reasoning/document, coding, or vision, selects model, and gives reason.
        """
        payload = {
            "query": query,
            "has_image": bool(uploaded_file and uploaded_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))),
            "has_file": bool(uploaded_file)
        }

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.post(f"{ROUTER_SERVICE_URL}/route", json=payload)
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"Failed to connect to Model Router service at {ROUTER_SERVICE_URL}: {e}")

        if ENABLE_SERVICE_FALLBACKS:
            return RouterService._fallback_route(query, uploaded_file)
        
        raise RuntimeError("Model Router service unavailable and fallbacks disabled.")

    @staticmethod
    def _fallback_route(query: str, uploaded_file: str | None) -> dict:
        query_lower = query.lower()
        
        # Vision / P&ID tasks
        if uploaded_file and uploaded_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.pdf')):
            if "p&id" in query_lower or "diagram" in query_lower or "drawing" in query_lower:
                return {
                    "task": "vision_pid",
                    "model": "Qwen2.5-VL",
                    "endpoint": "http://localhost:8003",
                    "reason": "Industrial drawing / P&ID image request detected"
                }
            return {
                "task": "vision",
                "model": "Qwen2.5-VL",
                "endpoint": "http://localhost:8003",
                "reason": "Multimodal visual understanding request detected"
            }

        # Coding / script tasks
        coding_keywords = ["python", "code", "def ", "class ", "fix", "error", "bug", "traceback", "script", "function", "sql", "html"]
        if any(kw in query_lower for kw in coding_keywords):
            return {
                "task": "coding",
                "model": "Qwen2.5-Coder",
                "endpoint": "http://localhost:8002",
                "reason": "Request contains programming code or technical code analysis query"
            }

        # Document / Reasoning tasks
        return {
            "task": "document_reasoning",
            "model": "Sarvam-30B",
            "endpoint": "http://localhost:8001",
            "reason": "Industrial reasoning and SOP document synthesis request"
        }
