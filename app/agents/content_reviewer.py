from __future__ import annotations

from typing import List

from app.agents.llm_utils import invoke_structured
from app.agents.prompt_loader import load_prompt
from app.schemas import ContentReviewResponse, DraftItem, ReviewComment, UserRequest
from app.settings import settings


def review_content(request: UserRequest, items: List[DraftItem], iteration: int) -> ContentReviewResponse:
    if settings.APP_MODE == "mock":
        return ContentReviewResponse(comments=[])

    system_prompt = load_prompt("content_reviewer.md")
    payload = {"user_request": request.model_dump(), "items": [i.model_dump() for i in items], "iteration": iteration}

    messages = [
        ("system", system_prompt),
        ("human", f"Review for content validity.\n\nINPUT:\n{payload}"),
    ]

    resp = invoke_structured(
        ContentReviewResponse,
        messages,
        agent_name="content_reviewer",
        model_provider=request.model_provider,
    )
    # Ensure comment.type is correct even if the model forgets.
    fixed = []
    for c in resp.comments:
        fixed.append(ReviewComment(**{**c.model_dump(), "type": "content"}))
    return ContentReviewResponse(comments=fixed)
