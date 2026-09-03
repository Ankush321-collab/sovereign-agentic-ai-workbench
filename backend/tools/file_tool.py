from pathlib import Path
import logging
from backend.config import UPLOADS_DIR, OUTPUTS_DIR

logger = logging.getLogger("file_tool")

def read_file(file_path: str) -> dict:
    """Reads content from a local file securely."""
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = UPLOADS_DIR / file_path
        
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
            
        content = path.read_text(encoding="utf-8", errors="ignore")
        return {"success": True, "file_path": str(path), "content": content, "size": len(content)}
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return {"success": False, "error": str(e)}

def write_file(file_path: str, content: str) -> dict:
    """Writes text content to a file in outputs directory."""
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = OUTPUTS_DIR / file_path

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"success": True, "file_path": str(path), "bytes_written": len(content)}
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return {"success": False, "error": str(e)}
