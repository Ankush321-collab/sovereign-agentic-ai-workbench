from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from backend.config import OUTPUTS_DIR, UPLOADS_DIR

router = APIRouter(tags=["Files"])

@router.get("/files")
async def list_files_endpoint():
    """
    Lists all generated deliverable files and uploaded user documents.
    """
    generated = [f.name for f in OUTPUTS_DIR.glob("*.*")]
    uploaded = [f.name for f in UPLOADS_DIR.glob("*.*")]
    return {
        "generated_deliverables": generated,
        "uploaded_documents": uploaded
    }

@router.get("/files/download/{filename}")
async def download_file_endpoint(filename: str):
    """
    Downloads a deliverable or uploaded file.
    """
    # Check outputs first
    output_path = OUTPUTS_DIR / filename
    if output_path.exists():
        return FileResponse(path=str(output_path), filename=filename)

    # Check uploads
    upload_path = UPLOADS_DIR / filename
    if upload_path.exists():
        return FileResponse(path=str(upload_path), filename=filename)

    raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")
