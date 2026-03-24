"""Test suite for Critic agent adaptive thresholds.

This module tests the Critic agent's adaptive threshold logic that adjusts
acceptance criteria based on iteration number (AGT-10).

Threshold boundaries (0-based iteration):
  iter=0  → strict  (accept_max_severity=2, medium_plus_count=0)
  iter=1  → thorough (accept_max_severity=3, medium_plus_count=1)
  iter=2+ → final   (accept_max_severity=4, medium_plus_count=3)
"""

import pytest


# AGT-10: Critic adaptive thresholds
def test_adaptive_thresholds_strict():
    """Iteration 0 uses strict thresholds (most conservative)."""
    from backend.agents.critic import get_adaptive_thresholds

    t = get_adaptive_thresholds(iteration=0, max_iterations=3)

    assert t["mode"] == "strict"
    assert t["bias_blocker"] == 3
    assert t["content_blocker"] == 3
    assert t["accept_max_severity"] == 2
    assert t["accept_medium_plus_count"] == 0


def test_adaptive_thresholds_thorough():
    """Iteration 1 uses thorough thresholds (balanced)."""
    from backend.agents.critic import get_adaptive_thresholds

    t = get_adaptive_thresholds(iteration=1, max_iterations=3)

    assert t["mode"] == "thorough"
    assert t["bias_blocker"] == 3
    assert t["content_blocker"] == 4
    assert t["accept_max_severity"] == 3
    assert t["accept_medium_plus_count"] == 1


def test_adaptive_thresholds_final():
    """Iteration 2+ uses relaxed final thresholds."""
    from backend.agents.critic import get_adaptive_thresholds

    t2 = get_adaptive_thresholds(iteration=2, max_iterations=3)
    t5 = get_adaptive_thresholds(iteration=5, max_iterations=6)

    for t in (t2, t5):
        assert t["mode"] == "final"
        assert t["bias_blocker"] == 5
        assert t["content_blocker"] == 5
        assert t["accept_max_severity"] == 4
        assert t["accept_medium_plus_count"] == 3


def test_thorough_mode_rejects_severity_3():
    """In thorough mode (iter=1), severity-3 issues must trigger revision.

    This was the core bug: the old ordering let accept fire before force-revision,
    silently accepting severity-3 feedback.
    """
    from backend.agents.critic import decide
    from backend.schemas import ReviewComment

    comments = [
        ReviewComment(
            type="linguistic",
            item_index=0,
            issue="Vague quantifier detected",
            severity=3,
            suggested_edit="Add time anchor",
        )
    ]

    decision, reason = decide(
        linguistic_comments=comments,
        bias_comments=[],
        content_comments=[],
        iteration=1,  # thorough mode
    )

    assert decision == "revise", (
        f"Thorough mode should revise on severity=3, got '{decision}': {reason}"
    )


def test_strict_mode_rejects_severity_3():
    """In strict mode (iter=0), severity-3 issues must trigger revision."""
    from backend.agents.critic import decide
    from backend.schemas import ReviewComment

    comments = [
        ReviewComment(
            type="bias",
            item_index=0,
            issue="Cultural bias detected",
            severity=3,
            suggested_edit="Rewrite without bias",
        )
    ]

    decision, reason = decide(
        linguistic_comments=[],
        bias_comments=comments,
        content_comments=[],
        iteration=0,  # strict mode
    )

    assert decision == "revise", (
        f"Strict mode should revise on severity=3, got '{decision}': {reason}"
    )


def test_final_mode_accepts_severity_3():
    """In final mode (iter=2), severity-3 with 1 medium+ should be accepted."""
    from backend.agents.critic import decide
    from backend.schemas import ReviewComment

    comments = [
        ReviewComment(
            type="linguistic",
            item_index=0,
            issue="Minor quantifier issue",
            severity=3,
            suggested_edit="Add time anchor",
        )
    ]

    decision, reason = decide(
        linguistic_comments=comments,
        bias_comments=[],
        content_comments=[],
        iteration=2,  # at MAX_ITERATIONS boundary
    )

    # With MAX_ITERATIONS=2, iteration=2 triggers stop_max_iterations (force-accept)
    assert decision in ("accept", "stop_max_iterations"), (
        f"At max iterations should accept or stop, got '{decision}': {reason}"
    )


def test_threshold_mode_in_reason():
    """Critic decision reason includes threshold mode context."""
    from backend.agents.critic import decide
    from backend.schemas import ReviewComment

    comments = [
        ReviewComment(
            type="linguistic",
            item_index=0,
            issue="Vague quantifier detected",
            severity=3,
            suggested_edit="Add time anchor",
        )
    ]

    # Test strict iteration
    _, reason_strict = decide(
        linguistic_comments=comments,
        bias_comments=[],
        content_comments=[],
        iteration=0,
    )
    assert "iteration 0/" in reason_strict.lower()
    assert "strict" in reason_strict.lower() or "mode" in reason_strict.lower()

    # Test final iteration
    _, reason_final = decide(
        linguistic_comments=comments,
        bias_comments=[],
        content_comments=[],
        iteration=2,
    )
    assert "iteration 2/" in reason_final.lower()
    assert "final" in reason_final.lower() or "mode" in reason_final.lower()
