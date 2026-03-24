from __future__ import annotations

import json
import logging
import warnings
from typing import List, Tuple

from backend.agents.llm_factory import get_chat_model_for_agent
from backend.agents.llm_utils import TokenUsage, _extract_token_usage
from backend.agents.prompt_loader import load_prompt

def _detect_identical_scores(validations: List[ItemValidation]) -> bool:
    """Detect if all items received identical dimension scores.

    When an LLM returns the same scores for every item in a batch,
    it indicates lazy evaluation rather than genuine item-level assessment.
    """
    if len(validations) < 3:
        return False
    first_scores = tuple(d.score for d in validations[0].dimension_scores)
    return all(
        tuple(d.score for d in v.dimension_scores) == first_scores
        for v in validations[1:]
    )
from backend.schemas import (
    DimensionScore,
    DraftItem,
    ItemValidation,
    UserRequest,
    ValidationResponse,
)
from backend.settings import settings

logger = logging.getLogger(__name__)


_REASONING_MAX = 280


def _clamp_validation_fields(data: dict) -> dict:
    """Fix common field-level issues in raw validator JSON before Pydantic validation."""
    for v in data.get("validations", []):
        if not isinstance(v, dict):
            continue
        for ds in v.get("dimension_scores", []):
            if not isinstance(ds, dict):
                continue
            # Truncate oversized reasoning
            reasoning = ds.get("reasoning", "")
            if isinstance(reasoning, str) and len(reasoning) > _REASONING_MAX:
                truncated = reasoning[:_REASONING_MAX]
                last_period = truncated.rfind(". ")
                if last_period > 0:
                    ds["reasoning"] = truncated[: last_period + 1]
                else:
                    ds["reasoning"] = truncated[: _REASONING_MAX - 3] + "..."
            # Clamp score to valid range
            score = ds.get("score")
            if isinstance(score, (int, float)):
                ds["score"] = max(1, min(10, int(score)))
    return data


def _fallback_parse_validation(raw_message) -> ValidationResponse:
    """Extract JSON from raw LLM response and parse with field-level fixups.

    Mirrors the fallback logic in invoke_structured_with_usage but specific to
    the validator's ValidationResponse schema.
    """
    # Extract text content from the raw AI message
    content = getattr(raw_message, "content", None)
    if content is None:
        raise RuntimeError("Validator fallback: no content in raw message")

    # Handle tool call responses (Anthropic returns list of content blocks)
    raw_json = None
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                # Tool use block
                if block.get("type") == "tool_use" and "input" in block:
                    raw_json = block["input"]
                    break
                # Text block with JSON
                if block.get("type") == "text" and block.get("text", "").strip().startswith("{"):
                    try:
                        raw_json = json.loads(block["text"])
                    except json.JSONDecodeError:
                        continue
    elif isinstance(content, str):
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`").replace("json", "", 1).strip()
        try:
            raw_json = json.loads(text)
        except json.JSONDecodeError:
            pass

    if raw_json is None:
        raise RuntimeError(
            "Validator fallback: could not extract JSON from raw response"
        )

    # Apply field-level fixups
    if isinstance(raw_json, dict):
        raw_json = _clamp_validation_fields(raw_json)

    logger.info("VALIDATOR fallback parse succeeded after field fixups")
    return ValidationResponse.model_validate(raw_json)


def _use_smart_validation() -> bool:
    """Check if smart validation (tiered Sonnet→Opus) is enabled.

    Smart validation: Use cheaper Sonnet for first attempt, only use Opus if items fail.
    Cost savings: ~80% cheaper for items that pass Sonnet validation.
    """
    return getattr(settings, "SMART_VALIDATION_ENABLED", True)


def validate_items(
    request: UserRequest,
    items: List[DraftItem],
    attempt: int = 1,
) -> Tuple[ValidationResponse, TokenUsage]:
    """Validate all items using LLM-as-judge with chain-of-thought scoring.

    Args:
        request: User's measurement intent with construct definition
        items: List of draft items to validate
        attempt: Which regeneration attempt (1-3)

    Returns:
        Tuple of (ValidationResponse, TokenUsage)

    Raises:
        ValueError: If attempt is not between 1-3
        RuntimeError: If LLM invocation fails in real mode
    """
    if not 1 <= attempt <= 3:
        raise ValueError(f"Attempt must be 1-3, got {attempt}")

    if settings.APP_MODE == "mock":
        # Return deterministic mock validation for testing
        validations = []
        for idx, item in enumerate(items):
            # Alternate pass/fail for testing: even indices pass, odd indices fail
            is_passing = idx % 2 == 0
            score = 8.0 if is_passing else 6.5

            # For passing items (score ≥ 7): empty reasoning
            # For failing items (score < 7): provide detailed reasoning
            validations.append(
                ItemValidation(
                    item_index=idx,
                    item_text=item.item_text,
                    dimension_scores=[
                        DimensionScore(
                            dimension="correspondence",
                            reasoning="" if is_passing else "Mock failing: Item does not fully capture construct definition",
                            score=8 if is_passing else 6,
                        ),
                        DimensionScore(
                            dimension="distinctiveness",
                            reasoning="" if is_passing else "Mock failing: Item overlaps with related construct",
                            score=8 if is_passing else 7,
                        ),
                        DimensionScore(
                            dimension="clarity",
                            reasoning="",  # Always passing in mock
                            score=8,
                        ),
                        DimensionScore(
                            dimension="specificity",
                            reasoning="",  # Always passing in mock
                            score=8,
                        ),
                    ],
                    weighted_score=score,
                    accept=score >= 7.0,
                    attempt=attempt,
                )
            )
        return ValidationResponse(validations=validations), TokenUsage()

    # Real mode: Smart validation with tiered approach
    smart = _use_smart_validation()
    logger.info(
        "VALIDATOR start items=%d attempt=%d smart_validation=%s",
        len(items), attempt, smart,
    )
    try:
        system_prompt = load_prompt("validator.md")

        # Build user payload
        user_payload = {
            "construct_name": request.construct_name,
            "construct_definition": request.construct_definition,
            "items": [
                {"index": i, "text": item.item_text}
                for i, item in enumerate(items)
            ],
            "attempt": attempt,
        }

        # Convert to LangChain messages with cache_control for cost optimization
        # Only apply cache control for Claude models (Anthropic API supports prompt caching)
        from langchain_core.messages import HumanMessage, SystemMessage

        # Determine model based on smart validation and ChatGPT critics toggle
        # Smart validation: Use Sonnet first (80% cheaper), only use Opus if items fail
        # ChatGPT critics: Override to use ChatGPT if enabled
        use_chatgpt = getattr(request, "use_chatgpt_critics", False)

        if _use_smart_validation() and attempt == 1 and not use_chatgpt:
            # Smart validation: Sonnet first attempt (Claude only)
            logger.info(f"Smart validation: Attempting with Sonnet first (attempt {attempt})")
            model = get_chat_model_for_agent(
                agent_name="validator",
                model_provider="claude",
                use_chatgpt_critics=False,
            )
            # Override to force Sonnet for first attempt (not Opus)
            from backend.agents.llm_factory import get_claude_chat_model
            model = get_claude_chat_model(model="claude-sonnet-4-5")
            model_name = "claude-sonnet-4-5"
        else:
            # Use standard allocation (respects ChatGPT toggle)
            logger.info(f"Using validator model (attempt {attempt}, use_chatgpt={use_chatgpt})")
            if attempt >= 2:
                # On retry: use Opus with higher temperature to avoid deterministic
                # identical scores, and skip prompt cache to get fresh evaluation
                from backend.agents.llm_factory import get_claude_chat_model
                from langchain_anthropic import ChatAnthropic
                model = ChatAnthropic(
                    model="claude-opus-4-6",
                    api_key=settings.CLAUDE_API_KEY,
                    temperature=0.5,  # Higher temp forces score differentiation
                    max_retries=3,
                    timeout=60,
                )
                model_name = "claude-opus-4-6"
                logger.info(f"Retry attempt {attempt}: using Opus with temperature=0.5, no prompt cache")
            else:
                model = get_chat_model_for_agent(
                    agent_name="validator",
                    model_provider=request.model_provider,
                    use_chatgpt_critics=use_chatgpt,
                )
                model_name = getattr(model, "model_name", getattr(model, "model", "unknown"))

        # Build messages — disable prompt caching on retries to avoid cached lazy responses
        if attempt > 1:
            messages = [
                SystemMessage(content=system_prompt),  # No cache_control on retry
                HumanMessage(
                    content=(
                        f"RETRY ATTEMPT {attempt}: Previous validation returned identical scores for all items. "
                        "You MUST evaluate each item INDIVIDUALLY with differentiated scores.\n"
                        "CRITICAL: For each item, you MUST return the EXACT item_text as provided in the input. "
                        "Do not paraphrase, substitute, or modify the text in any way.\n\n"
                        f"INPUT:\n{user_payload}"
                    )
                ),
            ]
        else:
            messages = [
                SystemMessage(
                    content=system_prompt,
                    additional_kwargs={"cache_control": {"type": "ephemeral"}}
                ),
                HumanMessage(
                    content=(
                        "Validate these items using the 4-dimension rubric.\n"
                        "CRITICAL: For each item, you MUST return the EXACT item_text as provided in the input. "
                        "Do not paraphrase, substitute, or modify the text in any way.\n\n"
                        f"INPUT:\n{user_payload}"
                    )
                ),
            ]

        # Invoke with structured output, capturing raw response for token tracking
        # Use try-except pattern (same as llm_utils.py) for cross-provider compatibility
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.*")
            try:
                runnable = model.with_structured_output(ValidationResponse, strict=True, include_raw=True)
            except TypeError:
                runnable = model.with_structured_output(ValidationResponse, include_raw=True)
            response = runnable.invoke(messages)

        # Extract result and token usage
        if isinstance(response, dict) and "parsed" in response and "raw" in response:
            result = response["parsed"]
            raw_message = response["raw"]

            # If structured parsing failed, try JSON fallback with field fixups
            if result is None:
                logger.warning(
                    "VALIDATOR structured output parsed=None, attempting JSON fallback. "
                    "Model: %s, Attempt: %d/3",
                    model_name, attempt,
                )
                result = _fallback_parse_validation(raw_message)

            usage = _extract_token_usage(raw_message, model_name)
        else:
            # Fallback: no raw message available (older LangChain behavior)
            result = response
            usage = TokenUsage(model_name=model_name)

            # Also validate fallback path
            if result is None:
                logger.error(f"Validator returned None response (no LLM output)")
                raise RuntimeError(
                    f"Validator returned None - no response from LLM. "
                    f"Model: {model_name}, Attempt: {attempt}/3."
                )

        # Post-validation text integrity check: override LLM-returned item_text
        # with the actual input text to prevent hallucinated substitutions.
        for v in result.validations:
            idx = v.item_index
            if 0 <= idx < len(items):
                expected_text = items[idx].item_text
                if v.item_text != expected_text:
                    logger.warning(
                        "VALIDATOR_TEXT_MISMATCH item_index=%d expected=%r got=%r",
                        idx, expected_text[:80], v.item_text[:80],
                    )
                    v.item_text = expected_text

        # Detect lazy identical scores — all items get same dimension scores
        if _detect_identical_scores(result.validations):
            logger.warning(
                "VALIDATOR_IDENTICAL_SCORES attempt=%d model=%s items=%d — "
                "all items received identical dimension scores, indicating lazy LLM evaluation",
                attempt, model_name, len(result.validations),
            )
            if attempt < 3:
                raise RuntimeError(
                    "Validator returned identical scores for all items — "
                    "forcing retry with different model/temperature"
                )
            # On attempt 3 (hard limit), accept but the warning is logged

        accepted_count = sum(1 for v in result.validations if v.accept)
        logger.info(
            f"Validated {len(items)} items with {model_name} on attempt {attempt}. "
            f"Accepted: {accepted_count}/{len(items)}. "
            f"Tokens: {usage.total_tokens}"
        )

        return result, usage

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise RuntimeError(f"Validation agent failed: {e}") from e
