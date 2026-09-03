import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from multimodal.schemas import ExtractionResult, InspectionFinding
from multimodal.vision_client import LocalVisionClient
from multimodal.file_loader import FileLoader

logger = logging.getLogger("multimodal.inspection_analyzer")

INSPECTION_SYSTEM_PROMPT = """You are a senior industrial inspection engineer analyzing on-site photographs and defect evidence.
Analyze the provided image and extract:
1. Equipment component or tag identifier (if visible or identifiable)
2. Defect classification (e.g. galvanic corrosion, cavitation, wall thinning, seal blowout, fatigue crack)
3. Severity level: "NORMAL", "INFO", "WARNING", "ALERT", "CRITICAL"
4. Detailed engineering findings (bullet points)
5. Maintenance or remediation recommendation

Return ONLY a valid JSON object matching this schema:
{
  "component": "string",
  "defect_type": "string",
  "severity": "ALERT",
  "findings": ["finding 1", "finding 2"],
  "recommendation": "string",
  "confidence": 0.95
}
"""


class InspectionAnalyzer:
    """Specialized analyzer for visual defect, corrosion, and photographic inspection evidence."""

    def __init__(self, vision_client: Optional[LocalVisionClient] = None):
        self.vision_client = vision_client or LocalVisionClient()

    async def analyze(self, image_path: str, context: Optional[str] = None) -> ExtractionResult:
        """Analyze equipment inspection photo and return structured ExtractionResult."""
        doc_meta = FileLoader.inspect(image_path)
        prompt = INSPECTION_SYSTEM_PROMPT
        if context:
            prompt += f"\nContext Note: {context}"

        raw_result = await self.vision_client.analyze_image(image_path, prompt=prompt)

        findings_list = raw_result.get("findings", [])
        if isinstance(findings_list, str):
            findings_list = [findings_list]

        severity = raw_result.get("severity", "INFO")
        component = raw_result.get("component", "Industrial Component")
        recommendation = raw_result.get("recommendation", "")
        confidence = float(raw_result.get("confidence", 0.92))

        # Format markdown summary
        md_lines = [
            f"# Visual Inspection Analysis: {doc_meta.filename}",
            f"**Component**: {component}",
            f"**Severity**: `{severity}`",
            f"**Confidence**: {confidence:.2f}\n",
            "## Findings",
        ]
        for f in findings_list:
            md_lines.append(f"- {f}")

        if recommendation:
            md_lines.extend(["\n## Recommendation", f"> {recommendation}"])

        return ExtractionResult(
            type="image_inspection",
            text="\n".join(md_lines),
            pages=1,
            confidence=round(confidence, 2),
            tables=[],
            findings=findings_list,
            metadata={
                "filename": doc_meta.filename,
                "component": component,
                "severity": severity,
                "recommendation": recommendation,
                "pipeline": "InspectionAnalyzer"
            }
        )
