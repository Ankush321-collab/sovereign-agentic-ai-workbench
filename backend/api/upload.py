from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import uuid
from pathlib import Path
from backend.config import UPLOADS_DIR

router = APIRouter(tags=["Upload"])

@router.post("/upload")
async def upload_file_endpoint(file: UploadFile = File(...)):
    """
    File Upload Endpoint.
    Saves uploaded document/image to data/uploads and returns metadata.
    """
    try:
        file_ext = Path(file.filename).suffix
        unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        dest_path = UPLOADS_DIR / unique_name

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "success": True,
            "file_id": str(dest_path),
            "filename": file.filename,
            "saved_as": unique_name,
            "size": dest_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
