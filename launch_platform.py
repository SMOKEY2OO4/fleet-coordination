"""
FleetIQ Platform Unified Launcher.

Simultaneously starts the FastAPI backend and Vite frontend development server:
- Backend:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)
- Frontend: http://localhost:5173
- Static App: http://127.0.0.1:8000/app
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def print_banner():
    print("=" * 80)
    print("  FLEETIQ — INTELLIGENT WAREHOUSE FLEET MANAGEMENT PLATFORM")
    print("  Multi-Robot Coordination & Congestion Intelligence Engine")
    print("=" * 80)
    print("  Local Services:")
    print("  ► Frontend Dashboard:  http://localhost:5173")
    print("  ► Integrated Web App:  http://127.0.0.1:8000/app")
    print("  ► FastAPI Core API:    http://127.0.0.1:8000")
    print("  ► Swagger API Docs:    http://127.0.0.1:8000/docs")
    print("  ► Health Check:        http://127.0.0.1:8000/health")
    print("=" * 80)
    print("  Press Ctrl+C to stop all platform services.\n")


def main():
    print_banner()

    python_bin = sys.executable
    venv_python = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        python_bin = str(venv_python)

    # 1. Start FastAPI backend with uvicorn
    backend_cmd = [
        python_bin, "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]
    print(f"[*] Starting FastAPI Backend on port 8000...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(ROOT_DIR))

    # Give backend a moment to bind
    time.sleep(1.5)

    # 2. Start Vite Frontend
    print(f"[*] Starting Vite Frontend Development Server on port 5173...")
    npm_cmd = "npm run dev"
    frontend_proc = subprocess.Popen(
        npm_cmd,
        cwd=str(ROOT_DIR / "frontend"),
        shell=True
    )

    print("\n[+] FleetIQ Platform successfully launched!\n")

    def signal_handler(sig, frame):
        print("\n[*] Shutting down FleetIQ platform services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("[!] Backend process terminated.")
                break
            if frontend_proc.poll() is not None:
                print("[!] Frontend process terminated.")
                break
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()

