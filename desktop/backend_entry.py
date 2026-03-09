from __future__ import annotations

import multiprocessing
import os

import uvicorn

from app.main import app


def main() -> None:
    multiprocessing.freeze_support()
    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()

