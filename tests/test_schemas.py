"""Unit tests for the schema-level fixes (is_unidimensional default, issue cap)."""

from backend.schemas import ReviewComment, UserRequest


def test_is_unidimensional_defaults_false():
    """Regression: the True default silently collapsed multi-facet constructs."""
    req = UserRequest(
        construct_name="Grit",
        construct_definition="Perseverance and passion for long-term goals",
        target_population="adults",
        response_scale="5-point Likert",
    )
    assert req.is_unidimensional is False


def test_issue_field_accepts_long_text():
    """Regression: the 210-char cap crashed the content reviewer (string_too_long)."""
    c = ReviewComment(type="content", issue="x" * 400, severity=3)
    assert len(c.issue) == 400
