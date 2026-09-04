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
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("multimodal.vision")

# Resolve Ollama base URL and model name from environment or config/ollama_config.yaml
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_config_path = PROJECT_ROOT / "config" / "ollama_config.yaml"
_ollama_base = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_URL")
_vision_model = os.getenv("VISION_MODEL")
if _config_path.exists():
    try:
        _txt = _config_path.read_text()
        if not _ollama_base:
            m = re.search(r"base_url:\s*(\S+)", _txt)
            if m:
                _ollama_base = m.group(1).strip()
        if not _vision_model:
            m2 = re.search(r"vision:\s*[\s\S]*?name:\s*(\S+)", _txt)
            if m2:
                _vision_model = m2.group(1).strip()
    except Exception:
        logger.debug("Failed to parse config/ollama_config.yaml; falling back to envs/defaults")

OLLAMA_BASE_URL = (_ollama_base or "http://localhost:11434").rstrip("/")
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
# Prefer explicit config, then sensible local default matching common image tags
VISION_MODEL = _vision_model or "qwen2.5vl:7b"
FALLBACK_VISION_MODEL = "llava:latest"


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
        async with httpx.AsyncClient(timeout=40.0) as client:
            # Try the /api/generate shape first
            try:
                res = await client.post(OLLAMA_URL, json=payload)
            except Exception:
                res = None

            if res is not None and res.status_code == 200:
                try:
                    data = res.json()
                except Exception:
                    text = res.text
                    return {"success": True, "text": text, "model": model, "raw": res.text}

                # Ollama generate may return 'response' or 'text'
                text = data.get("response") or data.get("text") or ""
                # Some variants return choices/message
                if not text:
                    if isinstance(data.get("message"), dict):
                        text = data.get("message", {}).get("content", "")
                    elif isinstance(data.get("choices"), list) and data["choices"]:
                        c = data["choices"][0]
                        text = c.get("text") or (c.get("message") or {}).get("content", "")

                if text:
                    return {"success": True, "text": text, "model": model, "raw": data}

            # If /api/generate didn't return expected content, try the chat endpoint
            try:
                chat_payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt, "images": [img_b64]}],
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
                chat_url = OLLAMA_BASE_URL + "/api/chat"
                res2 = await client.post(chat_url, json=chat_payload)
                if res2.status_code == 200:
                    try:
                        d2 = res2.json()
                    except Exception:
                        return {"success": True, "text": res2.text, "model": model, "raw": res2.text}

                    # chat returns message.content or similar
                    text2 = (d2.get("message") or {}).get("content") if isinstance(d2.get("message"), dict) else ""
                    if not text2 and isinstance(d2.get("choices"), list) and d2["choices"]:
                        m = d2["choices"][0].get("message") or {}
                        text2 = m.get("content") or d2["choices"][0].get("text", "")
                    if text2:
                        return {"success": True, "text": text2, "model": model, "raw": d2}
            except Exception as e:
                logger.debug(f"Chat endpoint attempt failed: {e}")
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
    import json
    import re

    findings = []
    values = []

    txt = text.strip() if isinstance(text, str) else ""

    # If model returned JSON (or JSON inside markdown fences), extract it
    if txt.startswith("{") or txt.startswith("["):
        try:
            parsed = json.loads(txt)
            if isinstance(parsed, dict):
                if parsed.get("findings"):
                    findings = parsed.get("findings")
                elif parsed.get("text"):
                    findings = [parsed.get("text")]
                # numeric values
                values = parsed.get("values", [])
                return {
                    "success": True,
                    "type": parsed.get("type", _detect_file_type_from_name(filename)),
                    "findings": findings[:10],
                    "values": values[:10],
                    "confidence": parsed.get("confidence", 0.88),
                    "model_used": model,
                    "raw_response": txt[:1000]
                }
        except Exception:
            pass

    # Extract JSON from fenced markdown if present
    if "```json" in txt or "```" in txt:
        try:
            # strip fences
            if "```json" in txt:
                body = txt.split("```json", 1)[1].split("```", 1)[0]
            else:
                body = txt.split("```", 1)[1].split("```", 1)[0]
            parsed = json.loads(body)
            if isinstance(parsed, dict) and parsed.get("findings"):
                return _parse_vision_response(json.dumps(parsed), model, filename)
        except Exception:
            pass

    # Fallback: extract bullet lines and numeric values
    for line in txt.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(("-", "*", "•", "·")) or (len(line) > 2 and line[0].isdigit() and line[1] in ".):"):
            clean = line.lstrip("-*•·0123456789.) ").strip()
            if clean:
                findings.append(clean)

    for m in re.findall(r"[\d.]+\s*(?:mm|PSI|GPM|°C|bar|kPa|%)", txt):
        values.append(m.strip())

    if not findings:
        findings = [txt[:300]] if txt else ["No findings extracted"]

    return {
        "success": True,
        "type": _detect_file_type_from_name(filename),
        "findings": findings[:10],
        "values": list(dict.fromkeys(values))[:10],
        "confidence": 0.88,
        "model_used": model,
        "raw_response": txt[:1000]
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
