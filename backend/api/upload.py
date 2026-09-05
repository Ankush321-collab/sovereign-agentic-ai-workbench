
from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil, uuid
from pathlib import Path
from backend.config import UPLOADS_DIR

router = APIRouter(tags=["Upload"])

@router.post("/api/upload")
@router.post("/upload")
async def upload_file_endpoint(file: UploadFile = File(...)):
    """
    File Upload. Returns {file_id, name, size} for frontend FileUpload.jsx.
    """
    try:
        uid  = uuid.uuid4().hex[:8]
        name = f"{uid}_{file.filename}"
        dest = UPLOADS_DIR / name
        with open(dest, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        return {
            "success":  True,
            "file_id":  str(dest),
            "name":     file.filename,
            "saved_as": name,
            "size":     dest.stat().st_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
