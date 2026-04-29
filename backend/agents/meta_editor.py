from __future__ import annotations

import logging
import re
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


_NEGATION_PATTERN = re.compile(
    r"\b(not|never|no)\b|n['’]t\b",
    flags=re.IGNORECASE,
)


def _contains_negation(text: str) -> bool:
    """Return True if the text contains negation tokens (not/never/no/n't)."""
    return bool(_NEGATION_PATTERN.search(text or ""))


def _enforce_positive_keying(
    request: UserRequest,
    original_items: List[DraftItem],
    revised_items: List[DraftItem],
) -> List[DraftItem]:
    """If `request.constraints` includes "Positively keyed only", revert any
    revised item that introduces negation tokens (not/never/no/n't) when the
    corresponding original item did NOT contain them.

    The original item may itself be a system-generated mock and could contain
    "not" innocently — only revert when the LLM ADDED a negation.
    """
    if not any("Positively keyed only" in c for c in (request.constraints or [])):
        return revised_items

    out: List[DraftItem] = []
    leaks = 0
    for idx, rev in enumerate(revised_items):
        orig = original_items[idx] if idx < len(original_items) else None
        if (
            orig is not None
            and _contains_negation(rev.item_text)
            and not _contains_negation(orig.item_text)
        ):
            logger.warning(
                "META_EDITOR_NEGATION_LEAK item_index=%d original=%r revised=%r — reverting to original",
                idx, orig.item_text, rev.item_text,
            )
            # Preserve any other revision metadata (rationale/citations) from the
            # LLM, but restore the original item_text + construct_name so the
            # polarity constraint is honored.
            try:
                reverted = rev.model_copy(update={
                    "item_text": orig.item_text,
                    "construct_name": orig.construct_name,
                })
            except Exception:
                reverted = orig
            out.append(reverted)
            leaks += 1
        else:
            out.append(rev)

    if leaks:
        logger.warning("META_EDITOR_NEGATION_LEAKS_TOTAL count=%d", leaks)
    return out


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

    resp, usage = invoke_structured_with_usage(
        MetaEditorResponse,
        messages,
        agent_name="meta_editor",
        model_provider=request.model_provider,
        pre_validate=_clamp_rationales,
    )

    # Post-edit polarity enforcement: revert any item where the LLM introduced
    # a negation despite a "Positively keyed only" constraint.
    enforced_items = _enforce_positive_keying(request, items, resp.revised_items)
    if enforced_items is not resp.revised_items:
        resp = resp.model_copy(update={"revised_items": enforced_items})

    return resp, usage
