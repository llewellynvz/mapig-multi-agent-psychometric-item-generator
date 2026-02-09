from __future__ import annotations

from typing import List, Literal, Tuple

from pydantic import BaseModel, ConfigDict, Field

from app.agents.llm_utils import invoke_structured
from app.agents.prompt_loader import load_prompt
from app.schemas import ReviewComment
from app.settings import settings

Decision = Literal["accept", "revise", "stop_max_iterations", "needs_human"]


class CriticResponse(BaseModel):
    """LLM output contract for the critic."""
    model_config = ConfigDict(extra="forbid")

    decision: Decision = Field(..., description="Routing decision for the workflow.")
    reason: str = Field(..., min_length=3, description="Short justification for the decision.")


def _max_severity(comments: List[ReviewComment]) -> int:
    return max((int(c.severity) for c in comments), default=0)


def _count_medium_plus(comments: List[ReviewComment]) -> int:
    return sum(1 for c in comments if int(c.severity) >= 3)


def _rule_based_fallback(
    linguistic_comments: List[ReviewComment],
    bias_comments: List[ReviewComment],
    content_comments: List[ReviewComment],
    iteration: int,
) -> Tuple[Decision, str]:
    """Fallback if LLM critic fails."""
    all_comments = list(linguistic_comments) + list(bias_comments) + list(content_comments)

    if not all_comments:
        return "accept", "No review issues detected."

    max_sev = _max_severity(all_comments)
    med_plus = _count_medium_plus(all_comments)

    if iteration >= settings.MAX_ITERATIONS:
        return "stop_max_iterations", "Reached MAX_ITERATIONS before all medium+ issues were resolved."

    if max_sev >= 5:
        return "revise", f"Blocking issue(s) detected (max severity {max_sev})."

    # Early stopping: be more lenient on iteration 2+ (accept severity <= 3 instead of <= 2)
    base_threshold = getattr(settings, "CRITIC_MAX_SEVERITY_TO_ACCEPT", 2)
    effective_threshold = base_threshold if iteration < 2 else 3

    if med_plus >= 1 and max_sev > effective_threshold:
        return "revise", f"Medium+ issues detected (count {med_plus}, max severity {max_sev})."

    return "accept", f"Acceptable quality threshold met (max severity {max_sev}, threshold {effective_threshold})."


def decide(
    linguistic_comments: List[ReviewComment],
    bias_comments: List[ReviewComment],
    content_comments: List[ReviewComment],
    iteration: int,
) -> Tuple[Decision, str]:
    """
    LLM-based critic.

    Returns: (decision, reason)
    """

    # Hard stop is still enforced to prevent infinite looping.
    if iteration >= settings.MAX_ITERATIONS:
        return "stop_max_iterations", "Reached MAX_ITERATIONS before all medium+ issues were resolved."

    # Mock mode should not call external LLMs.
    if settings.APP_MODE == "mock":
        return _rule_based_fallback(linguistic_comments, bias_comments, content_comments, iteration)

    all_comments = list(linguistic_comments) + list(bias_comments) + list(content_comments)

    # If nothing to review, accept immediately (saves tokens and reduces variability).
    if not all_comments:
        return "accept", "No review issues detected."

    system_prompt = load_prompt("critic.md")

    # Early stopping: be more lenient on iteration 2+ (accept severity <= 3 instead of <= 2)
    base_threshold = getattr(settings, "CRITIC_MAX_SEVERITY_TO_ACCEPT", 2)
    effective_threshold = base_threshold if iteration < 2 else 3

    payload = {
        "iteration": iteration,
        "max_iterations": settings.MAX_ITERATIONS,
        "critic_max_severity_to_accept": effective_threshold,
        "linguistic_comments": [c.model_dump() for c in linguistic_comments],
        "bias_comments": [c.model_dump() for c in bias_comments],
        "content_comments": [c.model_dump() for c in content_comments],
    }

    messages = [
        ("system", system_prompt),
        ("human", f"Decide whether to revise again or finalize.\n\nINPUT:\n{payload}"),
    ]

    try:
        resp = invoke_structured(CriticResponse, messages)
        return resp.decision, resp.reason
    except Exception as e:
        # If the LLM misbehaves, fall back to deterministic logic so the system keeps running.
        d, r = _rule_based_fallback(linguistic_comments, bias_comments, content_comments, iteration)
        return d, f"{r} (LLM critic failed; fallback used: {type(e).__name__})"
