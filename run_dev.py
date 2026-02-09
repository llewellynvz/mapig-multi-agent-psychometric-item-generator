from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"


def kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.kill(pid, 15)
        except ProcessLookupError:
            pass


def main() -> int:
    backend_host = os.environ.get("BACKEND_HOST", "127.0.0.1")
    backend_port = os.environ.get("BACKEND_PORT", "8000")
    frontend_port = os.environ.get("FRONTEND_PORT", "3000")

    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        print("Could not find npm on PATH.", file=sys.stderr)
        return 1

    uvicorn_bin = shutil.which("uvicorn")
    if uvicorn_bin:
        backend_cmd = [
            uvicorn_bin,
            "app.main:app",
            "--reload",
            "--host",
            backend_host,
            "--port",
            backend_port,
        ]
    else:
        try:
            import uvicorn  # noqa: F401
        except Exception:
            print(
                "Could not find uvicorn. Activate your virtual environment or install backend dependencies.",
                file=sys.stderr,
            )
            return 1
        backend_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            backend_host,
            "--port",
            backend_port,
        ]

    frontend_cmd = [npm, "run", "dev", "--", "--port", frontend_port]

    print(f"Starting backend on http://{backend_host}:{backend_port}")
    backend = subprocess.Popen(backend_cmd, cwd=str(ROOT))

    print(f"Starting frontend on http://localhost:{frontend_port}")
    frontend = subprocess.Popen(frontend_cmd, cwd=str(FRONTEND_DIR))

    try:
        while True:
            if backend.poll() is not None:
                kill_tree(frontend.pid)
                return backend.returncode or 0
            if frontend.poll() is not None:
                kill_tree(backend.pid)
                return frontend.returncode or 0
            time.sleep(0.25)
    except KeyboardInterrupt:
        kill_tree(backend.pid)
        kill_tree(frontend.pid)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
