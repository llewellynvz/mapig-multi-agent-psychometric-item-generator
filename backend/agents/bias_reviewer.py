from __future__ import annotations

from typing import List, Tuple

from backend.agents.llm_utils import invoke_structured_with_usage, TokenUsage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import AbbreviatedRequest, BiasReviewResponse, DraftItem, ReviewComment
from backend.settings import settings


def review_bias(request: AbbreviatedRequest, items: List[DraftItem], iteration: int) -> Tuple[BiasReviewResponse, TokenUsage]:
    """Bias/fairness review of items."""
    if settings.APP_MODE == "mock":
        # Mock: no bias issues for the stub items.
        return BiasReviewResponse(comments=[]), TokenUsage()

    system_prompt = load_prompt("bias_reviewer.md")

    payload = {
        "user_request": request.model_dump(),
        "items": [it.model_dump() for it in items],
    }
    messages = [
        ("system", system_prompt),
        ("human", f"Review these items for bias and fairness risks.\n\nINPUT:\n{payload}"),
    ]

    resp, usage = invoke_structured_with_usage(
        BiasReviewResponse,
        messages,
        agent_name="bias_reviewer",
        model_provider=request.model_provider,
        use_chatgpt_critics=request.use_chatgpt_critics,
    )

    # Safety: enforce comment type at runtime.
    for c in resp.comments:
        c.type = "bias"
    return resp, usage
