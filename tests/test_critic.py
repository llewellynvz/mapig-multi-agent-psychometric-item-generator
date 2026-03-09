"""Test suite for Critic agent adaptive thresholds.

This module tests the Critic agent's adaptive threshold logic that adjusts
acceptance criteria based on iteration number (AGT-10).
"""

import pytest


# AGT-10: Critic adaptive thresholds
def test_adaptive_thresholds_early_iteration():
    """Test AGT-10: Verify early iterations (1-2) use stricter thresholds.

    Per research, early iterations should be more conservative to ensure
    high-quality items are prioritized.

    Expected thresholds for iterations 1-2:
    - bias_blocker = 4 (block on severity ≥4)
    - content_blocker = 4 (block on severity ≥4)
    - accept_max_severity = 2 (accept only if max severity ≤2)

    Expected behavior:
    - get_adaptive_thresholds(1) returns strict thresholds
    - get_adaptive_thresholds(2) returns strict thresholds
    - Thresholds stricter than mid/late iterations
    """
    from backend.agents.critic import get_adaptive_thresholds

    # Early iteration thresholds
    thresholds_iter1 = get_adaptive_thresholds(iteration=1, max_iterations=5)
    thresholds_iter2 = get_adaptive_thresholds(iteration=2, max_iterations=5)

    # Verify strict thresholds
    assert thresholds_iter1["bias_blocker"] == 4, "Early iteration bias_blocker must be 4"
    assert thresholds_iter1["content_blocker"] == 4, "Early iteration content_blocker must be 4"
    assert thresholds_iter1["accept_max_severity"] == 2, "Early iteration accept_max_severity must be 2"

    assert thresholds_iter2["bias_blocker"] == 4, "Early iteration (2) bias_blocker must be 4"
    assert thresholds_iter2["content_blocker"] == 4, "Early iteration (2) content_blocker must be 4"
    assert thresholds_iter2["accept_max_severity"] == 2, "Early iteration (2) accept_max_severity must be 2"


def test_adaptive_thresholds_mid_iteration():
    """Test AGT-10: Verify mid iterations (3-4) use standard thresholds.

    Mid iterations balance quality and progress.

    Expected thresholds for iterations 3-4:
    - bias_blocker = 4 (block on severity ≥4)
    - content_blocker = 4 (block on severity ≥4)
    - accept_max_severity = 3 (accept if max severity ≤3)

    Expected behavior:
    - get_adaptive_thresholds(3) returns standard thresholds
    - get_adaptive_thresholds(4) returns standard thresholds
    - Thresholds between early and late iterations
    """
    from backend.agents.critic import get_adaptive_thresholds

    # Mid iteration thresholds
    thresholds_iter3 = get_adaptive_thresholds(iteration=3, max_iterations=5)
    thresholds_iter4 = get_adaptive_thresholds(iteration=4, max_iterations=5)

    # Verify standard thresholds
    assert thresholds_iter3["bias_blocker"] == 4, "Mid iteration bias_blocker must be 4"
    assert thresholds_iter3["content_blocker"] == 4, "Mid iteration content_blocker must be 4"
    assert thresholds_iter3["accept_max_severity"] == 3, "Mid iteration accept_max_severity must be 3"

    assert thresholds_iter4["bias_blocker"] == 4, "Mid iteration (4) bias_blocker must be 4"
    assert thresholds_iter4["content_blocker"] == 4, "Mid iteration (4) content_blocker must be 4"
    assert thresholds_iter4["accept_max_severity"] == 3, "Mid iteration (4) accept_max_severity must be 3"


def test_adaptive_thresholds_late_iteration():
    """Test AGT-10: Verify late iterations (5+) use relaxed thresholds.

    Late iterations prioritize completion and accept minor issues.

    Expected thresholds for iterations 5+:
    - bias_blocker = 5 (block only on severity ≥5)
    - content_blocker = 5 (block only on severity ≥5)
    - accept_max_severity = 4 (accept if max severity ≤4)

    Expected behavior:
    - get_adaptive_thresholds(5) returns relaxed thresholds
    - get_adaptive_thresholds(6) returns relaxed thresholds
    - Thresholds more permissive than early/mid iterations
    """
    from backend.agents.critic import get_adaptive_thresholds

    # Late iteration thresholds
    thresholds_iter5 = get_adaptive_thresholds(iteration=5, max_iterations=5)
    thresholds_iter6 = get_adaptive_thresholds(iteration=6, max_iterations=6)

    # Verify relaxed thresholds
    assert thresholds_iter5["bias_blocker"] == 5, "Late iteration bias_blocker must be 5"
    assert thresholds_iter5["content_blocker"] == 5, "Late iteration content_blocker must be 5"
    assert thresholds_iter5["accept_max_severity"] == 4, "Late iteration accept_max_severity must be 4"

    assert thresholds_iter6["bias_blocker"] == 5, "Late iteration (6) bias_blocker must be 5"
    assert thresholds_iter6["content_blocker"] == 5, "Late iteration (6) content_blocker must be 5"
    assert thresholds_iter6["accept_max_severity"] == 4, "Late iteration (6) accept_max_severity must be 4"


def test_threshold_mode_in_reason():
    """Test AGT-10: Verify critic decision reason includes threshold mode context.

    For transparency, critic decisions should indicate which threshold mode
    was used (early/mid/late) and current iteration.

    Expected format in decision reason:
    "Iteration {current}/{max}: threshold mode {early|mid|late}"

    Expected behavior:
    - decide() includes iteration context in reason
    - Reason clearly states threshold mode used
    - Users can understand why certain items were accepted/rejected
    """
    from backend.agents.critic import decide
    from backend.schemas import ReviewComment

    # Sample comments with minor issue (severity 3)
    linguistic_comments = [
        ReviewComment(
            type="linguistic",
            item_index=0,
            issue="Vague quantifier detected",
            severity=3,
            suggested_edit="Add time anchor"
        )
    ]

    # Test early iteration (strict)
    decision_early, reason_early = decide(
        linguistic_comments=linguistic_comments,
        bias_comments=[],
        content_comments=[],
        iteration=1
    )

    assert "iteration 1/" in reason_early.lower(), \
        "Decision reason must include iteration context (1/...)"
    assert "early" in reason_early.lower() or "mode" in reason_early.lower(), \
        "Decision reason must indicate threshold mode"

    # Test late iteration (relaxed)
    decision_late, reason_late = decide(
        linguistic_comments=linguistic_comments,
        bias_comments=[],
        content_comments=[],
        iteration=5
    )

    assert "iteration 5/" in reason_late.lower(), \
        "Decision reason must include iteration context (5/...)"
    assert "late" in reason_late.lower() or "mode" in reason_late.lower(), \
        "Decision reason must indicate threshold mode"
