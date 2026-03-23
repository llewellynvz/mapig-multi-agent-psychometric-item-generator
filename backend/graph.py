from __future__ import annotations
import logging

import asyncio
import concurrent.futures
import datetime as _dt
import uuid
from typing import List, Literal, Optional

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from backend.agents.sanitizer import sanitize_user_request
from backend.agents.bias_reviewer import review_bias
from backend.agents.critic import decide as critic_decide
from backend.agents.item_writer import write_items
from backend.agents.linguistic_reviewer import review_linguistic
from backend.agents.meta_editor import revise_items
from backend.agents.retrieval_agent import retrieve_evidence
from backend.agents.llm_utils import TokenUsage
from backend.schemas import (
    AbbreviatedRequest,
    AuditMetadata,
    DimensionScore,
    DraftItem,
    EvidenceChunk,
    FacetMapperResponse,
    FinalOutput,
    IterationSnapshot,
    ItemValidation,
    MetaEditorResponse,
    ReviewComment,
    RevisionPlan,
    UserRequest,
    ValidationResponse,
)
from backend.settings import settings
from backend.logging_utils import step
from backend.agents.web_surfer import surf as web_surf
from backend.agents.content_reviewer import review_content

logger = logging.getLogger("lmaig")


def _accumulate_tokens(state: GraphState, usage: TokenUsage) -> dict:
    """Accumulate token usage into appropriate GraphState counters.

    Args:
        state: Current graph state
        usage: Token usage from LLM call

    Returns:
        Dict with updated token counters
    """
    model_name = usage.model_name.lower()
    opus_tokens = state.get("opus_tokens_used", 0)
    sonnet_tokens = state.get("sonnet_tokens_used", 0)
    openai_tokens = state.get("openai_tokens_used", 0)
    chatgpt_tokens = state.get("chatgpt_tokens_used", 0)
    gpt52_tokens = state.get("gpt52_tokens_used", 0)
    gpt52_reasoning = state.get("gpt52_reasoning_tokens", 0)
    gpt52_output = state.get("gpt52_output_tokens", 0)

    # Phase 7: GPT-5.2 routing with separate reasoning tracking
    if "gpt-5.2" in model_name:
        gpt52_tokens += usage.total_tokens
        gpt52_reasoning += getattr(usage, "reasoning_tokens", 0)
        gpt52_output += usage.output_tokens
    elif "opus" in model_name:
        opus_tokens += usage.total_tokens
    elif "sonnet" in model_name or "claude" in model_name:
        sonnet_tokens += usage.total_tokens
    elif "gpt-4o" in model_name and "mini" not in model_name:
        # GPT-4o (not mini) - used for ChatGPT critics toggle
        chatgpt_tokens += usage.total_tokens
    elif "gpt" in model_name or "openai" in model_name:
        # Other OpenAI models (e.g., GPT-4o-mini from overrides)
        openai_tokens += usage.total_tokens
    else:
        # Unknown model - add to sonnet as fallback
        sonnet_tokens += usage.total_tokens

    return {
        "opus_tokens_used": opus_tokens,
        "sonnet_tokens_used": sonnet_tokens,
        "openai_tokens_used": openai_tokens,
        "chatgpt_tokens_used": chatgpt_tokens,
        "gpt52_tokens_used": gpt52_tokens,
        "gpt52_reasoning_tokens": gpt52_reasoning,
        "gpt52_output_tokens": gpt52_output,
    }


def _should_validate_items(
    linguistic_comments: List[ReviewComment],
    bias_comments: List[ReviewComment],
    content_comments: List[ReviewComment],
) -> bool:
    """Decide if full Opus validation is needed based on review feedback.

    Cost optimization: Skip expensive Opus validation when items clearly pass reviews.

    Args:
        linguistic_comments: Linguistic reviewer feedback
        bias_comments: Bias reviewer feedback
        content_comments: Content reviewer feedback

    Returns:
        True if validation needed, False to skip
    """
    all_comments = linguistic_comments + bias_comments + content_comments

    # No comments at all → skip validation (items are clean!)
    if len(all_comments) == 0:
        logger.info("Smart validation: No review comments → skipping Opus validation (cost savings!)")
        return False

    # Only minor comments (severity ≤ 2) → skip validation
    max_severity = max((c.severity for c in all_comments), default=0)
    if max_severity <= 2:
        logger.info(f"Smart validation: Only minor issues (max severity {max_severity}) → skipping Opus validation")
        return False

    # High-severity issues (≥ 3) → full validation required
    logger.info(f"Smart validation: {len(all_comments)} comments with max severity {max_severity} → running Opus validation")
    return True


class GraphState(TypedDict, total=False):
    # Inputs / identifiers
    user_request: UserRequest
    thread_id: str
    run_id: str
    timestamp_utc: str

    # Working artifacts
    evidence: List[EvidenceChunk]
    facet_mapping: Optional[FacetMapperResponse]
    draft_items: List[DraftItem]
    linguistic_comments: List[ReviewComment]
    bias_comments: List[ReviewComment]
    content_comments: List[ReviewComment]
    revision_plan: Optional[RevisionPlan]
    validation_results: List[ItemValidation]
    validation_attempt: int
    failed_item_indices: List[int]

    # Comment history across iterations
    iteration_history: List[IterationSnapshot]

    # Control
    iteration: int
    stop_reason: str

    # Cost tracking (accumulated during run)
    opus_tokens_used: int
    sonnet_tokens_used: int
    openai_tokens_used: int
    chatgpt_tokens_used: int
    # Phase 7: GPT-5.2 token tracking
    gpt52_tokens_used: int
    gpt52_reasoning_tokens: int
    gpt52_output_tokens: int
    # Phase 10: Whether GPT-5.2 is enabled for analytics
    gpt52_analytics_enabled: bool

    # Output
    final_output: FinalOutput


def _utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def _create_abbreviated_request(
    full_request: UserRequest,
    evidence: List[EvidenceChunk] | None = None,
) -> AbbreviatedRequest:
    """Create abbreviated request for reviewers (cost optimization).

    Reviewers don't need: evidence, examples, neighbors, retrieval settings, feedback.
    Reduces payload size by ~60% (~500-800 tokens per reviewer call).

    Args:
        full_request: Complete UserRequest with all fields
        evidence: Optional evidence list to extract cultural context from

    Returns:
        AbbreviatedRequest with only essential fields for review
    """
    # Extract cultural context notes from evidence if available
    cultural_notes = None
    if evidence and full_request.cultural_group:
        cultural_chunks = [
            e.snippet for e in evidence if e.evidence_type == "cultural_context"
        ]
        if cultural_chunks:
            cultural_notes = " ".join(cultural_chunks)

    return AbbreviatedRequest(
        construct_name=full_request.construct_name,
        construct_definition=full_request.construct_definition,
        target_population=full_request.target_population,
        cultural_group=full_request.cultural_group,
        response_scale=full_request.response_scale,
        constraints=full_request.constraints,
        construct_exclusions=full_request.construct_exclusions,
        model_provider=full_request.model_provider,
        use_chatgpt_critics=full_request.use_chatgpt_critics,
        cultural_context_notes=cultural_notes,
    )


def init_run(state: GraphState) -> GraphState:
    """Initialize control fields."""
    with step("init_run", state):
        # Sanitize user inputs before any prompt interpolation
        sanitize_user_request(state["user_request"])

        return {
            "iteration": 0,
            "stop_reason": "",
            "linguistic_comments": [],
            "bias_comments": [],
            "content_comments": [],
            "iteration_history": [],
            "revision_plan": None,
            "validation_results": [],
            "validation_attempt": 1,
            "failed_item_indices": [],
            "timestamp_utc": state.get("timestamp_utc") or _utc_now(),
            "run_id": state.get("run_id") or str(uuid.uuid4()),
            "opus_tokens_used": 0,
            "sonnet_tokens_used": 0,
            "openai_tokens_used": 0,
            "chatgpt_tokens_used": 0,
            "gpt52_tokens_used": 0,
            "gpt52_reasoning_tokens": 0,
            "gpt52_output_tokens": 0,
            "gpt52_analytics_enabled": state.get("user_request").use_gpt52_analytics if state.get("user_request") and hasattr(state.get("user_request"), "use_gpt52_analytics") else False,
        }


def retrieve_node(state: GraphState) -> GraphState:
    with step("retrieve_node", state):
        # Local sources
        resp = retrieve_evidence(state["user_request"])
        evidence = list(resp.evidence)

        # Perplexity evidence (optional)
        local_count = len(evidence)

        if settings.SEARCH_PROVIDER in {"perplexity", "hybrid"}:
            pplx = web_surf(state["user_request"])
            # dedupe by source_id (not url — same URL can have multiple distinct evidence chunks)
            seen = {e.source_id for e in evidence}
            for e in pplx.evidence:
                if e.source_id not in seen:
                    evidence.append(e)
                    seen.add(e.source_id)

        web_count = len(evidence) - local_count
        logger.info(f"EVIDENCE_DEPTH total={len(evidence)} web={web_count} local={local_count}")
        if len(evidence) < 20:
            logger.warning(f"EVIDENCE_DEPTH_WARNING total={len(evidence)} (minimum recommended: 20)")
        return {"evidence": evidence}


def _check_item_diversity(items: List[DraftItem]) -> None:
    """Log a warning if generated items are too semantically similar.

    Uses OpenAI text-embedding-3-small (already available) to compute
    pairwise cosine similarity.  Non-blocking — warning only.
    """
    if len(items) < 3:
        return
    try:
        from openai import OpenAI
        import numpy as np
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
        )
        texts = [it.item_text for it in items]
        resp = client.embeddings.create(input=texts, model="text-embedding-3-small")
        vecs = np.array([d.embedding for d in resp.data])
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normed = vecs / norms
        sim = normed @ normed.T
        # Mean of upper-triangular (excluding diagonal)
        n = len(texts)
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append(sim[i, j])
        mean_sim = float(np.mean(pairs))
        if mean_sim > 0.80:
            logger.warning(
                "ITEM_HOMOGENEITY_WARNING mean_pairwise_similarity=%.3f (threshold=0.80). "
                "Items may be synonym variations rather than diverse facets.",
                mean_sim,
            )
        else:
            logger.info("Item diversity check passed: mean_similarity=%.3f", mean_sim)
    except Exception as e:
        logger.debug("Item diversity check skipped: %s", e)


def facet_mapper_node(state: GraphState) -> GraphState:
    """Map construct facets from evidence before item generation."""
    with step("facet_mapper_node", state):
        from backend.agents.facet_mapper import map_facets

        resp, usage = map_facets(state["user_request"], state.get("evidence", []))
        token_update = _accumulate_tokens(state, usage)

        return {
            "facet_mapping": resp,
            **token_update,
        }


def item_writer_node(state: GraphState) -> GraphState:
    with step("item_writer_node", state):
        resp, usage = write_items(
            state["user_request"],
            state.get("evidence", []),
            facet_mapping=state.get("facet_mapping"),
        )
        token_update = _accumulate_tokens(state, usage)

        # Non-blocking diversity check (warning only)
        if settings.APP_MODE != "mock" and resp is not None:
            _check_item_diversity(resp.items)

        return {
            "draft_items": resp.items,
            **token_update,
        }


def validation_node(state: GraphState) -> Command[Literal["regenerate_items_node", "reviewers_fanout_node"]]:
    """Validate draft items with LLM-as-judge scoring and route based on results."""
    with step("validation_node", state):
        from backend.agents.validator import validate_items

        draft_items = state.get("draft_items", [])
        attempt = state.get("validation_attempt", 1)

        try:
            resp, usage = validate_items(
                request=state["user_request"],
                items=draft_items,
                attempt=attempt
            )
        except Exception as e:
            logger.error(f"VALIDATION error={e}. Force-accepting all items.")
            resp = ValidationResponse(validations=[
                ItemValidation(
                    item_index=i,
                    item_text=item.item_text,
                    dimension_scores=[
                        DimensionScore(dimension="correspondence", reasoning="", score=7),
                        DimensionScore(dimension="distinctiveness", reasoning="", score=7),
                        DimensionScore(dimension="clarity", reasoning="", score=7),
                        DimensionScore(dimension="specificity", reasoning="", score=7),
                    ],
                    weighted_score=7.0,
                    accept=True,
                    attempt=attempt,
                )
                for i, item in enumerate(draft_items)
            ])
            usage = TokenUsage(model_name="fallback")

        # Accumulate token usage
        token_update = _accumulate_tokens(state, usage)

        # Store validation results and determine routing
        validation_results = resp.validations
        failed = [v for v in validation_results if not v.accept]
        max_attempts = 3

        if not failed:
            # All items passed
            logger.info("Validation passed: all items scored >= 7.0")
            return Command(
                update={
                    "validation_results": validation_results,
                    **token_update,
                },
                goto="reviewers_fanout_node"
            )

        if attempt >= max_attempts:
            # Max retries exhausted; accept best available
            logger.warning(f"Validation max retries ({max_attempts}) exhausted. Accepting best-scoring items.")
            return Command(
                update={
                    "validation_results": validation_results,
                    **token_update,
                },
                goto="reviewers_fanout_node"
            )

        # Route to regeneration
        logger.info(f"Validation failed: {len(failed)} items below threshold. Attempt {attempt}/{max_attempts}")
        return Command(
            update={
                "validation_results": validation_results,
                "validation_attempt": attempt + 1,
                "failed_item_indices": [v.item_index for v in failed],
                **token_update,
            },
            goto="regenerate_items_node"
        )


def regenerate_items_node(state: GraphState) -> GraphState:
    """Regenerate only items that failed validation."""
    with step("regenerate_items_node", state):
        from backend.agents.item_writer import write_items

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
        resp, usage = write_items(modified_request, state.get("evidence", []))
        token_update = _accumulate_tokens(state, usage)

        # Merge: keep accepted items, replace failed items
        merged_items = draft_items.copy()
        for idx, new_item in zip(failed_indices, resp.items):
            merged_items[idx] = new_item

        return {
            "draft_items": merged_items,
            **token_update,
        }


def linguistic_review_node(state: GraphState) -> GraphState:
    with step("linguistic_review_node", state):
        resp, usage = review_linguistic(
            state["user_request"],
            state.get("draft_items", []),
            iteration=state.get("iteration", 0),
        )
        token_update = _accumulate_tokens(state, usage)
        return {
            "linguistic_comments": resp.comments,
            **token_update,
        }


def bias_review_node(state: GraphState) -> GraphState:
    with step("bias_review_node", state):
        resp, usage = review_bias(
            state["user_request"],
            state.get("draft_items", []),
            iteration=state.get("iteration", 0),
        )
        token_update = _accumulate_tokens(state, usage)
        return {
            "bias_comments": resp.comments,
            **token_update,
        }

def content_review_node(state: GraphState) -> GraphState:
    with step("content_review_node", state):
        resp, usage = review_content(
            state["user_request"],
            state.get("draft_items", []),
            iteration=state.get("iteration", 0),
        )
        token_update = _accumulate_tokens(state, usage)
        logger.info("content_review comments=%d", len(resp.comments))
        return {
            "content_comments": resp.comments,
            **token_update,
        }


def reviewers_fanout_node(state: GraphState) -> GraphState:
    """Run all three reviewers in parallel with abbreviated request.

    Cost optimization: Uses AbbreviatedRequest to reduce payload size by ~60%
    (~500-800 tokens per reviewer × 3 reviewers = ~1,500-2,400 tokens saved per iteration).
    """
    with step("reviewers_fanout_node", state):
        full_request = state["user_request"]
        # Create abbreviated request with cultural context from evidence
        abbreviated_request = _create_abbreviated_request(
            full_request, evidence=state.get("evidence"),
        )
        draft_items = state.get("draft_items", [])
        iteration = state.get("iteration", 0)

        # 1E: Extract previous iteration's comments for iteration awareness
        previous_comments = None
        if iteration > 0:
            history = state.get("iteration_history", [])
            if history:
                last_snap = history[-1]
                previous_comments = {
                    "linguistic": [c.model_dump() for c in last_snap.linguistic_comments],
                    "bias": [c.model_dump() for c in last_snap.bias_comments],
                    "content": [c.model_dump() for c in last_snap.content_comments],
                }

        # Run all three reviewers concurrently with abbreviated request
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            content_future = executor.submit(
                review_content, abbreviated_request, draft_items, iteration, previous_comments
            )
            linguistic_future = executor.submit(
                review_linguistic, abbreviated_request, draft_items, iteration, previous_comments
            )
            bias_future = executor.submit(
                review_bias, abbreviated_request, draft_items, iteration, previous_comments
            )

            # Wait for all to complete and get results
            content_resp, content_usage = content_future.result()
            linguistic_resp, linguistic_usage = linguistic_future.result()
            bias_resp, bias_usage = bias_future.result()

        logger.info(
            "reviewers_fanout: content=%d linguistic=%d bias=%d",
            len(content_resp.comments),
            len(linguistic_resp.comments),
            len(bias_resp.comments),
        )

        # Accumulate all token usage
        combined_usage = TokenUsage(
            input_tokens=content_usage.input_tokens + linguistic_usage.input_tokens + bias_usage.input_tokens,
            output_tokens=content_usage.output_tokens + linguistic_usage.output_tokens + bias_usage.output_tokens,
            total_tokens=content_usage.total_tokens + linguistic_usage.total_tokens + bias_usage.total_tokens,
            model_name=content_usage.model_name,  # All use same model
        )
        token_update = _accumulate_tokens(state, combined_usage)

        return {
            "content_comments": content_resp.comments,
            "linguistic_comments": linguistic_resp.comments,
            "bias_comments": bias_resp.comments,
            **token_update,
        }


def critic_node(state: GraphState) -> Command[Literal["meta_editor_node", "finalize_node"]]:
    user_request = state.get("user_request")
    model_provider = user_request.model_provider if user_request else "claude"
    use_chatgpt_critics = user_request.use_chatgpt_critics if user_request else False

    decision, reason = critic_decide(
        linguistic_comments=state.get("linguistic_comments", []),
        bias_comments=state.get("bias_comments", []),
        content_comments=state.get("content_comments", []),
        iteration=state.get("iteration", 0),
        model_provider=model_provider,
        use_chatgpt_critics=use_chatgpt_critics,
        iteration_history=state.get("iteration_history", []),
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
        # Smart comment filtering: Only pass high-severity comments (≥3) to Meta-Editor
        # This reduces input tokens by 40-60% while preserving critical feedback
        linguistic_comments = state.get("linguistic_comments", [])
        bias_comments = state.get("bias_comments", [])
        content_comments = state.get("content_comments", [])

        # Filter comments by severity threshold (≥3)
        severity_threshold = 3
        filtered_linguistic = [c for c in linguistic_comments if c.severity >= severity_threshold]
        filtered_bias = [c for c in bias_comments if c.severity >= severity_threshold]
        filtered_content = [c for c in content_comments if c.severity >= severity_threshold]

        # Log filtering effectiveness
        total_comments = len(linguistic_comments) + len(bias_comments) + len(content_comments)
        filtered_total = len(filtered_linguistic) + len(filtered_bias) + len(filtered_content)
        filtered_out = total_comments - filtered_total

        if total_comments > 0:
            reduction_pct = (filtered_out / total_comments) * 100
            logger.info(
                f"Smart comment filtering: {filtered_out}/{total_comments} low-severity comments filtered "
                f"({reduction_pct:.1f}% reduction) - linguistic: {len(linguistic_comments)}->{len(filtered_linguistic)}, "
                f"bias: {len(bias_comments)}->{len(filtered_bias)}, "
                f"content: {len(content_comments)}->{len(filtered_content)}"
            )

        try:
            resp, usage = revise_items(
                request=state["user_request"],
                items=state.get("draft_items", []),
                linguistic_comments=filtered_linguistic,
                bias_comments=filtered_bias,
                content_comments=filtered_content,
                iteration=state.get("iteration", 0),
            )
        except Exception as e:
            logger.error(f"META_EDITOR failed: {e}. Returning items unchanged.", exc_info=True)
            resp = MetaEditorResponse(
                revision_plan=RevisionPlan(summary=f"Meta-editor failed: {type(e).__name__}. Items returned unchanged."),
                revised_items=state.get("draft_items", []),
            )
            usage = TokenUsage(model_name="fallback")

        token_update = _accumulate_tokens(state, usage)

        # Snapshot current comments before clearing so full history is preserved
        snapshot = IterationSnapshot(
            iteration=state.get("iteration", 0),
            linguistic_comments=linguistic_comments,
            bias_comments=bias_comments,
            content_comments=content_comments,
        )
        history = list(state.get("iteration_history", []))
        history.append(snapshot)

        return {
            "draft_items": resp.revised_items,
            "revision_plan": resp.revision_plan,
            "iteration_history": history,
            # Clear comments so each iteration reflects current draft only.
            "linguistic_comments": [],
            "bias_comments": [],
            "content_comments": [],
            **token_update,
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

        # Calculate API costs (pricing as of 2025)
        opus_tokens = state.get("opus_tokens_used", 0)
        sonnet_tokens = state.get("sonnet_tokens_used", 0)
        openai_tokens = state.get("openai_tokens_used", 0)
        chatgpt_tokens = state.get("chatgpt_tokens_used", 0)

        # Claude pricing (per 1M tokens):
        # - Opus: $15 input + $75 output → blended ~$45
        # - Sonnet: $3 input + $15 output → blended ~$9
        # OpenAI pricing (per 1M tokens):
        # - GPT-4o: $2.50 input + $10 output → blended ~$6.25 (used for ChatGPT critics toggle)
        # - GPT-4o-mini: $0.15 input + $0.60 output → blended ~$0.375 (20x cheaper than Sonnet!)
        # Note: Assuming ~1:1 input/output ratio for blended rate

        opus_cost = (opus_tokens / 1_000_000) * 45.0  # Blended rate for Opus
        sonnet_cost = (sonnet_tokens / 1_000_000) * 9.0  # Blended rate for Sonnet
        # GPT-4o pricing (used when ChatGPT critics toggle is enabled)
        chatgpt_cost = (chatgpt_tokens / 1_000_000) * 6.25  # Blended rate for GPT-4o
        # GPT-4o-mini pricing (used for agent overrides like bias_reviewer, critic)
        openai_cost = (openai_tokens / 1_000_000) * 0.375  # Blended rate for GPT-4o-mini

        # Phase 10: GPT-5.2 cost calculation (reasoning tokens billed at $14/1M output rate)
        gpt52_reasoning = state.get("gpt52_reasoning_tokens", 0)
        gpt52_output = state.get("gpt52_output_tokens", 0)
        gpt52_reasoning_cost = (gpt52_reasoning / 1_000_000) * 14.0
        gpt52_output_cost = (gpt52_output / 1_000_000) * 14.0

        # Check budget cap
        total_gpt52_cost = gpt52_reasoning_cost + gpt52_output_cost
        budget_exceeded = total_gpt52_cost > settings.ANALYTICS_BUDGET_CAP

        total_cost = opus_cost + sonnet_cost + chatgpt_cost + openai_cost + gpt52_reasoning_cost + gpt52_output_cost

        # Determine if smart validation was used
        from backend.agents.validator import _use_smart_validation
        smart_val_enabled = _use_smart_validation()
        validation_model = None
        if smart_val_enabled and state.get("validation_attempt", 1) == 1:
            # First attempt with smart validation: used Sonnet (unless all items passed)
            # Check if Opus was actually used by looking at token usage
            if opus_tokens > 0:
                validation_model = "opus"  # Fallback to Opus occurred
            else:
                validation_model = "sonnet"  # Sonnet was sufficient
        elif state.get("validation_attempt", 1) > 1:
            validation_model = "opus"  # Retries always use Opus
        else:
            validation_model = "opus"  # Smart validation disabled, always Opus

        # Update audit with validation metadata and cost tracking
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
            opus_cost=round(opus_cost, 2) if opus_cost > 0 else None,
            sonnet_cost=round(sonnet_cost, 2) if sonnet_cost > 0 else None,
            openai_cost=round(openai_cost, 2) if openai_cost > 0 else None,
            chatgpt_cost=round(chatgpt_cost, 2) if chatgpt_cost > 0 else None,
            total_cost=round(total_cost, 2) if total_cost > 0 else None,
            smart_validation_used=smart_val_enabled,
            validation_model_used=validation_model,
            gpt52_reasoning_cost=round(gpt52_reasoning_cost, 4) if gpt52_reasoning_cost > 0 else None,
            gpt52_output_cost=round(gpt52_output_cost, 4) if gpt52_output_cost > 0 else None,
            analytics_budget_exceeded=budget_exceeded if total_gpt52_cost > 0 else None,
        )

        # Phase 03.1: Extract review feedback from GraphState for complete metadata export
        # Aggregate comments from all iterations (iteration_history) + final iteration
        user_request = state.get("user_request")
        iteration_history = state.get("iteration_history", [])

        linguistic_feedback = []
        bias_feedback = []
        content_feedback = []
        for snap in iteration_history:
            linguistic_feedback.extend(snap.linguistic_comments)
            bias_feedback.extend(snap.bias_comments)
            content_feedback.extend(snap.content_comments)
        # Include final iteration's comments (not yet snapshotted)
        linguistic_feedback.extend(state.get("linguistic_comments", []))
        bias_feedback.extend(state.get("bias_comments", []))
        content_feedback.extend(state.get("content_comments", []))

        out = FinalOutput(
            final_items=enriched_items,
            audit=audit,
            user_request=user_request,
            linguistic_feedback=linguistic_feedback,
            bias_feedback=bias_feedback,
            content_feedback=content_feedback,
            iteration_history=iteration_history,
        )

        # Phase 10: Extract GPT-5.2 analytics toggle
        gpt52_enabled = user_request.use_gpt52_analytics if user_request and hasattr(user_request, "use_gpt52_analytics") else False

        return {"final_output": out, "gpt52_analytics_enabled": gpt52_enabled}


async def correlation_node(state: GraphState) -> GraphState:
    """Correlation analysis using embedding cosine similarity and McDonald's omega.

    Uses Hommel & Arslan (2024) methodology: sentence-embedding cosine similarity
    to estimate pairwise correlations, then calculates McDonald's omega.
    """
    with step("correlation_node", state):
        try:
            # Extract finalized items from state
            final_output = state.get("final_output")
            if not final_output:
                logger.warning("No final_output in state, skipping correlation analysis")
                return {}

            final_items = final_output.final_items
            if len(final_items) < 3:
                logger.info(f"Too few items ({len(final_items)}) for correlation analysis (minimum 3), skipping")
                return {}

            # Extract item texts and construct name
            item_texts = [item.item_text for item in final_items]
            user_request = state.get("user_request")
            construct_name = user_request.construct_name if user_request else "Unknown Construct"

            logger.info(f"Starting correlation analysis for {len(item_texts)} items measuring '{construct_name}'")

            # Import correlation modules
            from backend.agents.correlation_estimator import estimate_pairwise_correlations
            from backend.analytics.omega_calculator import calculate_omega
            from backend.schemas import CorrelationMatrix

            # Estimate pairwise correlations using embedding cosine similarity
            cells = await estimate_pairwise_correlations(item_texts, construct_name)

            if not cells:
                logger.warning("Correlation estimation returned no cells, skipping omega calculation")
                return {}

            # Calculate McDonald's omega and internal consistency metrics
            omega_result = calculate_omega(cells, num_items=len(item_texts))

            # Handle calculation failure
            if omega_result["omega_total"] is None:
                logger.warning("Omega calculation failed (non-positive-definite matrix), setting omega=0.0")
                omega_total = 0.0
                internal_consistency_flag = "calculation_failed"
            else:
                omega_total = omega_result["omega_total"]
                internal_consistency_flag = omega_result["internal_consistency_flag"]

            # Build CorrelationMatrix
            correlation_matrix = CorrelationMatrix(
                cells=cells,
                mcdonalds_omega=omega_total,
                mean_inter_item_correlation=omega_result["mean_inter_item_correlation"],
                internal_consistency_flag=internal_consistency_flag,
                guidance=omega_result.get("guidance"),
            )

            # Update FinalOutput with correlation_matrix
            updated_final_output = final_output.model_copy(deep=True)
            updated_final_output.correlation_matrix = correlation_matrix

            logger.info(
                f"Correlation analysis complete: omega={omega_total:.3f}, "
                f"mean_r={omega_result['mean_inter_item_correlation']:.3f}, "
                f"flag={internal_consistency_flag}"
            )

            # TODO: Track GPT-5.2 token usage from correlation estimation
            # For now, return updated FinalOutput
            return {"final_output": updated_final_output}

        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}", exc_info=True)
            # Graceful failure: return empty dict, FinalOutput.correlation_matrix stays None
            return {}


def comparison_node(state: GraphState) -> GraphState:
    """Instrument comparison: search for convergent/discriminant instruments and detect plagiarism.

    Phase 9 Plan 02: Real implementation - discovers comparison instruments via Perplexity search,
    scores convergent validity, runs plagiarism detection, and updates FinalOutput.
    """
    with step("comparison_node", state):
        try:
            # Extract finalized items from state
            final_output = state.get("final_output")
            if not final_output:
                logger.warning("No final_output in state, skipping comparison analysis")
                return {}

            final_items = final_output.final_items
            if not final_items:
                logger.warning("No final items in final_output, skipping comparison analysis")
                return {}

            # Extract user request for construct info
            user_request = state.get("user_request")
            if not user_request:
                logger.warning("No user_request in state, skipping comparison analysis")
                return {}

            construct_name = user_request.construct_name
            construct_definition = user_request.construct_definition

            logger.info(f"Starting instrument comparison for '{construct_name}'")

            # Import search and scoring modules
            from backend.agents.instrument_searcher import search_instruments
            from backend.agents.validity_scorer import score_convergent_validity
            from backend.analytics.similarity_calculator import get_plagiarism_detector

            # Search for convergent and discriminant instruments
            convergent_instrument, discriminant_instrument = search_instruments(
                construct_name, construct_definition
            )

            logger.info(
                f"Found comparison instruments: convergent={convergent_instrument.name}, "
                f"discriminant={discriminant_instrument.name}"
            )

            # Extract item texts for validity scoring
            item_texts = [item.item_text for item in final_items]

            # Score convergent validity (embedding-based when items available, LLM fallback)
            convergent_score, convergent_method = score_convergent_validity(
                item_texts,
                convergent_instrument.name,
                convergent_instrument.measured_construct,
                construct_name,
                published_items=convergent_instrument.items,
            )
            convergent_instrument = convergent_instrument.model_copy(
                update={"validity_method": convergent_method}
            )

            logger.info(f"Convergent validity score: {convergent_score:.2f} (method={convergent_method})")

            # 1B: Convergent validity ceiling warning
            if convergent_score > 0.85:
                ceiling_warning = (
                    f"Convergent validity of {convergent_score:.2f} with {convergent_instrument.name} "
                    f"suggests items may be derivative (expected: 0.60-0.80)"
                )
                logger.warning(f"CONVERGENT_CEILING_WARNING {ceiling_warning}")
                # Will be added to plagiarism_flags below with index -1

            # Run plagiarism detection against known instrument items
            from data.known_instrument_items import lookup_instrument_items
            published_items = lookup_instrument_items(convergent_instrument.name)
            if not published_items:
                # Try construct name as fallback
                published_items = lookup_instrument_items(construct_name)
            logger.info(f"Plagiarism check: {len(published_items)} known items for '{convergent_instrument.name}'")

            plagiarism_detector = get_plagiarism_detector()
            plagiarism_flags = plagiarism_detector.detect_plagiarism(
                item_texts,
                published_items,
                convergent_instrument.name
            )

            # Add convergent ceiling warning to plagiarism flags
            if convergent_score > 0.85:
                plagiarism_flags[-1] = (
                    f"Convergent validity of {convergent_score:.2f} with {convergent_instrument.name} "
                    f"suggests items may be derivative (expected: 0.60-0.80)"
                )

            # Update FinalOutput with comparison data
            updated_final_output = final_output.model_copy(deep=True)
            updated_final_output.comparison_instruments = [convergent_instrument, discriminant_instrument]
            updated_final_output.plagiarism_flags = plagiarism_flags if plagiarism_flags else None
            updated_final_output.convergent_validity_score = convergent_score

            logger.info(
                f"Comparison analysis complete: {len(updated_final_output.comparison_instruments)} instruments, "
                f"{len(plagiarism_flags)} plagiarism flags"
            )

            return {"final_output": updated_final_output}

        except Exception as e:
            logger.error(f"Comparison analysis failed: {e}", exc_info=True)
            # Graceful failure: return empty dict, comparison fields stay default
            return {}


def cross_construct_node(state: GraphState) -> GraphState:
    """Cross-construct discriminant validity analysis.

    Phase 9 Plan 02: Real implementation - scores discriminant validity between target construct
    and comparison constructs, builds CrossConstructComparison with validity flags.
    """
    with step("cross_construct_node", state):
        try:
            # Extract finalized items from state
            final_output = state.get("final_output")
            if not final_output:
                logger.warning("No final_output in state, skipping cross-construct analysis")
                return {}

            # Check if comparison instruments were found
            if not final_output.comparison_instruments:
                logger.warning("No comparison_instruments in final_output, skipping cross-construct analysis")
                return {}

            final_items = final_output.final_items
            if not final_items:
                logger.warning("No final items in final_output, skipping cross-construct analysis")
                return {}

            # Extract user request for construct info
            user_request = state.get("user_request")
            if not user_request:
                logger.warning("No user_request in state, skipping cross-construct analysis")
                return {}

            construct_name = user_request.construct_name

            logger.info(f"Starting cross-construct analysis for '{construct_name}'")

            # Import scoring module
            from backend.agents.validity_scorer import score_discriminant_validity
            from backend.schemas import CrossConstructComparison

            # Get discriminant instrument (second one from comparison_instruments)
            discriminant_instrument = final_output.comparison_instruments[1]

            # 1C: If construct_exclusions set, use it as discriminant construct
            exclusion_construct = None
            if user_request.construct_exclusions:
                exclusion_construct = user_request.construct_exclusions
                logger.info(f"Using construct_exclusions as discriminant target: '{exclusion_construct}'")

            # Extract item texts
            item_texts = [item.item_text for item in final_items]

            # Score discriminant validity (embedding-based when items available, LLM fallback)
            disc_name = discriminant_instrument.name
            disc_construct = exclusion_construct or discriminant_instrument.measured_construct
            discriminant_pair, disc_method = score_discriminant_validity(
                item_texts,
                disc_name,
                disc_construct,
                construct_name,
                published_items=discriminant_instrument.items,
            )

            logger.info(
                f"Discriminant validity: correlation={discriminant_pair.estimated_correlation:.2f}, "
                f"flag={discriminant_pair.discriminant_validity_flag} (method={disc_method})"
            )

            # Build analysis summary
            flag = discriminant_pair.discriminant_validity_flag
            corr = discriminant_pair.estimated_correlation
            if flag == "concern":
                summary = (
                    f"High overlap detected between '{construct_name}' and '{discriminant_instrument.measured_construct}' "
                    f"(estimated r = {corr:.2f}). Consider refining item wording to improve discriminant validity."
                )
            else:
                summary = (
                    f"Adequate discriminant validity between '{construct_name}' and '{discriminant_instrument.measured_construct}' "
                    f"(estimated r = {corr:.2f}). Constructs appear sufficiently distinct."
                )

            # Build CrossConstructComparison
            disc_disclaimer = (
                "Embedding-based cosine similarity (Hommel & Arslan, 2024)"
                if disc_method == "embedding"
                else "LLM-estimated (no published items available), not empirically validated"
            )
            cross_construct_analysis = CrossConstructComparison(
                target_construct=construct_name,
                comparison_constructs=[discriminant_instrument.measured_construct],
                analysis_summary=summary,
                construct_pairs=[discriminant_pair],
                disclaimer=disc_disclaimer,
            )

            # Update FinalOutput
            updated_final_output = final_output.model_copy(deep=True)
            updated_final_output.cross_construct_analysis = cross_construct_analysis

            logger.info("Cross-construct analysis complete")

            return {"final_output": updated_final_output}

        except Exception as e:
            logger.error(f"Cross-construct analysis failed: {e}", exc_info=True)
            # Graceful failure: return empty dict, cross_construct_analysis stays None
            return {}


async def analytics_dispatch_node(state: GraphState) -> GraphState:
    """Run analytics in parallel using asyncio.gather, then merge results.

    Correlation and comparison run concurrently. Cross-construct runs after
    comparison completes because it depends on comparison_instruments.
    Budget check runs at the end.
    """
    with step("analytics_dispatch_node", state):
        final_output = state.get("final_output")
        if not final_output or len(final_output.final_items) < 3:
            logger.info(f"Too few items for analytics (minimum 3), skipping")
            return {}

        gpt52_enabled = state.get("gpt52_analytics_enabled", False)
        logger.info(f"Running parallel analytics (GPT-5.2 enabled: {gpt52_enabled})")

        # Phase 1: correlation + comparison in parallel
        results = await asyncio.gather(
            correlation_node(state),
            asyncio.to_thread(comparison_node, state),
            return_exceptions=True,
        )

        correlation_result, comparison_result = results
        logger.info(
            "ANALYTICS_RESULTS correlation=%s comparison=%s",
            "ok" if isinstance(correlation_result, dict) else type(correlation_result).__name__,
            "ok" if isinstance(comparison_result, dict) else type(comparison_result).__name__,
        )

        # Merge into single FinalOutput
        updated = final_output.model_copy(deep=True)

        if isinstance(correlation_result, dict) and "final_output" in correlation_result:
            updated.correlation_matrix = correlation_result["final_output"].correlation_matrix
            # 1D: Pairwise redundancy detection
            if updated.correlation_matrix and updated.correlation_matrix.cells:
                redundancy_flags = []
                for cell in updated.correlation_matrix.cells:
                    if cell.correlation > 0.75:
                        redundancy_flags.append(
                            f"Items {cell.item_i_index + 1} and {cell.item_j_index + 1} are redundant "
                            f"(r = {cell.correlation:.2f}) — consider replacing one"
                        )
                if redundancy_flags:
                    updated.correlation_matrix.redundancy_flags = redundancy_flags
                    logger.warning(f"REDUNDANCY_FLAGS count={len(redundancy_flags)}")
        elif isinstance(correlation_result, Exception):
            logger.error(f"Correlation analysis failed: {correlation_result}")

        if isinstance(comparison_result, dict) and "final_output" in comparison_result:
            comp_fo = comparison_result["final_output"]
            updated.comparison_instruments = comp_fo.comparison_instruments
            updated.plagiarism_flags = comp_fo.plagiarism_flags
            updated.convergent_validity_score = comp_fo.convergent_validity_score
        elif isinstance(comparison_result, Exception):
            logger.error(f"Comparison analysis failed: {comparison_result}")

        # Phase 2: cross-construct (needs comparison_instruments from phase 1)
        if updated.comparison_instruments:
            cross_state = dict(state)
            cross_state["final_output"] = updated
            try:
                cross_result = cross_construct_node(cross_state)
                if isinstance(cross_result, dict) and "final_output" in cross_result:
                    updated.cross_construct_analysis = cross_result["final_output"].cross_construct_analysis
            except Exception as e:
                logger.error(f"Cross-construct analysis failed: {e}")
        else:
            logger.info("No comparison instruments found, skipping cross-construct analysis")

        # Budget check
        if gpt52_enabled:
            gpt52_reasoning = state.get("gpt52_reasoning_tokens", 0)
            gpt52_output = state.get("gpt52_output_tokens", 0)
            gpt52_cost = (gpt52_reasoning + gpt52_output) / 1_000_000 * 14.0
            if gpt52_cost > settings.ANALYTICS_BUDGET_CAP:
                logger.warning(
                    f"ANALYTICS_BUDGET_EXCEEDED cost=${gpt52_cost:.4f} cap=${settings.ANALYTICS_BUDGET_CAP:.2f}"
                )

        return {"final_output": updated}


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
    # Phase 7: Analytics placeholder nodes
    builder.add_node("correlation_node", correlation_node)
    builder.add_node("comparison_node", comparison_node)
    builder.add_node("cross_construct_node", cross_construct_node)
    # Phase 10: Analytics dispatch node (parallel via asyncio.gather)
    builder.add_node("analytics_dispatch_node", analytics_dispatch_node)

    builder.add_node("facet_mapper_node", facet_mapper_node)

    builder.add_edge(START, "init_run")
    builder.add_edge("init_run", "retrieve_node")
    builder.add_edge("retrieve_node", "facet_mapper_node")
    builder.add_edge("facet_mapper_node", "item_writer_node")

    # Validation gate BEFORE reviewers
    # validation_node returns Command object for conditional routing
    builder.add_edge("item_writer_node", "validation_node")

    # Regeneration loops back to validation
    builder.add_edge("regenerate_items_node", "validation_node")

    # Use parallel reviewers instead of sequential
    builder.add_edge("reviewers_fanout_node", "critic_node")

    # Critic routes to either meta-editor (revise) or finalize (end)
    # Meta-editor loops back into parallel reviewers.
    builder.add_edge("meta_editor_node", "reviewers_fanout_node")

    # Phase 10: Analytics dispatch (correlation + comparison parallel, then cross-construct)
    builder.add_edge("finalize_node", "analytics_dispatch_node")
    builder.add_edge("analytics_dispatch_node", END)

    return builder.compile(checkpointer=checkpointer)
