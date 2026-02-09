from __future__ import annotations

import datetime as _dt
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# #region agent log
import os as _os
DEBUG_LOG_PATH = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    ".cursor",
    "debug.log",
)
_os.makedirs(_os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)

def _debug_log(message: str, data: dict, hypothesis_id: str = "H1") -> None:
    try:
        payload = {
            "id": f"log_{int(time.time() * 1000)}",
            "timestamp": int(time.time() * 1000),
            "location": "main.py",
            "message": message,
            "data": data,
            "hypothesisId": hypothesis_id,
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# #endregion

from app.graph import build_graph
from app.logging_setup import configure_logging
from app.schemas import FinalOutput, UserRequest
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    # Checkpointer (SQLite) for durable thread state
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except Exception as e:
        raise RuntimeError(
            "Missing SqliteSaver. Ensure langgraph-checkpoint-sqlite is installed."
        ) from e

    # Keep DB open for the life of the app.
    with SqliteSaver.from_conn_string(settings.CHECKPOINT_DB_PATH) as checkpointer:
        app.state.graph = build_graph(checkpointer=checkpointer)
        yield


app = FastAPI(
    title="MAPIG: Multi-Agent Psychometric Item Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# #region agent log
@app.middleware("http")
async def _debug_request_log(request, call_next):
    response = await call_next(request)
    _debug_log(
        "request_handled",
        {
            "method": request.method,
            "path": request.url.path,
            "origin": request.headers.get("origin"),
            "status_code": response.status_code,
        },
        "H1_H3_H4",
    )
    return response
# #endregion


@app.get("/", include_in_schema=False)
def root():
    """Redirect browser users to API docs so the app 'loads' when opening the backend URL."""
    return RedirectResponse(url="/docs", status_code=302)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "mode": settings.APP_MODE}


@app.post("/v1/generate-items", response_model=FinalOutput)
async def generate_items(
    request: UserRequest,
    x_thread_id: Optional[str] = Header(default=None),
) -> FinalOutput:
    """Generate and review item drafts.

    - Provide X-Thread-ID to resume a thread (checkpointing), or omit to create a new one.
    """
    if not hasattr(app.state, "graph"):
        raise HTTPException(status_code=503, detail="Graph not initialized")

    thread_id = x_thread_id or str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    timestamp_utc = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

    # LangGraph config: thread_id is required for checkpointing.
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,  # hard stop in case of prompt failures
    }

    initial_state = {
        "user_request": request,
        "thread_id": thread_id,
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
    }

    result_state = app.state.graph.invoke(initial_state, config=config)

    if "final_output" not in result_state:
        raise HTTPException(status_code=500, detail="Graph completed without final_output")

    return result_state["final_output"]
