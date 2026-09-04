"""
run.py — Sovereign AI Workbench Turbo Launcher
Smart India Hackathon 2026 | Team Quanta Codes

Runs everything at once with 1 command:
  1. Checks Ollama local daemon
  2. Starts FastAPI Backend on port 8000
  3. Starts Vite React Frontend on port 5173
  4. Auto-opens browser to http://localhost:5173
  5. Gracefully terminates all services on Ctrl+C
"""

import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"

def log(prefix: str, msg: str):
    try:
        print(f"[{prefix}] {msg}", flush=True)
    except Exception:
        pass

def stream_output(proc: subprocess.Popen, prefix: str):
    try:
        for line in iter(proc.stdout.readline, ""):
            if line:
                log(prefix, line.strip())
    except Exception:
        pass

def check_ollama():
    log("OLLAMA", "Checking local Ollama daemon on http://localhost:11434...")
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2.0) as res:
            if res.status == 200:
                log("OLLAMA", "Ollama is ONLINE with local models ready. [OK]")
                return True
    except Exception:
        log("OLLAMA", "Ollama not running on port 11434 (fallbacks enabled).")
    return False

def main():
    print("""
===============================================================
       🛡️  SOVEREIGN AI WORKBENCH — TURBO LAUNCHER  🛡️
                   SIH 2026 | Team Quanta Codes
===============================================================
""", flush=True)

    check_ollama()
    processes = []

    try:
        # 1. Start Backend
        log("BACKEND", "Starting FastAPI backend on http://localhost:8000...")
        backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )
        processes.append(("Backend", backend_proc))
        threading.Thread(target=stream_output, args=(backend_proc, "BACKEND"), daemon=True).start()

        time.sleep(1.5)

        # 2. Start Frontend
        log("FRONTEND", "Starting Vite frontend on http://localhost:5173...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=True
        )
        processes.append(("Frontend", frontend_proc))
        threading.Thread(target=stream_output, args=(frontend_proc, "FRONTEND"), daemon=True).start()

        time.sleep(2.0)

        # 3. Open Browser
        log("LAUNCHER", "Opening browser at http://localhost:5173...")
        webbrowser.open("http://localhost:5173")

        print("\n🚀 All services running! Press Ctrl+C anytime to stop.\n", flush=True)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all services...", flush=True)
        for name, proc in processes:
            try:
                proc.terminate()
            except Exception:
                pass
        print("All services stopped. Exiting.", flush=True)

if __name__ == "__main__":
    main()
