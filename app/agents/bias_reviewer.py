from __future__ import annotations

from typing import List

from app.agents.llm_utils import invoke_structured
from app.agents.prompt_loader import load_prompt
from app.schemas import BiasReviewResponse, DraftItem, ReviewComment, UserRequest
from app.settings import settings


def review_bias(request: UserRequest, items: List[DraftItem], iteration: int) -> BiasReviewResponse:
    """Bias/fairness review of items."""
    if settings.APP_MODE == "mock":
        # Mock: no bias issues for the stub items.
        return BiasReviewResponse(comments=[])

    system_prompt = load_prompt("bias_reviewer.md")

    payload = {
        "user_request": request.model_dump(),
        "items": [it.model_dump() for it in items],
    }
    messages = [
        ("system", system_prompt),
        ("human", f"Review these items for bias and fairness risks.\n\nINPUT:\n{payload}"),
    ]

    resp = invoke_structured(
        BiasReviewResponse,
        messages,
        agent_name="bias_reviewer",
        model_provider=request.model_provider,
    )

    # Safety: enforce comment type at runtime.
    for c in resp.comments:
        c.type = "bias"
    return resp
