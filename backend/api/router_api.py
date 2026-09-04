from fastapi import APIRouter
from backend.agent.state import RouteRequest, RouteResponse
from backend.services.router_service import RouterService

router = APIRouter(tags=["Router"])

@router.post("/route", response_model=RouteResponse)
async def route_query_endpoint(request: RouteRequest):
    """
    Direct Model Routing Endpoint.
    """
    res = await RouterService.route_task(
        query=request.query,
        uploaded_file="sample_image.png" if request.has_image else None
    )
    return RouteResponse(
        task=res.get("task", "general"),
        model=res.get("model", "Sarvam-30B"),
        endpoint=res.get("endpoint", "http://localhost:8001"),
        reason=res.get("reason", "Rule based routing")
    )

@router.get("/routing")
async def get_routing_info():
    """
    Gets model routing configuration and registry status.
    """
    return {
        "active_models": [
            {"task": "reasoning", "model": "Sarvam-30B", "status": "ONLINE", "endpoint": "http://localhost:8001"},
            {"task": "coding", "model": "Qwen2.5-Coder", "status": "ONLINE", "endpoint": "http://localhost:8002"},
            {"task": "vision", "model": "Qwen2.5-VL", "status": "ONLINE", "endpoint": "http://localhost:8003"}
        ]
    }
