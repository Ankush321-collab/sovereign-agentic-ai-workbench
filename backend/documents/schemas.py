from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class InspectionFinding(BaseModel):
    Component: str
    Nominal: str
    Measured: str
    Status: str

class PDFApprovalData(BaseModel):
    file_reference_no: str
    date: str
    subject: str
    background_summary: str
    statutory_standard: str
    operational_risk_assessment: str
    financial_sanction_inr: str
    recommendation_for_approval: str
    inspection_findings_table: List[InspectionFinding]

class ArtifactResult(BaseModel):
    filename: str
    file_type: str
    path: str
    sha256: str
    validation_status: str
    source_evidence_ids: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
