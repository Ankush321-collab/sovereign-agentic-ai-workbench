from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RouteRequest(BaseModel):
    query: str
    has_image: bool = False
    has_file: bool = False
    task_type: Optional[str] = None

class RouteResponse(BaseModel):
    task_type: str
    model: str
    endpoint: Optional[str] = None
    reason: str
    fallback: bool = False
    healthy: bool = True

class ModelInfo(BaseModel):
    name: str
    task: str
    enabled: bool
    healthy: bool
    endpoint: Optional[str] = None

class ModelListResponse(BaseModel):
    models: List[ModelInfo]

class HistoryItem(BaseModel):
    task_type: str
    model: str
    reason: str
    endpoint: Optional[str] = None

class HistoryResponse(BaseModel):
    history: List[HistoryItem]

class SocketConnection(BaseModel):
    pid: int
    local_address: str
    remote_address: Optional[str] = None
    status: str
    is_loopback: bool
    is_external: bool

class SovereigntyStatus(BaseModel):
    timestamp: str
    external_connections: int = 0
    local_connections: int
    internet_blocked: bool = True
    firewall_status: str = "ACTIVE - ZERO EGRESS"
    airgap_verification: str = "PASSED - LOCAL LOOPBACK ONLY"
    active_services: List[Dict[str, Any]]
    audit_hash: str

class ForensicAuditReport(BaseModel):
    report_id: str
    timestamp: str
    host_system: str
    total_sockets_scanned: int
    external_violations_detected: int = 0
    loopback_verified: bool = True
    sockets: List[SocketConnection]
    integrity_signature_sha256: str
