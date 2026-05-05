from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def run_cli() -> None:
    from pss_ai.cli import main as cli_main

    cli_main()


def run_api(host: str, port: int, open_browser: bool = True) -> None:
    from pss_ai.api import app
    import uvicorn

    if open_browser:
        webbrowser.open(f"http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


def run_doctor_demo() -> None:
    from pss_ai import AppSettings, PSSAssistant
    from pss_ai.models import UserQuery

    assistant = PSSAssistant(AppSettings())
    result = assistant.run(UserQuery(text="Dolore toracico e tachicardia", comune="Milano"), extracted_terms=["VISITA CARDIOLOGICA"])
    print(result)


def _resolve_npm_command() -> str:
    if os.name == "nt":
        return shutil.which("npm.cmd") or "npm.cmd"
    return shutil.which("npm") or "npm"


def run_full(host: str, port: int) -> None:
    backend_cmd = [sys.executable, "main.py", "api", "--host", host, "--port", str(port)]
    npm_cmd = [_resolve_npm_command(), "--prefix", "frontend", "run", "dev"]

    backend = subprocess.Popen(backend_cmd, cwd=ROOT)
    frontend = subprocess.Popen(npm_cmd, cwd=ROOT)

    try:
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:5173")
        while True:
            if backend.poll() is not None:
                raise RuntimeError("Backend process terminated.")
            if frontend.poll() is not None:
                raise RuntimeError("Frontend process terminated.")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (frontend, backend):
            if proc.poll() is None:
                proc.terminate()
        for proc in (frontend, backend):
            try:
                proc.wait(timeout=5)
            except Exception:
                if proc.poll() is None:
                    proc.kill()


def main() -> None:
    parser = argparse.ArgumentParser(description="PSS AI assistant launcher")
    parser.add_argument("mode", nargs="?", default="web", choices=["web", "api", "cli", "demo", "full"], help="Run mode")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    args = parser.parse_args()

    if args.mode == "web":
        run_api(args.host, args.port, open_browser=True)
    elif args.mode == "api":
        run_api(args.host, args.port, open_browser=False)
    elif args.mode == "cli":
        run_cli()
    elif args.mode == "full":
        run_full(args.host, args.port)
    else:
        run_doctor_demo()


if __name__ == "__main__":
    main()
