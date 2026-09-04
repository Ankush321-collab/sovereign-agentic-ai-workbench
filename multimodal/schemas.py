from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MultimodalDocument(BaseModel):
    """Metadata representing an ingested file for multimodal processing."""
    file_path: str = Field(..., description="Absolute or relative path to the local file")
    filename: str = Field(..., description="Original file name")
    mime_type: str = Field("application/octet-stream", description="Detected MIME type")
    file_size_bytes: int = Field(0, description="Size of the file in bytes")
    page_count: int = Field(1, description="Total pages in document")

class TableData(BaseModel):
    """Structured table representation with headers and rows."""
    page: int = Field(1, description="1-based page number where the table is located")
    headers: List[str] = Field(default_factory=list, description="Column header titles")
    rows: List[List[str]] = Field(default_factory=list, description="Row values")
    markdown: str = Field("", description="Markdown-formatted table string")

class InspectionFinding(BaseModel):
    """Visual defect or diagnostic observation from equipment inspection."""
    finding: str = Field(..., description="Description of the finding")
    severity: Optional[str] = Field("INFO", description="Severity level: INFO, WARNING, ALERT, CRITICAL")
    component: Optional[str] = Field(None, description="Associated component or tag identifier")
    measurement: Optional[str] = Field(None, description="Quantitative measurement if available")

class PIDEquipment(BaseModel):
    """Equipment item identified in a P&ID schematic."""
    tag: str = Field(..., description="Equipment tag identifier, e.g. P-101A, V-204")
    type: str = Field(..., description="Equipment category, e.g. Centrifugal Slurry Pump, Vessel")
    description: Optional[str] = Field("", description="Contextual engineering description")
    status: Optional[str] = Field("Operational", description="Operating status or condition")

class PIDInstrument(BaseModel):
    """Instrument sensor or control loop identified in a P&ID schematic."""
    tag: str = Field(..., description="ISA-5.1 instrument tag, e.g. PT-201, FT-102, LCV-301")
    type: str = Field(..., description="Instrument classification, e.g. Pressure Transmitter")
    loop_id: Optional[str] = Field("", description="Loop identification number")
    range: Optional[str] = Field("", description="Operating range or calibration limits")

class ExtractionResult(BaseModel):
    """Unified payload returned by the multimodal extraction pipeline."""
    type: str = Field("standard_document", description="Document type: scanned_inspection_report, p_and_id_drawing, image_inspection, standard_document, unknown")
    text: str = Field("", description="Extracted full text in Markdown format")
    pages: int = Field(1, description="Total number of pages processed")
    confidence: float = Field(1.0, description="Estimated extraction confidence score (0.0 to 1.0)")
    tables: List[TableData] = Field(default_factory=list, description="Extracted tabular data")
    findings: List[str] = Field(default_factory=list, description="Inspection findings or highlights")
    equipment: Optional[List[PIDEquipment]] = Field(default_factory=list, description="Detected P&ID equipment tags")
    instruments: Optional[List[PIDInstrument]] = Field(default_factory=list, description="Detected P&ID instrument tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic and processing telemetry")

class ProcessRequest(BaseModel):
    """Request payload for POST /multimodal/process."""
    file_path: str = Field(..., description="Path to the document/image file")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Processing flags and overrides")
