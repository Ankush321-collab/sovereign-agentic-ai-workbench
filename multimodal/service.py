import logging
from pathlib import Path
from typing import Dict, Any, Optional

from multimodal.schemas import ExtractionResult
from multimodal.file_loader import FileLoader
from multimodal.document_pipeline import DocumentPipeline
from multimodal.inspection_analyzer import InspectionAnalyzer
from multimodal.pid_extractor import PIDExtractor

logger = logging.getLogger("multimodal.service")


class MultimodalEngine:
    """Unified engine coordinating document OCR, visual defect inspection, and P&ID extraction."""

    def __init__(self):
        self.document_pipeline = DocumentPipeline()
        self.inspection_analyzer = InspectionAnalyzer()
        self.pid_extractor = PIDExtractor()

    async def process_file(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        """Analyze a file and route to the specialized sub-pipeline based on content & intent."""
        options = options or {}
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        name_lower = path.name.lower()
        forced_type = options.get("type", "").lower()

        # 1. P&ID Schematic extraction route
        if forced_type == "pid" or any(k in name_lower for k in ["pid", "p&id", "schematic", "drawing", "diagram"]):
            logger.info(f"Routing {path.name} to PIDExtractor.")
            return await self.pid_extractor.extract(str(path))

        # 2. Visual inspection photo route
        if forced_type == "inspection" or any(k in name_lower for k in ["flange", "corrosion", "defect", "crack", "photo", "leak"]):
            logger.info(f"Routing {path.name} to InspectionAnalyzer.")
            return await self.inspection_analyzer.analyze(str(path), context=options.get("context"))

        # 3. Default Document / Scanned Report Pipeline (MarkItDown + OCR)
        logger.info(f"Routing {path.name} to DocumentPipeline.")
        return self.document_pipeline.process(str(path))
