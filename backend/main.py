from __future__ import annotations

import asyncio
import datetime as _dt
import json
import logging
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse

logger = logging.getLogger("lmaig")

from backend.graph import build_graph
from backend.logging_setup import configure_logging
from backend.logging_utils import get_performance_summary
from backend.schemas import FinalOutput, UserRequest
from backend.settings import STANDARD_ITEM_CONSTRAINTS, settings
from backend.evaluation.baseline_runner import run_baseline_comparison, BaselineComparison
from backend.checkpoint_config import create_checkpointer

RUN_STATUS_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Human-readable display names for pipeline nodes (sent via SSE events)
_NODE_DISPLAY_NAMES: Dict[str, str] = {
    "init_run": "Setting up pipeline",
    "retrieve_node": "Searching academic sources",
    "facet_mapper_node": "Mapping construct facets",
    "item_writer_node": "Drafting survey items",
    "validation_node": "Validating item quality",
    "regenerate_items_node": "Improving failed items",
    "reviewers_fanout_node": "Running review panel",
    "content_review_node": "Reviewing construct alignment",
    "linguistic_review_node": "Reviewing language clarity",
    "bias_review_node": "Reviewing bias and fairness",
    "critic_node": "Evaluating review outcomes",
    "meta_editor_node": "Applying reviewer feedback",
    "pfa_pruning_node": "Pruning items via PFA",
    "expert_panel_node": "Expert panel review",
    "expert_revision_node": "Applying expert revisions",
    "finalize_node": "Finalizing results",
    "correlation_node": "Estimating inter-item correlations",
    "comparison_node": "Comparing with published instruments",
    "cross_construct_node": "Analyzing cross-construct validity",
    "analytics_dispatch_node": "Running analytics suite",
}


def _utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def _normalize_request(request: UserRequest) -> UserRequest:
    # Baseline constraints are always active; user constraints are additive.
    merged_constraints: list[str] = []
    for item in [*STANDARD_ITEM_CONSTRAINTS, *(request.constraints or [])]:
        value = (item or "").strip()
        if value and value not in merged_constraints:
            merged_constraints.append(value)
    return request.model_copy(update={"constraints": merged_constraints})


def _set_run_status(thread_id: str, run_id: str, **updates: Any) -> None:
    existing = RUN_STATUS_REGISTRY.get(thread_id, {})
    if not existing:
        existing = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": "running",
            "current_node": None,
            "display_name": None,
            "iteration": 0,
            "error": None,
            "final_output": None,
            "started_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
        }
    existing["thread_id"] = thread_id
    existing["run_id"] = run_id
    existing.update(updates)
    existing["updated_at"] = _utc_now_iso()
    RUN_STATUS_REGISTRY[thread_id] = existing


class _PydanticSerializationFilter(logging.Filter):
    """Suppress cosmetic PydanticSerializationUnexpectedValue log messages.

    The OpenAI SDK's ParsedResponse objects contain 20+ union type variants.
    Pydantic V2 warns when trying each variant during serialization.
    Data parses correctly — these are purely cosmetic noise.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "PydanticSerializationUnexpectedValue" not in record.getMessage()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    # Suppress known harmless Pydantic serialization warnings from OpenAI SDK
    # (documented in CLAUDE.md as cosmetic — data parses correctly)
    import warnings
    warnings.filterwarnings(
        "ignore",
        message="(?s).*PydanticSerializationUnexpectedValue.*",
        category=UserWarning,
    )
    # Also suppress at the logging level — Pydantic may emit via logging
    # rather than the warnings module, causing error-level log noise on Vercel
    _pydantic_logger = logging.getLogger("pydantic")
    _pydantic_logger.addFilter(_PydanticSerializationFilter())

    # Use in-memory checkpointer with registered custom types
    # Checkpoints are ephemeral (lost on cold start) but functional during single run
    # Custom types are pre-registered to eliminate "Deserializing unregistered type" warnings
    # and ensure forward compatibility with future LangGraph versions
    checkpointer = create_checkpointer()
    app.state.graph = build_graph(checkpointer=checkpointer)

    yield
    # No cleanup needed for MemorySaver (in-memory only)


app = FastAPI(
    title="MAPIG: Multi-Agent Psychometric Item Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    # Only this project's Vercel preview deployments — production is same-origin.
    allow_origin_regex=r"https://lmaig-langgraph(-[a-z0-9-]+)?\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generation runs are expensive (many LLM calls); cap concurrent runs and
# reject the overflow with 429 instead of letting them pile onto the budget.
_GENERATION_SLOTS = asyncio.Semaphore(2)


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Optional shared-key gate for generation endpoints (cost-abuse
    protection, not authentication). No-op when MAPIG_API_KEY is unset."""
    expected = settings.MAPIG_API_KEY
    # Compare bytes: compare_digest raises TypeError on non-ASCII str input,
    # which would turn a hostile header into a 500 instead of a 401.
    if expected and not secrets.compare_digest(
        (x_api_key or "").encode("utf-8", "surrogateescape"), expected.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


def _reject_if_at_capacity() -> None:
    if _GENERATION_SLOTS.locked():
        raise HTTPException(
            status_code=429,
            detail="Generation capacity reached (2 concurrent runs). Retry shortly.",
        )


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


@app.get("/v1/runs/{thread_id}/status")
def run_status(thread_id: str):
    state = RUN_STATUS_REGISTRY.get(thread_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run status not found")
    return state


@app.post("/v1/generate-items", response_model=FinalOutput, dependencies=[Depends(require_api_key)])
async def generate_items(
    request: UserRequest,
    x_thread_id: Optional[str] = Header(default=None),
) -> FinalOutput:
    """Generate and review item drafts.

    - Provide X-Thread-ID to resume a thread (checkpointing), or omit to create a new one.
    """
    if not hasattr(app.state, "graph"):
        raise HTTPException(status_code=503, detail="Graph not initialized")
    _reject_if_at_capacity()

    thread_id = x_thread_id or str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    timestamp_utc = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

    # LangGraph config: thread_id is required for checkpointing.
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,  # hard stop in case of prompt failures
    }

    normalized_request = _normalize_request(request)
    initial_state = {
        "user_request": normalized_request,
        "thread_id": thread_id,
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
    }
    _set_run_status(
        thread_id,
        run_id,
        status="running",
        current_node="init_run",
        display_name="Initializing",
        iteration=0,
        error=None,
        final_output=None,
        started_at=timestamp_utc,
    )

    try:
        async with _GENERATION_SLOTS:
            result_state = await app.state.graph.ainvoke(initial_state, config=config)
    except Exception as exc:
        _set_run_status(
            thread_id,
            run_id,
            status="error",
            error=str(exc),
        )
        raise

    if "final_output" not in result_state:
        _set_run_status(
            thread_id,
            run_id,
            status="error",
            error="Graph completed without final_output",
        )
        raise HTTPException(status_code=500, detail="Graph completed without final_output")

    final_output = result_state["final_output"]
    _set_run_status(
        thread_id,
        run_id,
        status="complete",
        current_node="finalize_node",
        display_name="Finalizing",
        final_output=final_output.model_dump(),
        error=None,
    )

    return final_output


@app.post("/v1/generate-items-stream", dependencies=[Depends(require_api_key)])
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
    _reject_if_at_capacity()

    # Validate API key for selected provider
    if request.model_provider == "claude":
        if not settings.CLAUDE_API_KEY:
            raise HTTPException(
                status_code=400,
                detail="CLAUDE_API_KEY not configured. Add to .env or Vercel environment variables, or switch to OpenAI provider."
            )
    elif request.model_provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=400,
                detail="OPENAI_API_KEY not configured. Add to .env or Vercel environment variables."
            )

    # Analytics always need OpenAI for embeddings (correlation + plagiarism detection)
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured — analytics (correlation, comparison) will be skipped")

    thread_id = x_thread_id or str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    timestamp_utc = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()

    # LangGraph config: thread_id is required for checkpointing.
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,  # hard stop in case of prompt failures
    }

    normalized_request = _normalize_request(request)
    initial_state = {
        "user_request": normalized_request,
        "thread_id": thread_id,
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
    }
    _set_run_status(
        thread_id,
        run_id,
        status="running",
        current_node="init_run",
        display_name="Initializing",
        iteration=0,
        error=None,
        final_output=None,
        started_at=timestamp_utc,
    )

    async def event_generator():
        """Generate SSE events as the graph executes.

        The slot is acquired as the generator's first statement: if the client
        aborts before streaming starts, an unstarted generator's body (and its
        finally) never runs, so acquiring outside would leak the slot."""
        await _GENERATION_SLOTS.acquire()
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'run_id': run_id, 'thread_id': thread_id})}\n\n"

            # Track seen nodes globally: (node_name, iteration) tuples
            seen_nodes = set()
            last_iteration = -1
            latest_final_output = None

            # Use astream to get incremental state updates
            # Each event is a dict: {node_name: state_dict}
            async for event in app.state.graph.astream(initial_state, config=config):
                for node_name, node_state in event.items():
                    if node_state is None:
                        continue
                    current_iteration = node_state.get("iteration", 0)

                    # Emit node start event (once per node per iteration)
                    if (node_name, current_iteration) not in seen_nodes:
                        node_display_name = _NODE_DISPLAY_NAMES.get(
                            node_name,
                            node_name.replace("_node", "").replace("_", " ").title(),
                        )
                        _set_run_status(
                            thread_id,
                            run_id,
                            status="running",
                            current_node=node_name,
                            display_name=node_display_name,
                            iteration=current_iteration,
                            error=None,
                        )
                        yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'display_name': node_display_name, 'iteration': current_iteration})}\n\n"
                        seen_nodes.add((node_name, current_iteration))

                        # Add friendly messages for validation nodes
                        if node_name == "validation_node":
                            yield f"data: {json.dumps({'type': 'status', 'message': 'Validating item quality...'})}\n\n"
                        elif node_name == "regenerate_items_node":
                            yield f"data: {json.dumps({'type': 'status', 'message': 'Regenerating low-scoring items...'})}\n\n"

                    # Emit validation results summary after validation_node completes
                    if node_name == "validation_node" and "validation_results" in node_state:
                        validation_results = node_state.get("validation_results", [])
                        failed_count = len([v for v in validation_results if not v.accept])
                        if failed_count > 0:
                            yield f"data: {json.dumps({'type': 'warning', 'message': f'{failed_count} items below quality threshold, regenerating...'})}\n\n"

                    # Emit iteration change event
                    if current_iteration != last_iteration and current_iteration > 0:
                        _set_run_status(
                            thread_id,
                            run_id,
                            status="running",
                            iteration=current_iteration,
                            error=None,
                        )
                        yield f"data: {json.dumps({'type': 'iteration', 'iteration': current_iteration})}\n\n"
                        last_iteration = current_iteration

                    # Track latest final_output (analytics nodes update it after finalize_node)
                    if "final_output" in node_state:
                        latest_final_output = node_state["final_output"]

            # Stream fully consumed — send final output with all analytics data
            if latest_final_output is not None:
                try:
                    dumped = latest_final_output.model_dump(mode="json")
                except Exception:
                    logger.exception("SSE final output model_dump failed")
                    raise
                try:
                    payload = json.dumps({"type": "complete", "data": dumped})
                except Exception:
                    logger.exception("SSE final output json.dumps failed")
                    raise
                _set_run_status(
                    thread_id,
                    run_id,
                    status="complete",
                    current_node="complete",
                    display_name="Complete",
                    final_output=dumped,
                    error=None,
                )
                yield f"data: {payload}\n\n"
            else:
                _set_run_status(
                    thread_id,
                    run_id,
                    status="error",
                    error="Graph completed without final_output",
                )
                yield f"data: {json.dumps({'type': 'error', 'message': 'Graph completed without final_output'})}\n\n"

        except asyncio.CancelledError:
            _set_run_status(
                thread_id,
                run_id,
                status="error",
                error="Client disconnected before completion",
            )
            raise
        except Exception as e:
            error_msg = str(e)
            logger.exception("SSE event_generator failed")
            _set_run_status(
                thread_id,
                run_id,
                status="error",
                error=error_msg,
            )
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        finally:
            _GENERATION_SLOTS.release()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.post("/v1/run-evaluation", tags=["evaluation"], dependencies=[Depends(require_api_key)])
async def run_evaluation(model_provider: str = "claude") -> dict:
    """Run evaluation suite and return baseline comparison results.

    Args:
        model_provider: "claude" or "openai"

    Returns:
        JSON with evaluation metrics and baseline comparison:
        {
          "current": {
            "item_quality_score": 8.2,
            "agent_performance_score": 8.5,
            "workflow_efficiency_score": 8.1,
            "construct_validity_score": 8.3,
            "overall_score": 8.275,
            "total_comparisons": 25
          },
          "baseline": { ... },
          "improvement": {
            "overall_improvement": 18.5,
            "item_quality_improvement": 20.1,
            "agent_performance_improvement": 22.3,
            "workflow_efficiency_improvement": 15.2,
            "construct_validity_improvement": 16.8
          },
          "success_criteria": {
            "meets_improvement_threshold": true,
            "all_dimensions_passing": true,
            "success": true
          }
        }
    """
    _reject_if_at_capacity()
    try:
        async with _GENERATION_SLOTS:
            comparison = await run_baseline_comparison(model_provider)

        return {
            "current": {
                "item_quality_score": comparison.current.item_quality_score,
                "agent_performance_score": comparison.current.agent_performance_score,
                "workflow_efficiency_score": comparison.current.workflow_efficiency_score,
                "construct_validity_score": comparison.current.construct_validity_score,
                "overall_score": comparison.current.overall_score,
                "total_comparisons": comparison.current.total_comparisons
            },
            "baseline": {
                "item_quality_score": comparison.baseline.item_quality_score,
                "agent_performance_score": comparison.baseline.agent_performance_score,
                "workflow_efficiency_score": comparison.baseline.workflow_efficiency_score,
                "construct_validity_score": comparison.baseline.construct_validity_score,
                "overall_score": comparison.baseline.overall_score,
                "total_comparisons": comparison.baseline.total_comparisons
            },
            "improvement": {
                "overall_improvement": comparison.overall_improvement,
                "item_quality_improvement": comparison.item_quality_improvement,
                "agent_performance_improvement": comparison.agent_performance_improvement,
                "workflow_efficiency_improvement": comparison.workflow_efficiency_improvement,
                "construct_validity_improvement": comparison.construct_validity_improvement
            },
            "success_criteria": {
                "meets_improvement_threshold": comparison.meets_improvement_threshold,
                "all_dimensions_passing": comparison.all_dimensions_passing,
                "success": comparison.success
            }
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Evaluation suite failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
