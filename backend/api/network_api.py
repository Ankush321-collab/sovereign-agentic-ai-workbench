from fastapi import APIRouter
from backend.services.network_service import NetworkService

router = APIRouter(tags=["Network / Sovereignty"])

@router.get("/network/status")
async def get_network_status():
    """
    Sovereignty & Network Status Endpoint.
    Provides verifiable proof of 0 external outbound network connections.
    """
    return NetworkService.get_sovereignty_status()
