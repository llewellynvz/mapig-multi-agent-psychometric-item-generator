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
    ItemValidation,
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
    validation_results: List[ItemValidation]
    validation_attempt: int
    failed_item_indices: List[int]

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
            "validation_results": [],
            "validation_attempt": 1,
            "failed_item_indices": [],
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


def validation_node(state: GraphState) -> GraphState:
    """Validate draft items with LLM-as-judge scoring."""
    with step("validation_node", state):
        from app.agents.validator import validate_items

        draft_items = state.get("draft_items", [])
        attempt = state.get("validation_attempt", 1)

        resp = validate_items(
            request=state["user_request"],
            items=draft_items,
            attempt=attempt
        )

        return {"validation_results": resp.validations}


def route_after_validation(state: GraphState) -> Command[Literal["regenerate_items_node", "reviewers_fanout_node"]]:
    """Route based on validation results."""
    validation_results = state.get("validation_results", [])

    # Check for failed items
    failed = [v for v in validation_results if not v.accept]
    max_attempts = 3
    current_attempt = state.get("validation_attempt", 1)

    if not failed:
        # All items passed
        logger.info("Validation passed: all items scored >= 7.0")
        return Command(goto="reviewers_fanout_node")

    if current_attempt >= max_attempts:
        # Max retries exhausted; accept best available
        logger.warning(f"Validation max retries ({max_attempts}) exhausted. Accepting best-scoring items.")
        return Command(goto="reviewers_fanout_node")

    # Route to regeneration
    logger.info(f"Validation failed: {len(failed)} items below threshold. Attempt {current_attempt}/{max_attempts}")
    return Command(
        update={
            "validation_attempt": current_attempt + 1,
            "failed_item_indices": [v.item_index for v in failed]
        },
        goto="regenerate_items_node"
    )


def regenerate_items_node(state: GraphState) -> GraphState:
    """Regenerate only items that failed validation."""
    with step("regenerate_items_node", state):
        from app.agents.item_writer import write_items

        validation_results = state.get("validation_results", [])
        draft_items = state.get("draft_items", [])
        failed_indices = state.get("failed_item_indices", [])

        # Get validation feedback for failed items
        failed_validations = [v for v in validation_results if not v.accept]

        # Build feedback context for Item Writer
        feedback_text = "Previous items failed validation:\n"
        for v in failed_validations:
            feedback_text += f"\nItem {v.item_index}: {v.item_text}\n"
            for dim_score in v.dimension_scores:
                feedback_text += f"  - {dim_score.dimension} ({dim_score.score}/10): {dim_score.reasoning}\n"

        # Create modified request with feedback
        modified_request = state["user_request"].model_copy(deep=True)
        modified_request.human_feedback = feedback_text
        modified_request.previous_items = [draft_items[i].item_text for i in failed_indices]
        modified_request.item_count = len(failed_indices)

        # Regenerate failed items
        resp = write_items(modified_request, state.get("evidence", []))

        # Merge: keep accepted items, replace failed items
        merged_items = draft_items.copy()
        for idx, new_item in zip(failed_indices, resp.items):
            merged_items[idx] = new_item

        return {"draft_items": merged_items}


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

        # Attach validation results to items
        draft_items = state.get("draft_items", [])
        validation_results = state.get("validation_results", [])

        # Create lookup dict for validation results
        validation_lookup = {v.item_index: v for v in validation_results}

        # Enrich items with validation data
        enriched_items = []
        for idx, item in enumerate(draft_items):
            # Copy item and attach validation result if available
            enriched_item = item.model_copy(deep=True)
            if idx in validation_lookup:
                enriched_item.validation_result = validation_lookup[idx]
            enriched_items.append(enriched_item)

        model_info = {"mode": settings.APP_MODE}
        if settings.APP_MODE == "azure":
            model_info.update(
                {
                    "azure_deployment": settings.AZURE_OPENAI_DEPLOYMENT,
                    "api_version": settings.AZURE_OPENAI_API_VERSION,
                    "endpoint": settings.AZURE_OPENAI_ENDPOINT,
                }
            )

        # Update audit with validation metadata
        audit = AuditMetadata(
            thread_id=state.get("thread_id", "unknown"),
            run_id=state.get("run_id", "unknown"),
            timestamp_utc=state.get("timestamp_utc", _utc_now()),
            iteration_count=state.get("iteration", 0),
            stop_reason=state.get("stop_reason", ""),
            model_info=model_info,
            approved_sources=approved_sources,
            validation_attempts=state.get("validation_attempt", 1),
            validation_failures=len([v for v in validation_results if not v.accept]),
        )

        out = FinalOutput(final_items=enriched_items, audit=audit)
        return {"final_output": out}


def build_graph(checkpointer=None):
    """Build and compile the LangGraph workflow."""
    builder = StateGraph(GraphState)

    builder.add_node("init_run", init_run)
    builder.add_node("retrieve_node", retrieve_node)
    builder.add_node("item_writer_node", item_writer_node)
    builder.add_node("validation_node", validation_node)
    builder.add_node("regenerate_items_node", regenerate_items_node)
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

    # Validation gate BEFORE reviewers
    builder.add_edge("item_writer_node", "validation_node")
    builder.add_conditional_edges(
        "validation_node",
        route_after_validation
    )

    # Regeneration loops back to validation
    builder.add_edge("regenerate_items_node", "validation_node")

    # Use parallel reviewers instead of sequential
    builder.add_edge("reviewers_fanout_node", "critic_node")

    # Critic routes to either meta-editor (revise) or finalize (end)
    # Meta-editor loops back into parallel reviewers.
    builder.add_edge("meta_editor_node", "reviewers_fanout_node")
    builder.add_edge("finalize_node", END)

    return builder.compile(checkpointer=checkpointer)
