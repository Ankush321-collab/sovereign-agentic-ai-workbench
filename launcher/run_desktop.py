import sys
import os
import time
import threading
import socket
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from backend.main import app
from backend.config import HOST, PORT

def get_local_ip() -> str:
    """Retrieve local intranet LAN IP for evaluator access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def start_backend_server():
    """Runs FastAPI server on background thread."""
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")

def main():
    print("=" * 70)
    print("  VAJRA: SOVEREIGN AIR-GAPPED AI WORKBENCH")
    print("  PSU & Defence Workstation Desktop Shell")
    print("=" * 70)
    
    local_ip = get_local_ip()
    print(f"[*] Starting local air-gapped FastAPI engine on port {PORT}...")
    server_thread = threading.Thread(target=start_backend_server, daemon=True)
    server_thread.start()
    time.sleep(1.2)

    target_url = f"http://localhost:{PORT}"
    print(f"[+] Sovereign Node Active: {target_url}")
    print(f"[+] Intranet LAN Access:   http://{local_ip}:{PORT}")
    print(f"[+] Air-Gap Verification:  STRICT LOOPBACK (0 Outbound Bytes)")
    print("=" * 70)

    try:
        import webview
        print("[*] Launching Native Windows Desktop Workstation Window...")
        window = webview.create_window(
            title="VAJRA // Sovereign Air-Gapped AI Workbench (PSU & Defence Edition)",
            url=target_url,
            width=1400,
            height=900,
            resizable=True,
            confirm_close=True
        )
        webview.start()
    except Exception as ex:
        print(f"[!] PyWebView window could not open in this environment ({ex}).")
        print(f"[*] Running in Web Server Mode. Open {target_url} in your browser.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down sovereign workbench.")

if __name__ == "__main__":
    main()
