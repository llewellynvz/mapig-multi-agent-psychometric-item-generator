from __future__ import annotations

import asyncio
import datetime as _dt
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse

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
from app.logging_utils import get_performance_summary
from app.schemas import FinalOutput, UserRequest
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    # Checkpointer (SQLite) for durable thread state
    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    except Exception as e:
        raise RuntimeError(
            "Missing AsyncSqliteSaver. Ensure langgraph-checkpoint-sqlite and aiosqlite are installed."
        ) from e

    # Keep DB open for the life of the app.
    async with AsyncSqliteSaver.from_conn_string(settings.CHECKPOINT_DB_PATH) as checkpointer:
        app.state.graph = build_graph(checkpointer=checkpointer)
        yield


app = FastAPI(
    title="MAPIG: Multi-Agent Psychometric Item Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
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


@app.get("/v1/performance-summary")
def performance_summary():
    """Get performance statistics for all agent steps."""
    return get_performance_summary()


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


@app.post("/v1/generate-items-stream")
async def generate_items_stream(
    request: UserRequest,
    x_thread_id: Optional[str] = Header(default=None),
):
    """Generate and review item drafts with Server-Sent Events streaming.

    - Provide X-Thread-ID to resume a thread (checkpointing), or omit to create a new one.
    - Returns SSE stream with progress updates and final result.
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

    async def event_generator():
        """Generate SSE events as the graph executes."""
        # #region agent log
        import os as _os
        DEBUG_LOG_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), ".cursor", "debug.log")
        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": f"log_{int(time.time() * 1000)}", "timestamp": int(time.time() * 1000), "location": "main.py:event_generator", "message": "SSE generator started", "data": {"thread_id": thread_id, "run_id": run_id}, "hypothesisId": "H1_H2_H3_H4_H5"}) + "\n")
        except Exception:
            pass
        # #endregion
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'run_id': run_id, 'thread_id': thread_id})}\n\n"
            # #region agent log
            try:
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"id": f"log_{int(time.time() * 1000)}", "timestamp": int(time.time() * 1000), "location": "main.py:event_generator", "message": "Initial SSE event sent", "data": {}, "hypothesisId": "H1_H2_H3_H4_H5"}) + "\n")
            except Exception:
                pass
            # #endregion

            # Track seen nodes per iteration
            seen_in_iteration = {}  # {iteration: set of nodes}
            last_iteration = -1
            final_output_sent = False

            # Check if graph has astream method
            # #region agent log
            has_astream = hasattr(app.state.graph, 'astream')
            try:
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"id": f"log_{int(time.time() * 1000)}", "timestamp": int(time.time() * 1000), "location": "main.py:event_generator", "message": "Checking graph.astream availability", "data": {"has_astream": has_astream, "graph_type": str(type(app.state.graph))}, "hypothesisId": "H1"}) + "\n")
            except Exception:
                pass
            # #endregion

            # Use astream to get incremental state updates
            # Each event is a dict: {node_name: state_dict}
            async for event in app.state.graph.astream(initial_state, config=config):
                # #region agent log
                try:
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"id": f"log_{int(time.time() * 1000)}", "timestamp": int(time.time() * 1000), "location": "main.py:event_generator", "message": "Received astream event", "data": {"event_keys": list(event.keys()) if isinstance(event, dict) else "not_dict"}, "hypothesisId": "H1_H2"}) + "\n")
                except Exception:
                    pass
                # #endregion
                for node_name, node_state in event.items():
                    current_iteration = node_state.get("iteration", 0)
                    
                    # Initialize iteration tracking
                    if current_iteration not in seen_in_iteration:
                        seen_in_iteration[current_iteration] = set()
                    
                    # Emit node start event (once per node per iteration)
                    if node_name not in seen_in_iteration[current_iteration]:
                        node_display_name = node_name.replace("_node", "").replace("_", " ").title()
                        yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'display_name': node_display_name, 'iteration': current_iteration})}\n\n"
                        seen_in_iteration[current_iteration].add(node_name)

                    # Emit iteration change event
                    if current_iteration != last_iteration and current_iteration > 0:
                        yield f"data: {json.dumps({'type': 'iteration', 'iteration': current_iteration})}\n\n"
                        last_iteration = current_iteration

                    # Check for final output
                    if "final_output" in node_state and not final_output_sent:
                        final_output = node_state["final_output"]
                        yield f"data: {json.dumps({'type': 'complete', 'data': final_output.model_dump()})}\n\n"
                        final_output_sent = True
                        return

            # Fallback: if stream ended without final_output, invoke synchronously
            if not final_output_sent:
                result_state = await asyncio.to_thread(app.state.graph.invoke, initial_state, config)
                if "final_output" in result_state:
                    yield f"data: {json.dumps({'type': 'complete', 'data': result_state['final_output'].model_dump()})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Graph completed without final_output'})}\n\n"

        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            # #region agent log
            try:
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"id": f"log_{int(time.time() * 1000)}", "timestamp": int(time.time() * 1000), "location": "main.py:event_generator", "message": "Exception in SSE generator", "data": {"error": error_msg, "error_type": type(e).__name__, "trace": error_trace}, "hypothesisId": "H1_H2_H3_H4_H5"}) + "\n")
            except Exception:
                pass
            # #endregion
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg, 'trace': error_trace})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
