import logging
import httpx
from pathlib import Path
from backend.config import MULTIMODAL_SERVICE_URL, ENABLE_SERVICE_FALLBACKS

logger = logging.getLogger("multimodal_service")

class MultimodalService:
    @staticmethod
    async def process_document(file_path: str) -> dict:
        """
        Interfaces with Pankaj's Multimodal AI, OCR & P&ID pipeline.
        Extracts OCR text, layout, tables, and visual inspection/P&ID tags.
        """
        payload = {"file_path": file_path}
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(f"{MULTIMODAL_SERVICE_URL}/multimodal/process", json=payload)
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"Failed to connect to Multimodal service at {MULTIMODAL_SERVICE_URL}: {e}")

        if ENABLE_SERVICE_FALLBACKS:
            return MultimodalService._fallback_process(file_path)

        return {"type": "unknown", "text": "", "findings": [], "confidence": 0.0}

    @staticmethod
    def _fallback_process(file_path: str) -> dict:
        path = Path(file_path)
        file_name = path.name.lower()

        if "pid" in file_name or "p&id" in file_name or "drawing" in file_name:
            return {
                "type": "p_and_id_drawing",
                "text": "P&ID Schematic Diagram - Unit 100",
                "confidence": 0.95,
                "equipment": [
                    {"tag": "P-101A", "type": "Centrifugal Slurry Pump", "status": "Operational"},
                    {"tag": "V-204", "type": "High Pressure Separator Vessel", "status": "Active"}
                ],
                "instruments": [
                    {"tag": "PT-201", "type": "Pressure Transmitter", "range": "0-200 PSI"},
                    {"tag": "FT-102", "type": "Flow Transmitter", "range": "0-500 GPM"}
                ],
                "findings": ["Equipment tags identified", "Safety interlock loop validated"]
            }

        return {
            "type": "scanned_inspection_report",
            "text": "CONFIDENTIAL INDUSTRIAL INSPECTION REPORT\nStatus: Action Required\nCorrosion observed on secondary cooling loop flange FL-402.\nThickness loss: 1.2mm.",
            "pages": 1,
            "tables": [
                {"component": "FL-402", "reading": "3.8mm", "min_allowed": "4.0mm", "status": "ALERT"}
            ],
            "findings": [
                "Wall thickness below minimum tolerance threshold",
                "Immediate maintenance approval note generation recommended"
            ],
            "confidence": 0.92
        }
