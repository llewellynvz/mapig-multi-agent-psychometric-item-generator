from __future__ import annotations

import logging
from typing import List, Tuple

from backend.agents.llm_utils import invoke_structured_with_usage, TokenUsage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import AbbreviatedRequest, ContentReviewResponse, DraftItem, ReviewComment
from backend.settings import settings

logger = logging.getLogger("lmaig.content_reviewer")


def review_content(request: AbbreviatedRequest, items: List[DraftItem], iteration: int, previous_comments: dict | None = None) -> Tuple[ContentReviewResponse, TokenUsage]:
    logger.info("CONTENT_REVIEWER start items=%d iteration=%d", len(items), iteration)
    if settings.APP_MODE == "mock":
        return ContentReviewResponse(comments=[]), TokenUsage()

    system_prompt = load_prompt("content_reviewer.md")
    payload = {"user_request": request.model_dump(), "items": [i.model_dump() for i in items], "iteration": iteration}
    if previous_comments and "content" in previous_comments:
        payload["previous_comments"] = previous_comments["content"]

    messages = [
        ("system", system_prompt),
        ("human", f"Review for content validity.\n\nINPUT:\n{payload}"),
    ]

    resp, usage = invoke_structured_with_usage(
        ContentReviewResponse,
        messages,
        agent_name="content_reviewer",
        model_provider=request.model_provider,
        use_chatgpt_critics=request.use_chatgpt_critics,
    )
    # Ensure comment.type is correct even if the model forgets.
    fixed = []
    for c in resp.comments:
        fixed.append(ReviewComment(**{**c.model_dump(), "type": "content"}))
    logger.info("CONTENT_REVIEWER done comments=%d tokens=%d", len(fixed), usage.total_tokens)
    return ContentReviewResponse(comments=fixed), usage
