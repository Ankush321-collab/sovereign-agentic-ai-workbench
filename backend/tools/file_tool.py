from pathlib import Path
import logging
import re
from typing import List, Dict, Any
from backend.config import DATA_DIR, UPLOADS_DIR, OUTPUTS_DIR, KNOWLEDGE_DIR, PROJECT_ROOT

logger = logging.getLogger("file_tool")

SEARCH_DIRS = [
    KNOWLEDGE_DIR,
    UPLOADS_DIR,
    DATA_DIR / "sample_documents",
    DATA_DIR,
    OUTPUTS_DIR
]

def _clean_name(filename: str) -> str:
    """Strips UUID prefixes like 0ad5969d_ from uploaded filenames."""
    return re.sub(r'^[a-f0-9]{8,12}_', '', filename, flags=re.IGNORECASE)

def resolve_file_path(file_path: str) -> Path | None:
    """Finds and resolves an absolute or relative file path across all workspace directories."""
    if not file_path:
        return None
        
    p = Path(file_path)
    if p.is_absolute() and p.exists():
        return p

    target_name = p.name.lower()
    cleaned_target = _clean_name(p.name).lower()

    # Check search directories
    for d in SEARCH_DIRS:
        if d.exists():
            candidate = d / file_path
            if candidate.exists() and candidate.is_file():
                return candidate
            # Check by exact or clean filename
            for f in d.glob("*.*"):
                if f.is_file():
                    fname_lower = f.name.lower()
                    fclean_lower = _clean_name(f.name).lower()
                    if fname_lower == target_name or fclean_lower == target_name or fclean_lower == cleaned_target:
                        return f

    return None

def auto_detect_relevant_files(query: str) -> List[Dict[str, Any]]:
    """
    Scans the local workspace (knowledge, uploads, sample documents) and automatically
    detects files relevant to the user query based on exact word boundary and stem matching.
    """
    if not query:
        return []

    q_lower = query.lower()
    
    # Check if this is a file-generation query rather than a file-reading query
    is_write_intent = any(w in q_lower for w in ["write", "create", "generate", "save to", "save as"]) and not any(w in q_lower for w in ["from", "using file", "based on file", "read"])
    
    stopwords = {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "of", "to", "for",
        "with", "by", "from", "show", "get", "what", "how", "file", "document", "files",
        "documents", "read", "open", "check", "tell", "about", "please", "all", "one", "code",
        "python", "generate", "create", "write", "save", "operation", "class", "data", "new"
    }
    
    clean_q = re.sub(r'[^a-zA-Z0-9_\-\.]', ' ', q_lower)
    query_tokens = [w for w in clean_q.split() if len(w) > 2 and w not in stopwords]

    detected = []
    seen_paths = set()

    # Search in knowledge, sample documents, and uploads (NOT outputs, since outputs are generated deliverables)
    for directory in [KNOWLEDGE_DIR, DATA_DIR / "sample_documents", UPLOADS_DIR]:
        if not directory.exists():
            continue

        for f in directory.glob("*.*"):
            if f.is_dir() or f.name.startswith("."):
                continue

            fname_lower = f.name.lower()
            clean_fname = _clean_name(f.name).lower()
            stem_lower = f.stem.lower()
            clean_stem = _clean_name(f.stem).lower()

            match_score = 0

            # 1. Exact full filename mentioned in query with word boundary
            if re.search(rf'\b{re.escape(fname_lower)}\b', q_lower) or re.search(rf'\b{re.escape(clean_fname)}\b', q_lower):
                match_score += 12

            # 2. Distinct stem mentioned in query (only for stems >= 3 chars, strict word boundary)
            elif len(clean_stem) >= 3 and re.search(rf'\b{re.escape(clean_stem)}\b', q_lower):
                match_score += 9

            # 3. Specific enterprise file domain keywords (only if query is asking to inspect/check that domain)
            if not is_write_intent:
                if any(re.search(rf'\b{k}\b', q_lower) for k in ["emergency", "shutdown", "evacuat", "trip"]) and "emergency" in clean_fname:
                    match_score += 8
                if any(re.search(rf'\b{k}\b', q_lower) for k in ["torque", "bolt", "equipment", "manual", "bearing"]) and "equipment" in clean_fname:
                    match_score += 8
                if any(re.search(rf'\b{k}\b', q_lower) for k in ["valve", "actuator", "seat", "leakage", "gasket"]) and "valve" in clean_fname:
                    match_score += 8
                if any(re.search(rf'\b{k}\b', q_lower) for k in ["sop", "ppe", "hazard", "safety guideline"]) and "safety" in clean_fname:
                    match_score += 8
                if any(re.search(rf'\b{k}\b', q_lower) for k in ["flange corrosion", "thickness loss", "ultrasonic inspection"]) and ("inspection" in clean_fname or "flange" in clean_fname):
                    match_score += 8
                if any(re.search(rf'\b{k}\b', q_lower) for k in ["tuition", "tution", "hostel rent", "mess rent", "insurance fee"]) and any(w in clean_fname for w in ["tution", "tuition", "rent", "insurance"]):
                    match_score += 8
                if any(re.search(rf'\b{k}\b', q_lower) for k in ["p&id drawing", "pid diagram", "engineering schematic"]) and any(w in clean_fname for w in ["drawing", "pid", "schematic"]):
                    match_score += 8

            # Only accept files with a confident match score (>= 8)
            if match_score >= 8 and str(f) not in seen_paths:
                seen_paths.add(str(f))
                detected.append({
                    "name": f.name,
                    "clean_name": _clean_name(f.name),
                    "path": str(f),
                    "size": f.stat().st_size,
                    "type": f.suffix.lstrip(".").lower(),
                    "score": match_score
                })

    detected.sort(key=lambda x: x["score"], reverse=True)
    return detected

def read_file(file_path: str) -> dict:
    """Reads content from a local file securely across all workspace directories."""
    try:
        resolved = resolve_file_path(file_path)
        if not resolved:
            return {"success": False, "error": f"File '{file_path}' not found in workspace."}

        suffix = resolved.suffix.lower()
        clean_name = _clean_name(resolved.name)

        # Plain text formats
        if suffix in [".txt", ".md", ".csv", ".json", ".py", ".yaml", ".yml", ".log", ".sql", ".sh"]:
            content = resolved.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            return {
                "success": True,
                "filename": resolved.name,
                "clean_name": clean_name,
                "file_path": str(resolved),
                "content": content,
                "lines": len(lines),
                "size": len(content),
                "preview": content[:800] + ("..." if len(content) > 800 else "")
            }

        # Rich formats (DOCX, PDF, XLSX, PPTX, Images) via MarkItDown
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            res = md.convert(str(resolved))
            text = res.text_content or ""
            return {
                "success": True,
                "filename": resolved.name,
                "clean_name": clean_name,
                "file_path": str(resolved),
                "content": text,
                "size": len(text),
                "preview": text[:800] + ("..." if len(text) > 800 else "")
            }
        except Exception as conv_err:
            logger.warning(f"MarkItDown extraction failed for {resolved.name} ({conv_err})")
            return {
                "success": True,
                "filename": resolved.name,
                "clean_name": clean_name,
                "file_path": str(resolved),
                "content": f"[Binary/Document file {clean_name} ({resolved.stat().st_size} bytes)]",
                "size": resolved.stat().st_size,
                "preview": f"Binary/Document file ({suffix})"
            }

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
        return {
            "success": True,
            "filename": path.name,
            "file_path": str(path),
            "bytes_written": len(content),
            "size": path.stat().st_size
        }
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return {"success": False, "error": str(e)}
