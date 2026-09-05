# -*- coding: utf-8 -*-
"""
tests/test_ollama_text.py
Owner: Roshan (feature/roshan-local-models-frontend)

Verifies that the Qwen text model (qwen2.5:7b-instruct) is:
  - Running through Ollama
  - Accessible via the local API
  - Responding to prompts without any external LLM API
"""

import sys
import io
import json
import time
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
BASE_URL  = config["ollama"]["base_url"]
TEXT_MODEL = config["models"]["text"]["name"]

# --- Helpers ----------------------------------------------------------------
def pass_msg(msg: str):
    print(f"  [PASS]  {msg}")

def fail_msg(msg: str):
    print(f"  [FAIL]  {msg}")
    sys.exit(1)

# --- Tests ------------------------------------------------------------------

def test_ollama_is_running():
    """Test 1: Check that Ollama is running and reachable."""
    print("\n[1/4] Checking Ollama is running...")
    try:
        resp = requests.get(f"{BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            pass_msg(f"Ollama is running at {BASE_URL}")
        else:
            fail_msg(f"Ollama returned HTTP {resp.status_code}")
    except requests.exceptions.ConnectionError:
        fail_msg(f"Cannot connect to Ollama at {BASE_URL}. Run: ollama serve")


def test_model_exists():
    """Test 2: Check that the text model is installed."""
    print(f"\n[2/4] Checking model '{TEXT_MODEL}' exists...")
    resp = requests.get(f"{BASE_URL}/api/tags", timeout=5)
    models = [m["name"] for m in resp.json().get("models", [])]
    matches = [m for m in models if TEXT_MODEL.split(":")[0] in m]
    if matches:
        pass_msg(f"Model found: {matches}")
    else:
        fail_msg(
            f"Model '{TEXT_MODEL}' not found.\n"
            f"  Installed models: {models}\n"
            f"  Run: ollama pull {TEXT_MODEL}"
        )


def test_text_generation():
    """Test 3: Send a test prompt and receive a response."""
    print(f"\n[3/4] Testing text generation with '{TEXT_MODEL}'...")
    payload = {
        "model": TEXT_MODEL,
        "prompt": (
            "You are a helpful assistant for an industrial AI workbench. "
            "In one sentence, confirm that you are running locally."
        ),
        "stream": False,
    }
    start = time.time()
    resp = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=120)
    elapsed = time.time() - start

    if resp.status_code == 200:
        data = resp.json()
        response_text = data.get("response", "").strip()
        if response_text:
            pass_msg(f"Response received in {elapsed:.1f}s")
            print(f"\n     Model response:\n     {response_text[:300]}\n")
        else:
            fail_msg("Response body is empty.")
    else:
        fail_msg(f"HTTP {resp.status_code}: {resp.text[:200]}")


def test_no_external_api():
    """Test 4: Verify the call went to localhost (not a cloud LLM)."""
    print("\n[4/4] Verifying no external LLM API was used...")
    if "localhost" in BASE_URL or "127.0.0.1" in BASE_URL:
        pass_msg("All calls routed to local Ollama — no external LLM dependency.")
    else:
        fail_msg(f"BASE_URL is not localhost: {BASE_URL}")


# ─── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Sovereign AI Workbench — Text Model Test")
    print(f"  Model : {TEXT_MODEL}")
    print(f"  URL   : {BASE_URL}")
    print("=" * 60)

    test_ollama_is_running()
    test_model_exists()
    test_text_generation()
    test_no_external_api()

    print("\n" + "=" * 60)
    print("  All tests passed. Text model is ready. [OK]")
    print("=" * 60)
