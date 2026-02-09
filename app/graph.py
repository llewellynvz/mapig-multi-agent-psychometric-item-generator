from __future__ import annotations
import logging

import concurrent.futures
import datetime as _dt
import uuid
from typing import List, Literal, Optional

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from app.agents.bias_reviewer import review_bias
from app.agents.critic import decide as critic_decide
from app.agents.item_writer import write_items
from app.agents.linguistic_reviewer import review_linguistic
from app.agents.meta_editor import revise_items
from app.agents.retrieval_agent import retrieve_evidence
from app.schemas import (
    AuditMetadata,
    DraftItem,
    EvidenceChunk,
    FinalOutput,
    ReviewComment,
    RevisionPlan,
    UserRequest,
)
from app.settings import settings
from app.logging_utils import step
from app.agents.web_surfer import surf as web_surf
from app.agents.content_reviewer import review_content

logger = logging.getLogger("lmaig")


class GraphState(TypedDict, total=False):
    # Inputs / identifiers
    user_request: UserRequest
    thread_id: str
    run_id: str
    timestamp_utc: str

    # Working artifacts
    evidence: List[EvidenceChunk]
    draft_items: List[DraftItem]
    linguistic_comments: List[ReviewComment]
    bias_comments: List[ReviewComment]
    content_comments: List[ReviewComment]
    revision_plan: Optional[RevisionPlan]


    # Control
    iteration: int
    stop_reason: str

    # Output
    final_output: FinalOutput


def _utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def init_run(state: GraphState) -> GraphState:
    """Initialize control fields."""
    with step("init_run", state):
        return {
            "iteration": 0,
            "stop_reason": "",
            "linguistic_comments": [],
            "bias_comments": [],
            "content_comments": [],
            "revision_plan": None,
            "timestamp_utc": state.get("timestamp_utc") or _utc_now(),
            "run_id": state.get("run_id") or str(uuid.uuid4()),
        }


def retrieve_node(state: GraphState) -> GraphState:
    with step("retrieve_node", state):
        # Local sources
        resp = retrieve_evidence(state["user_request"])
        evidence = list(resp.evidence)

        # Perplexity evidence (optional)
        if settings.SEARCH_PROVIDER in {"perplexity", "hybrid"}:
            pplx = web_surf(state["user_request"])
            # dedupe by url
            seen = {e.url_or_docref for e in evidence}
            for e in pplx.evidence:
                if e.url_or_docref not in seen:
                    evidence.append(e)
                    seen.add(e.url_or_docref)
        return {"evidence": evidence}


def item_writer_node(state: GraphState) -> GraphState:
    with step("item_writer_node", state):
        resp = write_items(state["user_request"], state.get("evidence", []))
        return {"draft_items": resp.items}


def linguistic_review_node(state: GraphState) -> GraphState:
    with step("linguistic_review_node", state):
        resp = review_linguistic(
            state["user_request"],
            state.get("draft_items", []),
            iteration=state.get("iteration", 0),
        )
        return {"linguistic_comments": resp.comments}


def bias_review_node(state: GraphState) -> GraphState:
    with step("bias_review_node", state):
        resp = review_bias(
            state["user_request"],
            state.get("draft_items", []),
            iteration=state.get("iteration", 0),
        )
        return {"bias_comments": resp.comments}

def content_review_node(state: GraphState) -> GraphState:
    with step("content_review_node", state):
        resp = review_content(
            state["user_request"],
            state.get("draft_items", []),
            iteration=state.get("iteration", 0),
        )
        logger.info("content_review comments=%d", len(resp.comments))
        return {"content_comments": resp.comments}


def reviewers_fanout_node(state: GraphState) -> GraphState:
    """Run all three reviewers in parallel."""
    with step("reviewers_fanout_node", state):
        user_request = state["user_request"]
        draft_items = state.get("draft_items", [])
        iteration = state.get("iteration", 0)

        # Run all three reviewers concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            content_future = executor.submit(
                review_content, user_request, draft_items, iteration
            )
            linguistic_future = executor.submit(
                review_linguistic, user_request, draft_items, iteration
            )
            bias_future = executor.submit(
                review_bias, user_request, draft_items, iteration
            )

            # Wait for all to complete and get results
            content_resp = content_future.result()
            linguistic_resp = linguistic_future.result()
            bias_resp = bias_future.result()

        logger.info(
            "reviewers_fanout: content=%d linguistic=%d bias=%d",
            len(content_resp.comments),
            len(linguistic_resp.comments),
            len(bias_resp.comments),
        )

        return {
            "content_comments": content_resp.comments,
            "linguistic_comments": linguistic_resp.comments,
            "bias_comments": bias_resp.comments,
        }


def critic_node(state: GraphState) -> Command[Literal["meta_editor_node", "finalize_node"]]:
    decision, reason = critic_decide(
        linguistic_comments=state.get("linguistic_comments", []),
        bias_comments=state.get("bias_comments", []),
        content_comments=state.get("content_comments", []),
        iteration=state.get("iteration", 0),
    )

    if decision == "revise":
        return Command(
            update={
                "stop_reason": reason,
                "iteration": state.get("iteration", 0) + 1,
            },
            goto="meta_editor_node",
        )

    # accept / stop_max_iterations / needs_human all end the loop
    return Command(
        update={"stop_reason": reason},
        goto="finalize_node",
    )


def meta_editor_node(state: GraphState) -> GraphState:
    with step("meta_editor_node", state):
        resp = revise_items(
            request=state["user_request"],
            items=state.get("draft_items", []),
            linguistic_comments=state.get("linguistic_comments", []),
            bias_comments=state.get("bias_comments", []),
            content_comments=state.get("content_comments", []),
            iteration=state.get("iteration", 0),
        )

        return {
            "draft_items": resp.revised_items,
            "revision_plan": resp.revision_plan,
            # Clear comments so each iteration reflects current draft only.
            "linguistic_comments": [],
            "bias_comments": [],
            "content_comments": [],
        }


def finalize_node(state: GraphState) -> GraphState:
    # Collect allowlisted sources used (doc refs or urls)
    with step("finalize_node", state):
        approved_sources = []
        for e in state.get("evidence", []):
            if e.url_or_docref not in approved_sources:
                approved_sources.append(e.url_or_docref)

        model_info = {"mode": settings.APP_MODE}
        if settings.APP_MODE == "azure":
            model_info.update(
                {
                    "azure_deployment": settings.AZURE_OPENAI_DEPLOYMENT,
                    "api_version": settings.AZURE_OPENAI_API_VERSION,
                    "endpoint": settings.AZURE_OPENAI_ENDPOINT,
                }
            )

        audit = AuditMetadata(
            thread_id=state.get("thread_id", "unknown"),
            run_id=state.get("run_id", "unknown"),
            timestamp_utc=state.get("timestamp_utc", _utc_now()),
            iteration_count=state.get("iteration", 0),
            stop_reason=state.get("stop_reason", ""),
            model_info=model_info,
            approved_sources=approved_sources,
        )

        out = FinalOutput(final_items=state.get("draft_items", []), audit=audit)
        return {"final_output": out}


def build_graph(checkpointer=None):
    """Build and compile the LangGraph workflow."""
    builder = StateGraph(GraphState)

    builder.add_node("init_run", init_run)
    builder.add_node("retrieve_node", retrieve_node)
    builder.add_node("item_writer_node", item_writer_node)
    # Keep individual reviewer nodes for backward compatibility if needed
    builder.add_node("content_review_node", content_review_node)
    builder.add_node("linguistic_review_node", linguistic_review_node)
    builder.add_node("bias_review_node", bias_review_node)
    # New parallel reviewers node
    builder.add_node("reviewers_fanout_node", reviewers_fanout_node)
    builder.add_node("critic_node", critic_node)
    builder.add_node("meta_editor_node", meta_editor_node)
    builder.add_node("finalize_node", finalize_node)

    builder.add_edge(START, "init_run")
    builder.add_edge("init_run", "retrieve_node")
    builder.add_edge("retrieve_node", "item_writer_node")
    # Use parallel reviewers instead of sequential
    builder.add_edge("item_writer_node", "reviewers_fanout_node")
    builder.add_edge("reviewers_fanout_node", "critic_node")

    # Critic routes to either meta-editor (revise) or finalize (end)
    # Meta-editor loops back into parallel reviewers.
    builder.add_edge("meta_editor_node", "reviewers_fanout_node")
    builder.add_edge("finalize_node", END)

    return builder.compile(checkpointer=checkpointer)
