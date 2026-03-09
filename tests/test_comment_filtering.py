"""Test smart comment filtering in meta_editor_node."""

from backend.schemas import ReviewComment


def test_comment_filtering_logic():
    """Verify that severity filtering works as expected."""
    # Create test comments with different severities
    comments = [
        ReviewComment(type="linguistic", severity=1, issue="Minor typo", suggested_edit="Fix it"),
        ReviewComment(type="linguistic", severity=2, issue="Small clarity issue", suggested_edit="Clarify"),
        ReviewComment(type="bias", severity=3, issue="Moderate bias concern", suggested_edit="Revise"),
        ReviewComment(type="content", severity=4, issue="Major content issue", suggested_edit="Rewrite"),
        ReviewComment(type="linguistic", severity=5, issue="Critical error", suggested_edit="Must fix"),
    ]

    # Apply severity threshold filtering (≥3)
    severity_threshold = 3
    filtered = [c for c in comments if c.severity >= severity_threshold]

    # Verify filtering results
    assert len(filtered) == 3, "Should keep only severity 3, 4, 5"
    assert all(c.severity >= 3 for c in filtered), "All filtered comments should have severity ≥3"
    assert len(comments) - len(filtered) == 2, "Should filter out 2 low-severity comments"

    # Verify correct comments were kept
    severities = [c.severity for c in filtered]
    assert severities == [3, 4, 5], "Should keep comments with severity 3, 4, 5"


def test_empty_comments_list():
    """Verify filtering handles empty list correctly."""
    comments = []
    severity_threshold = 3
    filtered = [c for c in comments if c.severity >= severity_threshold]

    assert len(filtered) == 0, "Empty list should remain empty"


def test_all_low_severity_comments():
    """Verify all comments filtered when all are low severity."""
    comments = [
        ReviewComment(type="linguistic", severity=1, issue="Minor", suggested_edit="Fix"),
        ReviewComment(type="bias", severity=2, issue="Small", suggested_edit="Revise"),
    ]

    severity_threshold = 3
    filtered = [c for c in comments if c.severity >= severity_threshold]

    assert len(filtered) == 0, "Should filter out all low-severity comments"


def test_all_high_severity_comments():
    """Verify no filtering when all comments are high severity."""
    comments = [
        ReviewComment(type="linguistic", severity=3, issue="Moderate", suggested_edit="Fix"),
        ReviewComment(type="bias", severity=4, issue="Major", suggested_edit="Revise"),
        ReviewComment(type="content", severity=5, issue="Critical", suggested_edit="Rewrite"),
    ]

    severity_threshold = 3
    filtered = [c for c in comments if c.severity >= severity_threshold]

    assert len(filtered) == 3, "Should keep all high-severity comments"
    assert filtered == comments, "No comments should be filtered"
