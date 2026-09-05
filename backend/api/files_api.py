
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from backend.config import OUTPUTS_DIR, UPLOADS_DIR, KNOWLEDGE_DIR, DATA_DIR
from backend.tools.file_tool import resolve_file_path, _clean_name

router = APIRouter(tags=["Files"])

@router.get("/api/files")
@router.get("/files")
async def list_files_endpoint():
    """
    Lists all workspace files (outputs, knowledge, sample documents, uploads).
    Frontend expects: [{name, clean_name, type, size, category}]
    """
    results = []
    seen = set()

    for category, directory in [
        ("Output Deliverable", OUTPUTS_DIR),
        ("Knowledge Vault", KNOWLEDGE_DIR),
        ("Sample Document", DATA_DIR / "sample_documents"),
        ("Uploaded File", UPLOADS_DIR)
    ]:
        if directory.exists():
            for f in sorted(directory.glob("*.*")):
                if f.is_file() and not f.name.startswith(".") and f.name not in seen:
                    seen.add(f.name)
                    try:
                        results.append({
                            "name": f.name,
                            "clean_name": _clean_name(f.name),
                            "type": f.suffix.lstrip(".").lower(),
                            "size": f.stat().st_size,
                            "category": category
                        })
                    except Exception:
                        pass
    return results

MIME_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pdf": "application/pdf",
    "txt": "text/plain",
    "py": "text/x-python",
    "csv": "text/csv",
    "json": "application/json",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}

@router.get("/api/files/download/{filename:path}")
@router.get("/files/download/{filename:path}")
async def download_file_endpoint(filename: str):
    """Downloads a generated or workspace file with proper Content-Disposition and MIME headers."""
    resolved = resolve_file_path(filename)
    if resolved and resolved.exists() and resolved.is_file():
        ext = resolved.suffix.lstrip(".").lower()
        media_type = MIME_TYPES.get(ext, "application/octet-stream")
        download_name = resolved.name

        return FileResponse(
            path=str(resolved),
            filename=download_name,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{download_name}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    raise HTTPException(status_code=404, detail=f"File not found: {filename}")
