from pydantic import BaseModel, Field
from typing import List, Optional

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
