import os
from pathlib import Path

# ── Force 100% Offline / Air-Gapped Mode ──────────────────────────────────────
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"

# Ensure directories exist
for directory in [UPLOADS_DIR, OUTPUTS_DIR, KNOWLEDGE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Service Endpoints (External module dependencies)
ROUTER_SERVICE_URL = os.getenv("ROUTER_SERVICE_URL", "http://localhost:8001")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8002")
MULTIMODAL_SERVICE_URL = os.getenv("MULTIMODAL_SERVICE_URL", "http://localhost:8003")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
SARVAM_SERVICE_URL = os.getenv("SARVAM_SERVICE_URL", os.getenv("SARVAM_ENDPOINT", "http://localhost:8001")).rstrip("/")

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Standalone Fallback Toggle (enables seamless mock responses if external team services are offline)
ENABLE_SERVICE_FALLBACKS = True
