from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.services.network_service import NetworkService

router = APIRouter(tags=["Network / Sovereignty"])

@router.get("/network/status")
@router.get("/api/network/status")
async def get_network_status():
    """
    Sovereignty & Network Status Endpoint.
    Provides verifiable proof of 0 external outbound network connections.
    """
    return NetworkService.get_sovereignty_status()

@router.get("/network/audit-export")
@router.get("/api/network/audit-export")
async def export_network_audit():
    """
    Forensic Audit Export Endpoint.
    Generates a cryptographically signed SHA-256 audit record proving complete air-gap compliance.
    """
    audit = NetworkService.generate_forensic_audit()
    return JSONResponse(
        content=audit,
        headers={"Content-Disposition": f"attachment; filename=vajra_airgap_audit_{audit['report_id']}.json"}
    )
