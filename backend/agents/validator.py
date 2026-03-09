from __future__ import annotations

import logging
from typing import List, Tuple

from backend.agents.llm_factory import get_validator_model, get_claude_chat_model
from backend.agents.llm_utils import TokenUsage, _extract_token_usage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import (
    DimensionScore,
    DraftItem,
    ItemValidation,
    UserRequest,
    ValidationResponse,
)
from backend.settings import settings

logger = logging.getLogger(__name__)


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

        # Smart validation: Use Sonnet first (80% cheaper), only use Opus if items fail
        if _use_smart_validation() and attempt == 1:
            logger.info(f"Smart validation: Attempting with Sonnet first (attempt {attempt})")
            model = get_claude_chat_model(model="claude-sonnet-4-5")
            model_name = "claude-sonnet-4-5"
        else:
            # Use Opus for: (1) retries (attempt > 1), or (2) smart validation disabled
            logger.info(f"Using Opus validation (attempt {attempt})")
            model = get_validator_model()
            model_name = getattr(model, "model_name", getattr(model, "model", "opus"))

        # Build messages with cache_control for system prompt
        # Cache control reduces cost by ~90% on cached portions (5-minute TTL)
        messages = [
            SystemMessage(
                content=system_prompt,
                additional_kwargs={"cache_control": {"type": "ephemeral"}}
            ),
            HumanMessage(
                content=f"Validate these items using the 4-dimension rubric.\n\nINPUT:\n{user_payload}"
            ),
        ]

        # Invoke with structured output, capturing raw response for token tracking
        # Note: strict=False to allow minLength=0 for reasoning field (empty for passing dimensions)
        runnable = model.with_structured_output(ValidationResponse, strict=False, include_raw=True)
        response = runnable.invoke(messages)

        # Extract result and token usage
        if isinstance(response, dict) and "parsed" in response and "raw" in response:
            result = response["parsed"]
            raw_message = response["raw"]
            usage = _extract_token_usage(raw_message, model_name)
        else:
            # Fallback: no raw message available
            result = response
            usage = TokenUsage(model_name=model_name)

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
