# -*- coding: utf-8 -*-
"""
tests/test_ollama_vision.py
Owner: Roshan (feature/roshan-local-models-frontend)

Verifies that the Qwen vision model (qwen2.5vl:7b) is:
  - Running through Ollama
  - Accessible via the local API
  - Capable of receiving image input and returning descriptions
  - Operating entirely locally (no external LLM API)
"""

import sys
import base64
import time
import io
import requests
import yaml
from pathlib import Path

# Force UTF-8 output on Windows to handle emoji/unicode in print()
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── Load config ────────────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent.parent / "config" / "ollama_config.yaml"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

config = load_config()
BASE_URL      = config["ollama"]["base_url"]
VISION_MODEL  = config["models"]["vision"]["name"]

# ─── Helpers ────────────────────────────────────────────────────────────────
def pass_msg(msg: str):
    print(f"  [PASS]  {msg}")

def fail_msg(msg: str):
    print(f"  [FAIL]  {msg}")
    sys.exit(1)


def create_test_image_b64() -> str:
    """
    Creates a minimal 1x1 white PNG in memory and returns its base64 encoding.
    No disk I/O required — good for a quick connectivity test.
    Uses only stdlib so no Pillow dependency needed.
    """
    # Minimal valid 1×1 white PNG (hard-coded bytes)
    PNG_1x1_WHITE = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xA7, 0x35, 0x81,
        0x84, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ])
    return base64.b64encode(PNG_1x1_WHITE).decode("utf-8")


# ─── Tests ──────────────────────────────────────────────────────────────────

def test_ollama_is_running():
    """Test 1: Ollama must be running."""
    print("\n[1/5] Checking Ollama is running...")
    try:
        resp = requests.get(f"{BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            pass_msg(f"Ollama is running at {BASE_URL}")
        else:
            fail_msg(f"Ollama returned HTTP {resp.status_code}")
    except requests.exceptions.ConnectionError:
        fail_msg(f"Cannot connect to Ollama at {BASE_URL}. Run: ollama serve")


def test_vision_model_exists():
    """Test 2: Vision model must be installed."""
    print(f"\n[2/5] Checking model '{VISION_MODEL}' exists...")
    resp = requests.get(f"{BASE_URL}/api/tags", timeout=5)
    models = [m["name"] for m in resp.json().get("models", [])]
    base = VISION_MODEL.split(":")[0]
    matches = [m for m in models if base in m]
    if matches:
        pass_msg(f"Vision model found: {matches}")
    else:
        fail_msg(
            f"Vision model '{VISION_MODEL}' not found.\n"
            f"  Installed: {models}\n"
            f"  Run: ollama pull {VISION_MODEL}"
        )


def test_vision_text_prompt():
    """Test 3: Send a text-only prompt to the vision model."""
    print(f"\n[3/5] Testing text prompt with vision model '{VISION_MODEL}'...")
    payload = {
        "model": VISION_MODEL,
        "prompt": (
            "You are running as a local vision AI model. "
            "In one sentence, confirm you are ready to process images."
        ),
        "stream": False,
    }
    start = time.time()
    resp = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=120)
    elapsed = time.time() - start

    if resp.status_code == 200:
        response_text = resp.json().get("response", "").strip()
        if response_text:
            pass_msg(f"Text prompt responded in {elapsed:.1f}s")
            print(f"\n     Model response:\n     {response_text[:300]}\n")
        else:
            fail_msg("Response body is empty.")
    else:
        fail_msg(f"HTTP {resp.status_code}: {resp.text[:200]}")


def test_vision_image_input():
    """Test 4: Send an image (base64-encoded) to the vision model."""
    print(f"\n[4/5] Testing image input with vision model '{VISION_MODEL}'...")
    img_b64 = create_test_image_b64()

    payload = {
        "model": VISION_MODEL,
        "prompt": "Describe what you see in this image in one short sentence.",
        "images": [img_b64],   # Ollama multimodal format
        "stream": False,
    }
    start = time.time()
    resp = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=180)
    elapsed = time.time() - start

    if resp.status_code == 200:
        response_text = resp.json().get("response", "").strip()
        if response_text:
            pass_msg(f"Image input accepted and responded in {elapsed:.1f}s")
            print(f"\n     Vision response:\n     {response_text[:300]}\n")
        else:
            fail_msg("Vision model returned empty response.")
    else:
        fail_msg(f"HTTP {resp.status_code}: {resp.text[:300]}")


def test_no_external_api():
    """Test 5: Confirm everything used localhost."""
    print("\n[5/5] Verifying no external LLM API was used...")
    if "localhost" in BASE_URL or "127.0.0.1" in BASE_URL:
        pass_msg("All calls routed to local Ollama — no external dependency.")
    else:
        fail_msg(f"BASE_URL is not localhost: {BASE_URL}")


# ─── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Sovereign AI Workbench — Vision Model Test")
    print(f"  Model : {VISION_MODEL}")
    print(f"  URL   : {BASE_URL}")
    print("=" * 60)

    test_ollama_is_running()
    test_vision_model_exists()
    test_vision_text_prompt()
    test_vision_image_input()
    test_no_external_api()

    print("\n" + "=" * 60)
    print("  All tests passed. Vision model is ready. [OK]")
    print("=" * 60)
