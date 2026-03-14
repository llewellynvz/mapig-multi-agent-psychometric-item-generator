from __future__ import annotations
import logging

import concurrent.futures
import datetime as _dt
import uuid
from typing import List, Literal, Optional

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

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
    DraftItem,
    EvidenceChunk,
    FinalOutput,
    ItemValidation,
    ReviewComment,
    RevisionPlan,
    UserRequest,
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

    # Cost tracking (accumulated during run)
    opus_tokens_used: int
    sonnet_tokens_used: int
    openai_tokens_used: int
    chatgpt_tokens_used: int
    # Phase 7: GPT-5.2 token tracking
    gpt52_tokens_used: int
    gpt52_reasoning_tokens: int
    gpt52_output_tokens: int

    # Output
    final_output: FinalOutput


def _utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def _create_abbreviated_request(full_request: UserRequest) -> AbbreviatedRequest:
    """Create abbreviated request for reviewers (cost optimization).

    Reviewers don't need: evidence, examples, neighbors, retrieval settings, feedback.
    Reduces payload size by ~60% (~500-800 tokens per reviewer call).

    Args:
        full_request: Complete UserRequest with all fields

    Returns:
        AbbreviatedRequest with only essential fields for review
    """
    return AbbreviatedRequest(
        construct_name=full_request.construct_name,
        construct_definition=full_request.construct_definition,
        target_population=full_request.target_population,
        response_scale=full_request.response_scale,
        constraints=full_request.constraints,
        model_provider=full_request.model_provider,
        use_chatgpt_critics=full_request.use_chatgpt_critics,
    )


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
            "opus_tokens_used": 0,
            "sonnet_tokens_used": 0,
            "openai_tokens_used": 0,
            "chatgpt_tokens_used": 0,
            "gpt52_tokens_used": 0,
            "gpt52_reasoning_tokens": 0,
            "gpt52_output_tokens": 0,
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
        resp, usage = write_items(state["user_request"], state.get("evidence", []))
        token_update = _accumulate_tokens(state, usage)
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

        resp, usage = validate_items(
            request=state["user_request"],
            items=draft_items,
            attempt=attempt
        )

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
        # Create abbreviated request (no evidence, examples, or retrieval settings)
        abbreviated_request = _create_abbreviated_request(full_request)
        draft_items = state.get("draft_items", [])
        iteration = state.get("iteration", 0)

        # Run all three reviewers concurrently with abbreviated request
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            content_future = executor.submit(
                review_content, abbreviated_request, draft_items, iteration
            )
            linguistic_future = executor.submit(
                review_linguistic, abbreviated_request, draft_items, iteration
            )
            bias_future = executor.submit(
                review_bias, abbreviated_request, draft_items, iteration
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

        resp, usage = revise_items(
            request=state["user_request"],
            items=state.get("draft_items", []),
            linguistic_comments=filtered_linguistic,
            bias_comments=filtered_bias,
            content_comments=filtered_content,
            iteration=state.get("iteration", 0),
        )

        token_update = _accumulate_tokens(state, usage)

        return {
            "draft_items": resp.revised_items,
            "revision_plan": resp.revision_plan,
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

        total_cost = opus_cost + sonnet_cost + chatgpt_cost + openai_cost

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
        )

        # Phase 03.1: Extract review feedback from GraphState for complete metadata export
        user_request = state.get("user_request")
        linguistic_feedback = state.get("linguistic_comments", [])
        bias_feedback = state.get("bias_comments", [])
        content_feedback = state.get("content_comments", [])

        out = FinalOutput(
            final_items=enriched_items,
            audit=audit,
            user_request=user_request,
            linguistic_feedback=linguistic_feedback,
            bias_feedback=bias_feedback,
            content_feedback=content_feedback,
        )
        return {"final_output": out}


async def correlation_node(state: GraphState) -> GraphState:
    """Correlation analysis using GPT-5.2 pairwise estimation and McDonald's omega.

    Phase 8: Real implementation - estimates pairwise correlations, calculates omega,
    populates FinalOutput.correlation_matrix with full analytics.
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

            # Estimate pairwise correlations using GPT-5.2
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
                internal_consistency_flag=internal_consistency_flag
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

            # Score convergent validity
            convergent_score = score_convergent_validity(
                item_texts,
                convergent_instrument.name,
                convergent_instrument.construct,
                construct_name
            )

            logger.info(f"Convergent validity score: {convergent_score:.2f}")

            # Run plagiarism detection
            # Note: We don't have published item texts (copyright safeguard), so this returns empty dict
            # Infrastructure supports future enhancement if Perplexity snippets contain sample items
            plagiarism_detector = get_plagiarism_detector()
            plagiarism_flags = plagiarism_detector.detect_plagiarism(
                item_texts,
                [],  # No published items available (copyright protection)
                convergent_instrument.name
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

            # Extract item texts
            item_texts = [item.item_text for item in final_items]

            # Score discriminant validity
            discriminant_pair = score_discriminant_validity(
                item_texts,
                discriminant_instrument.name,
                discriminant_instrument.construct,
                construct_name
            )

            logger.info(
                f"Discriminant validity: correlation={discriminant_pair.estimated_correlation:.2f}, "
                f"flag={discriminant_pair.discriminant_validity_flag}"
            )

            # Build analysis summary
            flag = discriminant_pair.discriminant_validity_flag
            corr = discriminant_pair.estimated_correlation
            if flag == "concern":
                summary = (
                    f"High overlap detected between '{construct_name}' and '{discriminant_instrument.construct}' "
                    f"(estimated r = {corr:.2f}). Consider refining item wording to improve discriminant validity."
                )
            else:
                summary = (
                    f"Adequate discriminant validity between '{construct_name}' and '{discriminant_instrument.construct}' "
                    f"(estimated r = {corr:.2f}). Constructs appear sufficiently distinct."
                )

            # Build CrossConstructComparison
            cross_construct_analysis = CrossConstructComparison(
                target_construct=construct_name,
                comparison_constructs=[discriminant_instrument.construct],
                analysis_summary=summary,
                construct_pairs=[discriminant_pair],
                disclaimer="LLM-estimated, not empirically validated"
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

    builder.add_edge(START, "init_run")
    builder.add_edge("init_run", "retrieve_node")
    builder.add_edge("retrieve_node", "item_writer_node")

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

    # Phase 7: Analytics chain after finalize, before END
    builder.add_edge("finalize_node", "correlation_node")
    builder.add_edge("correlation_node", "comparison_node")
    builder.add_edge("comparison_node", "cross_construct_node")
    builder.add_edge("cross_construct_node", END)

    return builder.compile(checkpointer=checkpointer)
