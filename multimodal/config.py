import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_documents"
OUTPUTS_DIR = DATA_DIR / "outputs"

for d in [DATA_DIR, UPLOADS_DIR, SAMPLE_DOCS_DIR, OUTPUTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Microservice Configuration
HOST = os.getenv("MULTIMODAL_HOST", "0.0.0.0")
PORT = int(os.getenv("MULTIMODAL_PORT", "8003"))

# Vision Model Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5-vl")
VISION_ENDPOINT_FALLBACK = os.getenv("VISION_ENDPOINT_FALLBACK", "http://localhost:8003/v1")

# OCR Engine Configuration
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
# Common Windows installation locations for Tesseract
if not TESSERACT_CMD and os.name == "nt":
    win_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in win_paths:
        if Path(p).exists():
            TESSERACT_CMD = p
            break

# Feature toggles
ENABLE_FALLBACKS = os.getenv("ENABLE_MULTIMODAL_FALLBACKS", "true").lower() in ("true", "1", "yes")
ENABLE_DOCLING = os.getenv("ENABLE_DOCLING", "false").lower() in ("true", "1", "yes")
ENABLE_VISION_LLM = os.getenv("ENABLE_VISION_LLM", "true").lower() in ("true", "1", "yes")
