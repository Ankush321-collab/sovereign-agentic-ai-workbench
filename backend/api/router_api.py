from fastapi import APIRouter
from backend.router.schemas import RouteRequest, RouteResponse, ModelListResponse
from backend.router.router import ModelRouter
from backend.services.router_service import RouterService

router = APIRouter(prefix="/api/router", tags=["Router"])

# Singleton router instance
_model_router = ModelRouter()

@router.post("/route", response_model=RouteResponse)
async def route_query_endpoint(request: RouteRequest):
    """
    Direct Model Routing Endpoint with multi-stage explainable scoring.
    Returns task_class, feature_vector, score_breakdown, admitted_vram_gb.
    """
    response = _model_router.route(request)
    return response

@router.get("/models", response_model=ModelListResponse)
async def get_models_endpoint():
    """
    Returns all registered models with health status, VRAM, and quantization.
    Used by frontend ModelRouting.jsx component.
    """
    return _model_router.get_models()

@router.get("/history")
async def get_routing_history():
    """
    Returns routing history for audit and debugging.
    """
    return _model_router.get_history()

@router.get("/routing")
async def get_routing_info():
    """
    Legacy endpoint - returns simplified routing configuration.
    Kept for backward compatibility with existing frontend components.
    """
    models = _model_router.get_models()
    return {
        "active_models": [
            {
                "task": m.task,
                "model": m.name,
                "status": "ONLINE" if m.healthy else "OFFLINE",
                "endpoint": m.endpoint or "http://localhost:11434"
            }
            for m in models.models
        ]
    }

# Legacy un-prefixed router alias for /route and /routing compatibility
legacy_router = APIRouter(tags=["Router-Legacy"])

@legacy_router.post("/route", response_model=RouteResponse)
async def legacy_route_query_endpoint(request: RouteRequest):
    return _model_router.route(request)

@legacy_router.get("/routing")
async def legacy_get_routing_info():
    return await get_routing_info()

@legacy_router.get("/models", response_model=ModelListResponse)
async def legacy_get_models_endpoint():
    return _model_router.get_models()
