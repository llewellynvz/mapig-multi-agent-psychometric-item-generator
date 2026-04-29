from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional, Tuple

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

MetaEditorPhase = Literal["iterative", "expert_revision"]

_RATIONALE_MAX = 350


def _truncate_rationale(text: str, max_len: int = _RATIONALE_MAX) -> str:
    """Truncate rationale at the last sentence boundary within *max_len* chars.

    Falls back to hard truncation with ellipsis if no sentence boundary found.
    """
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    for sep in (". ", ".) ", "; "):
        last = truncated.rfind(sep)
        if last > 0:
            return truncated[: last + 1].rstrip()
    # No sentence boundary — hard cut
    return truncated[: max_len - 3].rstrip() + "..."


def _clamp_rationales(data: dict) -> dict:
    """Pre-validation hook: truncate any oversized rationale fields."""
    for item in data.get("revised_items", []):
        if isinstance(item, dict) and "rationale" in item:
            original = item["rationale"]
            item["rationale"] = _truncate_rationale(original)
            if len(original) > _RATIONALE_MAX:
                logger.warning(
                    "META_EDITOR rationale truncated from %d to %d chars",
                    len(original),
                    len(item["rationale"]),
                )
    return data


def revise_items(
    request: UserRequest,
    items: List[DraftItem],
    linguistic_comments: List[ReviewComment],
    bias_comments: List[ReviewComment],
    content_comments: List[ReviewComment],
    iteration: int,
    phase: MetaEditorPhase = "iterative",
    expert_consensus_revisions: Optional[RevisionPlan] = None,
) -> Tuple[MetaEditorResponse, TokenUsage]:

    """Apply reviewer feedback and produce revised items + a revision plan.

    Args:
        request: User construct specification.
        items: Current draft items.
        linguistic_comments: Comments from linguistic reviewer.
        bias_comments: Comments from bias reviewer.
        content_comments: Comments from content reviewer.
        iteration: 0-based iteration number.
        phase: "iterative" (default — runs in critic loop) or "expert_revision"
            (one-shot pass after expert panel; uses expert_consensus_revisions).
        expert_consensus_revisions: Required when phase="expert_revision". Lists
            items the expert panel flagged for refinement.
    """
    total_comments = len(linguistic_comments) + len(bias_comments) + len(content_comments)
    logger.info(
        "META_EDITOR start items=%d iteration=%d comments=%d phase=%s",
        len(items), iteration, total_comments, phase,
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

    payload: Dict[str, Any] = {
        "user_request": request.model_dump(),
        "items": [it.model_dump() for it in items],
        "linguistic_comments": [c.model_dump() for c in linguistic_comments],
        "bias_comments": [c.model_dump() for c in bias_comments],
        "content_comments": [c.model_dump() for c in content_comments],
        "phase": phase,
    }
    if phase == "expert_revision" and expert_consensus_revisions is not None:
        payload["expert_consensus_revisions"] = expert_consensus_revisions.model_dump()
        human_msg = (
            "Apply the expert panel's consensus revisions in ONE pass. "
            "Do not re-architect items. The critic loop will NOT re-run.\n\n"
            f"INPUT:\n{payload}"
        )
    else:
        human_msg = f"Revise the items using the reviewer feedback.\n\nINPUT:\n{payload}"

    messages = [
        ("system", system_prompt),
        ("human", human_msg),
    ]

    return invoke_structured_with_usage(
        MetaEditorResponse,
        messages,
        agent_name="meta_editor",
        model_provider=request.model_provider,
        pre_validate=_clamp_rationales,
    )
