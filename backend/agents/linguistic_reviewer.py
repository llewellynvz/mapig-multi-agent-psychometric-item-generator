from __future__ import annotations

import logging
from typing import List, Tuple

from backend.agents.llm_utils import invoke_structured_with_usage, truncate_review_comment_fields, TokenUsage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import AbbreviatedRequest, DraftItem, LinguisticReviewResponse, ReviewComment
from backend.settings import settings

logger = logging.getLogger("lmaig.linguistic_reviewer")


def review_linguistic(
    request: AbbreviatedRequest, items: List[DraftItem], iteration: int, previous_comments: dict | None = None
) -> Tuple[LinguisticReviewResponse, TokenUsage]:
    """Linguistic review of items."""
    logger.info("LINGUISTIC_REVIEWER start items=%d iteration=%d", len(items), iteration)
    if settings.APP_MODE == "mock":
        # Deterministic: force one revision loop by emitting a single medium-severity issue on iteration 0.
        if iteration == 0 and items:
            return LinguisticReviewResponse(
                comments=[
                    ReviewComment(
                        type="linguistic",
                        issue="The item is too generic and repeats the same stem across items, reducing content coverage.",
                        severity=3,
                        suggested_edit="Vary the wording and target different facets of the construct across items.",
                    )
                ]
            ), TokenUsage()
        return LinguisticReviewResponse(comments=[]), TokenUsage()

    system_prompt = load_prompt("linguistic_reviewer.md")

    payload = {
        "user_request": request.model_dump(),
        "items": [it.model_dump() for it in items],
        "iteration": iteration,
    }
    if previous_comments and "linguistic" in previous_comments:
        payload["previous_comments"] = previous_comments["linguistic"]
    messages = [
        ("system", system_prompt),
        ("human", f"Review these items for linguistic quality.\n\nINPUT:\n{payload}"),
    ]

    resp, usage = invoke_structured_with_usage(
        LinguisticReviewResponse,
        messages,
        agent_name="linguistic_reviewer",
        model_provider=request.model_provider,
        use_chatgpt_critics=request.use_chatgpt_critics,
        pre_validate=truncate_review_comment_fields,
    )

    # Safety: enforce comment type at runtime.
    for c in resp.comments:
        c.type = "linguistic"
    logger.info("LINGUISTIC_REVIEWER done comments=%d tokens=%d", len(resp.comments), usage.total_tokens)
    return resp, usage
