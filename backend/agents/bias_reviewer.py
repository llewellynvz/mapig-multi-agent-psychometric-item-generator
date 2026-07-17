from __future__ import annotations

import logging
from typing import List, Tuple

from backend.agents.llm_utils import invoke_structured_with_usage, truncate_review_comment_fields, TokenUsage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import AbbreviatedRequest, BiasReviewResponse, DraftItem, ReviewComment
from backend.settings import settings

logger = logging.getLogger("lmaig.bias_reviewer")


def _jaccard_word_similarity(a: str, b: str) -> float:
    """Word-level Jaccard similarity between two strings."""
    words_a = set(a.strip().lower().split())
    words_b = set(b.strip().lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0


def _filter_construct_level_comments(
    comments: List[ReviewComment], item_count: int
) -> List[ReviewComment]:
    """Filter out construct-level false positives.

    If >60% of items receive comments with Jaccard word similarity >0.5,
    the concerns are construct-level (apply to all items equally) and
    should be suppressed.
    """
    if not comments or item_count == 0:
        return comments

    # Group comments by item_index
    by_item: dict[int, List[ReviewComment]] = {}
    for c in comments:
        idx = c.item_index if c.item_index is not None else -1
        by_item.setdefault(idx, []).append(c)

    items_with_comments = len([k for k in by_item if k >= 0])
    ratio = items_with_comments / item_count if item_count > 0 else 0.0

    if ratio <= 0.6:
        return comments

    # Check pairwise Jaccard similarity of issue texts across items
    issue_texts = []
    for idx in sorted(by_item):
        if idx < 0:
            continue
        for c in by_item[idx]:
            issue_texts.append(c.issue)

    if len(issue_texts) < 2:
        return comments

    # Calculate mean pairwise similarity
    similarities = []
    for i in range(len(issue_texts)):
        for j in range(i + 1, len(issue_texts)):
            similarities.append(_jaccard_word_similarity(issue_texts[i], issue_texts[j]))

    mean_similarity = sum(similarities) / len(similarities) if similarities else 0.0

    if mean_similarity > 0.5:
        logger.info(
            "BIAS_CONSTRUCT_LEVEL_FILTER triggered: %d/%d items flagged, "
            "mean Jaccard=%.2f — suppressing construct-level false positives",
            items_with_comments, item_count, mean_similarity,
        )
        return []

    return comments


def review_bias(request: AbbreviatedRequest, items: List[DraftItem], iteration: int, previous_comments: dict | None = None) -> Tuple[BiasReviewResponse, TokenUsage]:
    """Bias/fairness review of items."""
    logger.info("BIAS_REVIEWER start items=%d iteration=%d", len(items), iteration)
    if settings.APP_MODE == "mock":
        # Mock: no bias issues for the stub items.
        return BiasReviewResponse(comments=[]), TokenUsage()

    system_prompt = load_prompt("bias_reviewer.md")

    payload = {
        "user_request": request.model_dump(),
        "items": [it.model_dump() for it in items],
        "iteration": iteration,
    }
    if previous_comments and "bias" in previous_comments:
        payload["previous_comments"] = previous_comments["bias"]
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
        pre_validate=truncate_review_comment_fields,
    )

    # Safety: enforce comment type at runtime.
    for c in resp.comments:
        c.type = "bias"

    # Post-processing: filter construct-level false positives
    resp.comments = _filter_construct_level_comments(resp.comments, len(items))

    logger.info("BIAS_REVIEWER done comments=%d tokens=%d", len(resp.comments), usage.total_tokens)
    return resp, usage
