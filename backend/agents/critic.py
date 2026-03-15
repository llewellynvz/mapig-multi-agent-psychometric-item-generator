from __future__ import annotations

import logging
from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from backend.agents.llm_utils import invoke_structured
from backend.agents.prompt_loader import load_prompt
from backend.schemas import IterationSnapshot, ReviewComment
from backend.settings import settings

logger = logging.getLogger("lmaig.critic")

Decision = Literal["accept", "revise", "stop_max_iterations", "needs_human"]


class CriticResponse(BaseModel):
    """LLM output contract for the critic."""
    model_config = ConfigDict(extra="forbid")

    decision: Decision = Field(..., description="Routing decision for the workflow.")
    reason: str = Field(..., min_length=3, description="Short justification for the decision.")


def get_adaptive_thresholds(iteration: int, max_iterations: int) -> dict:
    """Calculate thresholds based on iteration progress.

    Round 1 (iter=0) is strict so major issues get caught early.
    Round 2 (iter=1) is thorough — accepts if reasonably clean.
    Round 3 (iter=2) is a relaxed safety net that accepts almost anything.

    Args:
        iteration: Current iteration number (0-based)
        max_iterations: Maximum allowed iterations

    Returns:
        dict with keys: mode, bias_blocker, content_blocker,
                       accept_max_severity, accept_medium_plus_count
    """
    if iteration <= 0:
        # Round 1: strictest — force revision on any medium+ issue
        return {
            "mode": "strict",
            "bias_blocker": 3,
            "content_blocker": 3,
            "accept_max_severity": 2,
            "accept_medium_plus_count": 0
        }
    elif iteration <= 1:
        # Round 2: thorough — revise on high severity, tolerate 1 medium
        return {
            "mode": "thorough",
            "bias_blocker": 3,
            "content_blocker": 4,
            "accept_max_severity": 3,
            "accept_medium_plus_count": 1
        }
    else:
        # Round 3+: relaxed safety net — only block on critical issues
        return {
            "mode": "final",
            "bias_blocker": 5,
            "content_blocker": 5,
            "accept_max_severity": 4,
            "accept_medium_plus_count": 3
        }


def _max_severity(comments: List[ReviewComment]) -> int:
    return max((int(c.severity) for c in comments), default=0)


def _count_medium_plus(comments: List[ReviewComment]) -> int:
    return sum(1 for c in comments if int(c.severity) >= 3)


def _format_threshold_context(iteration: int, max_iterations: int, mode: str) -> str:
    """Format threshold mode context for decision reasons."""
    return f"Iteration {iteration}/{max_iterations}: threshold mode {mode}"


def _jaccard_word_similarity(a: str, b: str) -> float:
    """Word-level Jaccard similarity between two strings."""
    words_a = set(a.strip().lower().split())
    words_b = set(b.strip().lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0


def _comments_similarity(comments_a: List[ReviewComment], comments_b: List[ReviewComment]) -> float:
    """Mean pairwise Jaccard similarity between two sets of comments.

    Pairs each comment in A with its best-matching comment in B,
    then returns the mean of best-match similarities.
    """
    if not comments_a or not comments_b:
        return 0.0

    issues_a = [c.issue.strip().lower() for c in comments_a]
    issues_b = [c.issue.strip().lower() for c in comments_b]

    best_matches = []
    for a in issues_a:
        best = max(_jaccard_word_similarity(a, b) for b in issues_b)
        best_matches.append(best)

    return sum(best_matches) / len(best_matches) if best_matches else 0.0


def _detect_stagnation(
    current_comments: List[ReviewComment],
    iteration_history: Optional[List[IterationSnapshot]],
    iteration: int,
) -> bool:
    """Detect if reviewer comments are stagnant (paraphrased repetition).

    Uses Jaccard word-level similarity (threshold 0.7) instead of MD5 hash
    to catch paraphrased repetition (e.g., "satisfactory" → "good").
    Triggers at iteration >= 1 (one round earlier than before).
    """
    if iteration < 1 or not iteration_history:
        return False
    # Get previous iteration's combined comments
    prev_snap = iteration_history[-1]
    prev_comments = (
        list(prev_snap.linguistic_comments)
        + list(prev_snap.bias_comments)
        + list(prev_snap.content_comments)
    )
    if not prev_comments:
        return False
    similarity = _comments_similarity(current_comments, prev_comments)
    if similarity >= 0.7:
        logger.info("STAGNATION_DETECTED similarity=%.2f iteration=%d", similarity, iteration)
        return True
    return False


def _downgrade_construct_level_bias(bias_comments: List[ReviewComment]) -> List[ReviewComment]:
    """Downgrade bias comments to severity 1 if ALL are construct-level.

    If all bias comments have mean pairwise Jaccard similarity > 0.6,
    they represent construct-level concerns (not item-level) and should
    be downgraded to severity 1 (not actionable).
    """
    if len(bias_comments) < 2:
        return bias_comments

    issues = [c.issue.strip().lower() for c in bias_comments]
    similarities = []
    for i in range(len(issues)):
        for j in range(i + 1, len(issues)):
            similarities.append(_jaccard_word_similarity(issues[i], issues[j]))

    mean_sim = sum(similarities) / len(similarities) if similarities else 0.0

    if mean_sim > 0.6:
        logger.info(
            "CONSTRUCT_LEVEL_BIAS_DOWNGRADE mean_jaccard=%.2f comments=%d — downgrading to severity 1",
            mean_sim, len(bias_comments),
        )
        for c in bias_comments:
            c.severity = 1
    return bias_comments


def _rule_based_fallback(
    linguistic_comments: List[ReviewComment],
    bias_comments: List[ReviewComment],
    content_comments: List[ReviewComment],
    iteration: int,
    iteration_history: Optional[List[IterationSnapshot]] = None,
) -> Tuple[Decision, str]:
    """Fallback if LLM critic fails."""
    # Downgrade construct-level bias before threshold checks
    bias_comments = _downgrade_construct_level_bias(list(bias_comments))

    all_comments = list(linguistic_comments) + list(bias_comments) + list(content_comments)

    # Get adaptive thresholds
    thresholds = get_adaptive_thresholds(iteration, settings.MAX_ITERATIONS)

    threshold_ctx = _format_threshold_context(iteration, settings.MAX_ITERATIONS, thresholds['mode'])

    if not all_comments:
        return "accept", f"No review issues detected. {threshold_ctx}"

    max_sev = _max_severity(all_comments)
    med_plus = _count_medium_plus(all_comments)

    # Step 1: Check max iterations
    if iteration >= settings.MAX_ITERATIONS:
        return "stop_max_iterations", f"Reached MAX_ITERATIONS before all medium+ issues were resolved. {threshold_ctx}"

    # Step 1b: Stagnation detection (identical comments across iterations)
    if _detect_stagnation(all_comments, iteration_history, iteration):
        return "accept", f"Stagnation detected: identical issues across iterations — accepting current quality. {threshold_ctx}"

    # Step 2: Force revision in strict/thorough mode on severity >= 3
    if thresholds['mode'] in ('strict', 'thorough') and max_sev >= 3:
        return "revise", f"Medium+ issues in {thresholds['mode']} mode (max severity {max_sev}). {threshold_ctx}"

    # Step 3: Check severity 5 blockers
    if max_sev >= 5:
        return "revise", f"Blocking issue(s) detected (max severity {max_sev}). {threshold_ctx}"

    # Step 4: Check bias blocker threshold (adaptive)
    bias_max_sev = _max_severity(bias_comments)
    if bias_max_sev >= thresholds['bias_blocker']:
        return "revise", f"Bias issues ≥{thresholds['bias_blocker']}. {threshold_ctx}"

    # Step 5: Check content blocker threshold (adaptive)
    content_max_sev = _max_severity(content_comments)
    if content_max_sev >= thresholds['content_blocker']:
        return "revise", f"Content issues ≥{thresholds['content_blocker']}. {threshold_ctx}"

    # Step 6: Check convergence (adaptive thresholds)
    if med_plus >= 1 and max_sev > thresholds['accept_max_severity']:
        return "revise", f"Medium+ issues detected (count {med_plus}, max severity {max_sev}). {threshold_ctx}"

    return "accept", f"Acceptable quality threshold met (max severity {max_sev}, threshold {thresholds['accept_max_severity']}). {threshold_ctx}"


def decide(
    linguistic_comments: List[ReviewComment],
    bias_comments: List[ReviewComment],
    content_comments: List[ReviewComment],
    iteration: int,
    model_provider: str = "claude",
    use_chatgpt_critics: bool = False,
    iteration_history: Optional[List[IterationSnapshot]] = None,
) -> Tuple[Decision, str]:
    """
    LLM-based critic with adaptive thresholds and rule-based optimization.

    Cost optimization: Uses deterministic logic for clear accept/reject cases,
    only invoking LLM for borderline decisions (severity = 3).

    Returns: (decision, reason)
    """

    # Get adaptive thresholds
    thresholds = get_adaptive_thresholds(iteration, settings.MAX_ITERATIONS)
    threshold_ctx = _format_threshold_context(iteration, settings.MAX_ITERATIONS, thresholds['mode'])

    # Hard stop is still enforced to prevent infinite looping.
    if iteration >= settings.MAX_ITERATIONS:
        return "stop_max_iterations", f"Reached MAX_ITERATIONS before all medium+ issues were resolved. {threshold_ctx}"

    # Mock mode should not call external LLMs.
    if settings.APP_MODE == "mock":
        return _rule_based_fallback(linguistic_comments, bias_comments, content_comments, iteration, iteration_history)

    # Downgrade construct-level bias before threshold checks
    bias_comments = _downgrade_construct_level_bias(list(bias_comments))

    all_comments = list(linguistic_comments) + list(bias_comments) + list(content_comments)

    # If nothing to review, accept immediately (saves tokens and reduces variability).
    if not all_comments:
        return "accept", f"No review issues detected. {threshold_ctx}"

    # 1F: Stagnation detection — identical comments despite revision
    if _detect_stagnation(all_comments, iteration_history, iteration):
        return "accept", f"Stagnation detected: identical issues across iterations — accepting current quality. {threshold_ctx} [rule-based, 0 tokens]"

    # Rule-based optimization: Handle clear cases without LLM invocation
    if settings.RULE_BASED_CRITIC_ENABLED:
        max_sev = _max_severity(all_comments)
        med_plus = _count_medium_plus(all_comments)

        # Force revision first: In strict/thorough mode, severity>=3 must be revised
        # This MUST come before the accept check to prevent severity-3 issues from
        # being silently accepted when they happen to match threshold boundaries.
        if thresholds['mode'] in ('strict', 'thorough') and max_sev >= 3:
            return "revise", f"Medium+ issues detected in {thresholds['mode']} mode (max: {max_sev}, medium+: {med_plus}). {threshold_ctx} [rule-based, 0 tokens]"

        # Clear reject: Issues exceed current adaptive threshold — force revision
        if max_sev > thresholds['accept_max_severity']:
            return "revise", f"High-severity issues detected (max: {max_sev}, threshold: {thresholds['accept_max_severity']}). Revision required. {threshold_ctx} [rule-based, 0 tokens]"

        # Clear accept: All feedback below acceptance threshold
        if max_sev <= thresholds['accept_max_severity'] and med_plus <= thresholds['accept_medium_plus_count']:
            return "accept", f"All feedback within threshold (max: {max_sev}, medium+: {med_plus}). {threshold_ctx} [rule-based, 0 tokens]"

        # Borderline case: Fall through to LLM for nuanced judgment

    system_prompt = load_prompt("critic.md")

    payload = {
        "iteration": iteration,
        "max_iterations": settings.MAX_ITERATIONS,
        "critic_max_severity_to_accept": thresholds['accept_max_severity'],
        "bias_blocker": thresholds['bias_blocker'],
        "content_blocker": thresholds['content_blocker'],
        "threshold_mode": thresholds['mode'],
        "linguistic_comments": [c.model_dump() for c in linguistic_comments],
        "bias_comments": [c.model_dump() for c in bias_comments],
        "content_comments": [c.model_dump() for c in content_comments],
    }

    messages = [
        ("system", system_prompt),
        ("human", f"Decide whether to revise again or finalize.\n\nINPUT:\n{payload}"),
    ]

    try:
        resp = invoke_structured(
            CriticResponse,
            messages,
            agent_name="critic",
            model_provider=model_provider,
            use_chatgpt_critics=use_chatgpt_critics,
        )
        # Ensure threshold mode is in the reason
        reason_with_mode = f"{resp.reason} {threshold_ctx} [LLM-based]"
        return resp.decision, reason_with_mode
    except Exception as e:
        # If the LLM misbehaves, fall back to deterministic logic so the system keeps running.
        d, r = _rule_based_fallback(linguistic_comments, bias_comments, content_comments, iteration, iteration_history)
        return d, f"{r} (LLM critic failed; fallback used: {type(e).__name__})"
