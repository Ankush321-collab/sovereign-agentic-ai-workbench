
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from backend.config import OUTPUTS_DIR, UPLOADS_DIR

router = APIRouter(tags=["Files"])

@router.get("/api/files")
@router.get("/files")
async def list_files_endpoint():
    """
    Lists generated output files as objects.
    Frontend expects: [{name, type, size}]
    """
    results = []
    for f in OUTPUTS_DIR.glob("*.*"):
        try:
            results.append({
                "name": f.name,
                "type": f.suffix.lstrip(".").lower(),
                "size": f.stat().st_size,
            })
        except Exception:
            pass
    return results

@router.get("/api/files/download/{filename}")
@router.get("/files/download/{filename}")
async def download_file_endpoint(filename: str):
    """Downloads a generated or uploaded file."""
    for directory in (OUTPUTS_DIR, UPLOADS_DIR):
        path = directory / filename
        if path.exists():
            return FileResponse(path=str(path), filename=filename)
    raise HTTPException(status_code=404, detail=f"File not found: {filename}")
