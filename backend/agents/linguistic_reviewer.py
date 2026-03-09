from __future__ import annotations

from typing import List

from backend.agents.llm_utils import invoke_structured
from backend.agents.prompt_loader import load_prompt
from backend.schemas import DraftItem, LinguisticReviewResponse, ReviewComment, UserRequest
from backend.settings import settings


def review_linguistic(
    request: UserRequest, items: List[DraftItem], iteration: int
) -> LinguisticReviewResponse:
    """Linguistic review of items."""
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
            )
        return LinguisticReviewResponse(comments=[])

    system_prompt = load_prompt("linguistic_reviewer.md")

    payload = {
        "user_request": request.model_dump(),
        "items": [it.model_dump() for it in items],
    }
    messages = [
        ("system", system_prompt),
        ("human", f"Review these items for linguistic quality.\n\nINPUT:\n{payload}"),
    ]

    resp = invoke_structured(
        LinguisticReviewResponse,
        messages,
        agent_name="linguistic_reviewer",
        model_provider=request.model_provider,
    )

    # Safety: enforce comment type at runtime.
    for c in resp.comments:
        c.type = "linguistic"
    return resp
