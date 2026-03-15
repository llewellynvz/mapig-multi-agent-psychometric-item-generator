from __future__ import annotations

import logging
from typing import List, Tuple

from backend.agents.llm_utils import invoke_structured_with_usage, TokenUsage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import (
    DraftItem,
    MetaEditorResponse,
    RevisionEdit,
    RevisionPlan,
    ReviewComment,
    UserRequest,
)
from backend.settings import settings

logger = logging.getLogger("lmaig.meta_editor")


def revise_items(
    request: UserRequest,
    items: List[DraftItem],
    linguistic_comments: List[ReviewComment],
    bias_comments: List[ReviewComment],
    content_comments: List[ReviewComment],
    iteration: int,
) -> Tuple[MetaEditorResponse, TokenUsage]:

    """Apply reviewer feedback and produce revised items + a revision plan."""
    total_comments = len(linguistic_comments) + len(bias_comments) + len(content_comments)
    logger.info(
        "META_EDITOR start items=%d iteration=%d comments=%d",
        len(items), iteration, total_comments,
    )
    if settings.APP_MODE == "mock":

        # Deterministic revision: diversify stems.
        revised: List[DraftItem] = []
        stems = [
            "I feel accepted by the people I work with.",
            "I can be myself at work without negative consequences.",
            "I feel included in important conversations at work.",
            "People at work value my contributions.",
            "I feel like I fit in with my team.",
            "I feel connected to my workplace community.",
        ]
        for idx, it in enumerate(items):
            new_text = stems[idx % len(stems)]
            revised.append(
                DraftItem(
                    item_text=new_text,
                    construct_name=it.construct_name,
                    rationale="Reworded to increase content coverage and reduce redundancy.",
                    evidence_citations=it.evidence_citations,
                )
            )

        edits = []
        if items:
            edits.append(
                RevisionEdit(
                    item_index=0,
                    reason="Reduce redundancy and improve content coverage.",
                    before=items[0].item_text,
                    after=revised[0].item_text,
                )
            )

        return MetaEditorResponse(
            revision_plan=RevisionPlan(edits=edits),
            revised_items=revised,
        ), TokenUsage()

    system_prompt = load_prompt("meta_editor.md")

    payload = {
        "user_request": request.model_dump(),
        "items": [it.model_dump() for it in items],
        "linguistic_comments": [c.model_dump() for c in linguistic_comments],
        "bias_comments": [c.model_dump() for c in bias_comments],
        "content_comments": [c.model_dump() for c in content_comments],
    }
    messages = [
        ("system", system_prompt),
        ("human", f"Revise the items using the reviewer feedback.\n\nINPUT:\n{payload}"),
    ]

    return invoke_structured_with_usage(
        MetaEditorResponse,
        messages,
        agent_name="meta_editor",
        model_provider=request.model_provider,
    )
