from __future__ import annotations

import datetime as _dt
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException

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
