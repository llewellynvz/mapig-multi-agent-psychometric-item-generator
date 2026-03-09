from __future__ import annotations

import logging
from typing import List, Tuple

from backend.agents.llm_factory import get_validator_model
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
            score = 8.0 if idx % 2 == 0 else 6.5

            validations.append(
                ItemValidation(
                    item_index=idx,
                    item_text=item.item_text,
                    dimension_scores=[
                        DimensionScore(
                            dimension="correspondence",
                            reasoning="Mock reasoning for correspondence",
                            score=8,
                        ),
                        DimensionScore(
                            dimension="distinctiveness",
                            reasoning="Mock reasoning for distinctiveness",
                            score=8,
                        ),
                        DimensionScore(
                            dimension="clarity",
                            reasoning="Mock reasoning for clarity",
                            score=8,
                        ),
                        DimensionScore(
                            dimension="specificity",
                            reasoning="Mock reasoning for specificity",
                            score=8,
                        ),
                    ],
                    weighted_score=score,
                    accept=score >= 7.0,
                    attempt=attempt,
                )
            )
        return ValidationResponse(validations=validations), TokenUsage()

    # Real mode: Use Claude Opus for validation
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

        messages = [
            ("system", system_prompt),
            (
                "human",
                f"Validate these items using the 4-dimension rubric.\n\nINPUT:\n{user_payload}",
            ),
        ]

        # Get validator model (Claude Opus)
        model = get_validator_model()
        model_name = getattr(model, "model_name", getattr(model, "model", "opus"))

        # Invoke with structured output, capturing raw response for token tracking
        runnable = model.with_structured_output(ValidationResponse, strict=True, include_raw=True)
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

        logger.info(
            f"Validated {len(items)} items on attempt {attempt}. "
            f"Accepted: {sum(1 for v in result.validations if v.accept)}/{len(items)}. "
            f"Tokens: {usage.total_tokens}"
        )

        return result, usage

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise RuntimeError(f"Validation agent failed: {e}") from e
