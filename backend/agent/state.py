from typing import TypedDict, List, Optional, Any, Dict
from pydantic import BaseModel, Field

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
