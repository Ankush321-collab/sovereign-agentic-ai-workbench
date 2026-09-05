from typing import TypedDict, List, Optional, Any, Dict
from pydantic import BaseModel, Field

class ThicknessReading(BaseModel):
    location_id: str
    nominal_thickness_mm: float
    measured_thickness_mm: float
    minimum_allowable_thickness_mm: float
    corrosion_rate_mm_per_year: float

class CalculationResult(BaseModel):
    equipment_tag: str
    design_thickness_mm: float
    retirement_thickness_mm: float
    minimum_measured_mm: float
    remaining_operating_life_years: float
    asme_b31_3_compliant: bool
    risk_category: str
    formula_applied: str
    execution_time_ms: float
    sandbox_environment: str

class ApprovalSignatory(BaseModel):
    role_title: str
    department: str
    name: str
    status: str

class PSUApprovalNote(BaseModel):
    file_reference_no: str
    organization: str = "INDIAN OIL CORPORATION LIMITED"
    division: str = "Pipelines & Refinery Operations Division"
    subject: str
    background_summary: str
    inspection_findings_table: List[Dict[str, Any]]
    statutory_standard: str = "ASME B31.3 / OISD-105"
    operational_risk_assessment: str
    financial_sanction_inr: str
    recommendation_for_approval: str
    signatories: List[ApprovalSignatory]
    generated_docx_path: str

# Shared Agent State as defined in Section 4.3 of Team Spec
class AgentState(TypedDict):
    user_query: str
    uploaded_file: Optional[str]
    task_type: str
    selected_model: str
    routing_reason: str
    context: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    inspection_data: Optional[Dict[str, Any]]
    calculation_results: Optional[Dict[str, Any]]
    final_response: str
    generated_files: List[str]
    audit_log: List[Dict[str, Any]]


# Pydantic Schemas for FastAPI Endpoints
class ChatRequest(BaseModel):
    message: str = Field(..., description="User query or instruction")
    file_id: Optional[str] = Field(None, description="Optional uploaded file identifier or path")

class ChatResponse(BaseModel):
    response: str
    task_type: str
    model: str
    routing_reason: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)

class RouteRequest(BaseModel):
    query: str
    has_image: bool = False
    has_file: bool = False

class RouteResponse(BaseModel):
    task: str
    model: str
    endpoint: str
    reason: str

class NetworkStatusResponse(BaseModel):
    external_connections: int = 0
    local_connections: int = 4
    internet_blocked: bool = True

class RAGSearchRequest(BaseModel):
    query: str

class MultimodalProcessRequest(BaseModel):
    file_path: str
