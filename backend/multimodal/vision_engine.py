"""
backend/multimodal/vision_engine.py
Pankaj's Multimodal Module — Vision Understanding Engine

Per README Section 7.3:
  Image → Vision Model (Qwen2.5-VL via Ollama) → Structured findings JSON

Calls Ollama's vision-capable model locally.
Falls back gracefully if Ollama is not running or vision model unavailable.
"""

import logging
import httpx
import base64
from pathlib import Path
from typing import Any

logger = logging.getLogger("multimodal.vision")

OLLAMA_URL = "http://localhost:11434/api/generate"
VISION_MODEL = "qwen2.5vl:latest"        # Qwen2.5-VL via Ollama
FALLBACK_VISION_MODEL = "llava:latest"   # llava as secondary vision model


def _encode_image_base64(file_path: str) -> str | None:
    """Encode image file to base64 for Ollama vision API."""
    try:
        return base64.b64encode(Path(file_path).read_bytes()).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encode image {file_path}: {e}")
        return None


async def analyze_image(file_path: str, context_hint: str = "") -> dict[str, Any]:
    """
    Sends an image to Qwen2.5-VL (or LLaVA fallback) via Ollama for visual analysis.

    Per README spec, returns:
      {type, findings: [...], values: [...], confidence, model_used}
    """
    path = Path(file_path)
    if not path.exists():
        return _error_result(f"Image file not found: {file_path}")

    if path.suffix.lower() not in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        return _error_result(f"Not a supported image type: {path.suffix}")

    img_b64 = _encode_image_base64(file_path)
    if not img_b64:
        return _error_result("Could not encode image")

    prompt = _build_vision_prompt(path.name, context_hint)

    # Try primary vision model, then fallback
    for model in [VISION_MODEL, FALLBACK_VISION_MODEL]:
        result = await _call_ollama_vision(model, prompt, img_b64)
        if result.get("success"):
            return _parse_vision_response(result["text"], model, path.name)

    logger.warning("No vision model available — returning heuristic analysis")
    return _heuristic_analysis(path.name)


def analyze_image_sync(file_path: str, context_hint: str = "") -> dict[str, Any]:
    """Synchronous wrapper for use from non-async contexts."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, analyze_image(file_path, context_hint))
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(analyze_image(file_path, context_hint))
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        return _heuristic_analysis(Path(file_path).name)


async def _call_ollama_vision(model: str, prompt: str, img_b64: str) -> dict:
    """Calls Ollama's generate API with an image payload."""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 500}
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(OLLAMA_URL, json=payload)
            if res.status_code == 200:
                data = res.json()
                return {"success": True, "text": data.get("response", ""), "model": model}
    except Exception as e:
        logger.warning(f"Ollama vision call failed for model {model}: {e}")
    return {"success": False}


def _build_vision_prompt(filename: str, context: str) -> str:
    base = (
        "You are an industrial document analysis AI for a confidential refinery. "
        "Analyze this image and provide a structured assessment.\n\n"
    )
    if "pid" in filename.lower() or "drawing" in filename.lower():
        return base + (
            "This appears to be a P&ID (Piping and Instrumentation Diagram). "
            "List all visible equipment tags (P-, V-, K-, E-), instrument tags (PT-, FT-, TT-, XV-), "
            "and describe any notable features. Format findings as a clear list."
        )
    elif "inspection" in filename.lower() or "report" in filename.lower():
        return base + (
            "This is an industrial inspection report image. "
            "Identify: 1) Any equipment tags or component IDs visible, "
            "2) Findings (corrosion, damage, anomalies), "
            "3) Measurements or readings visible, "
            "4) Recommended actions if stated. Format as bullet points."
        )
    else:
        return base + (
            f"Analyze this industrial document image ({filename}). "
            f"{('Context: ' + context) if context else ''} "
            "List key findings, any equipment tags, measurements, and recommendations."
        )


def _parse_vision_response(text: str, model: str, filename: str) -> dict:
    """Parse the vision model's text response into structured output."""
    findings = []
    values = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(("-", "*", "•", "·")) or (len(line) > 2 and line[0].isdigit() and line[1] in ".):"):
            clean = line.lstrip("-*•·0123456789.) ").strip()
            if clean:
                findings.append(clean)

    import re
    # Extract numeric measurements
    for m in re.findall(r"[\d.]+\s*(?:mm|PSI|GPM|°C|bar|kPa|%)", text):
        values.append(m.strip())

    if not findings:
        findings = [text[:300]] if text else ["No findings extracted"]

    return {
        "success": True,
        "type": _detect_file_type_from_name(filename),
        "findings": findings[:10],
        "values": list(set(values))[:10],
        "confidence": 0.88,
        "model_used": model,
        "raw_response": text[:500]
    }


def _heuristic_analysis(filename: str) -> dict:
    """Returns a heuristic result when no vision model is available."""
    name_lower = filename.lower()
    if "pid" in name_lower or "drawing" in name_lower:
        return {
            "success": True,
            "type": "p_and_id_drawing",
            "findings": ["P&ID diagram detected", "Equipment tags present — requires vision model for full extraction"],
            "values": [],
            "confidence": 0.5,
            "model_used": "heuristic",
            "note": "Vision model not available — install Qwen2.5-VL or LLaVA via Ollama"
        }
    return {
        "success": True,
        "type": _detect_file_type_from_name(filename),
        "findings": ["Document image detected", "Visual content requires vision model for extraction"],
        "values": [],
        "confidence": 0.4,
        "model_used": "heuristic",
        "note": "Vision model not available — install Qwen2.5-VL or LLaVA via Ollama"
    }


def _detect_file_type_from_name(filename: str) -> str:
    name = filename.lower()
    if "pid" in name or "drawing" in name or "schematic" in name:
        return "p_and_id_drawing"
    if "inspection" in name or "report" in name:
        return "inspection_report"
    if "sop" in name or "safety" in name:
        return "safety_document"
    return "industrial_document"


def _error_result(msg: str) -> dict:
    return {
        "success": False, "error": msg,
        "type": "unknown", "findings": [], "values": [],
        "confidence": 0.0, "model_used": "none"
    }
