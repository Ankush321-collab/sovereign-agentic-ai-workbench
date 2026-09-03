from fastapi import APIRouter
from backend.router.schemas import RouteRequest, RouteResponse, ModelListResponse, HistoryResponse
from backend.router.router import ModelRouter

router = APIRouter()
model_router = ModelRouter()

@router.post("/route", response_model=RouteResponse)
def route_request(request: RouteRequest):
    return model_router.route(request)

@router.get("/models", response_model=ModelListResponse)
def get_models():
    return model_router.get_models()

@router.get("/routing/history", response_model=HistoryResponse)
def get_history():
    return model_router.get_history()
