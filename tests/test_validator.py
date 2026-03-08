"""Test suite for validation agent.

This module tests the LLM-as-judge validation agent that scores
psychometric items across four dimensions using Claude Opus.
"""

import os
import pytest
from pathlib import Path

os.environ["APP_MODE"] = "mock"

from app.schemas import UserRequest, DraftItem


# Task 1: Validation prompt tests
def test_prompt_instructs_cot_reasoning():
    """Test 1 for Task 1: Prompt instructs chain-of-thought reasoning before scores."""
    prompt_path = Path("app/prompts/validator.md")
    assert prompt_path.exists(), "validator.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for chain-of-thought instructions
    assert "chain" in content or "reasoning" in content, "Prompt must mention chain-of-thought or reasoning"
    assert "before" in content, "Prompt must instruct reasoning BEFORE scoring"


def test_prompt_defines_four_dimensions_with_weights():
    """Test 2 for Task 1: Prompt defines all 4 dimensions with weights."""
    prompt_path = Path("app/prompts/validator.md")
    assert prompt_path.exists(), "validator.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for all 4 dimensions
    assert "correspondence" in content, "Prompt must define correspondence dimension"
    assert "distinctiveness" in content, "Prompt must define distinctiveness dimension"
    assert "clarity" in content, "Prompt must define clarity dimension"
    assert "specificity" in content, "Prompt must define specificity dimension"

    # Check for weights
    assert "50" in content or "0.5" in content, "Prompt must specify correspondence weight (50%)"
    assert "25" in content or "0.25" in content, "Prompt must specify distinctiveness weight (25%)"
    assert "15" in content or "0.15" in content, "Prompt must specify clarity weight (15%)"
    assert "10" in content or "0.1" in content, "Prompt must specify specificity weight (10%)"


def test_prompt_provides_scale_anchors():
    """Test 3 for Task 1: Prompt provides 1-10 scale anchors per dimension."""
    prompt_path = Path("app/prompts/validator.md")
    assert prompt_path.exists(), "validator.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8")

    # Check for scale range
    assert "1-10" in content or "1 to 10" in content, "Prompt must specify 1-10 scale"

    # Check for scale anchors (high and low)
    assert "10" in content and "1" in content, "Prompt must provide scale anchors"

    # Check minimum line count (100+ lines as per requirement)
    lines = content.split('\n')
    assert len(lines) >= 100, f"Prompt must have at least 100 lines, got {len(lines)}"


def test_prompt_specifies_weighted_formula_and_threshold():
    """Test 4 for Task 1: Prompt specifies weighted score formula and 7.0 threshold."""
    prompt_path = Path("app/prompts/validator.md")
    assert prompt_path.exists(), "validator.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for weighted score formula
    assert "weighted" in content, "Prompt must mention weighted scoring"

    # Check for 7.0 threshold
    assert "7.0" in content or "7" in content, "Prompt must specify 7.0 acceptance threshold"


def test_four_dimensions():
    """Verify ValidationResponse contains exactly 4 DimensionScore objects.

    Tests VAL-02: Multi-dimensional scoring across correspondence (50%),
    distinctiveness (25%), clarity (15%), and specificity (10%).

    Expected behavior:
    - ValidationResult.dimension_scores is a list of 4 DimensionScore objects
    - Each DimensionScore has a dimension field matching one of the 4 dimensions
    - All 4 dimensions are present (no duplicates, no missing)
    """
    pytest.skip("Awaiting validator agent implementation in plan 01-02")


def test_cot_reasoning():
    """Verify each DimensionScore includes chain-of-thought reasoning before score.

    Tests VAL-03: Chain-of-thought prompting with explicit reasoning before scores.

    Expected behavior:
    - Each DimensionScore has a non-empty 'reasoning' field
    - Reasoning appears before the score in the structured output
    - Reasoning explains WHY the score was assigned (not just what the score is)
    - Reasoning is substantive (minimum 20 characters)
    """
    pytest.skip("Awaiting validator agent implementation in plan 01-02")


def test_score_range():
    """Verify all dimension scores are integers between 1-10 inclusive.

    Tests VAL-04: 1-10 categorical scale with clear criterion definitions.

    Expected behavior:
    - Each DimensionScore.score is an integer (not float)
    - All scores are >= 1 and <= 10
    - Pydantic validation enforces range constraints
    - No scores outside valid range (boundary test)
    """
    pytest.skip("Awaiting validator agent implementation in plan 01-02")


def test_rejection_threshold():
    """Verify items with weighted_score < 7.0 are marked as rejected.

    Tests VAL-05: Automatic rejection threshold >= 7.0 for item acceptance.

    Expected behavior:
    - ValidationResult.weighted_score is computed from dimension scores
    - Weighting formula: correspondence*0.5 + distinctiveness*0.25 + clarity*0.15 + specificity*0.1
    - ValidationResult.accept is False when weighted_score < 7.0
    - ValidationResult.accept is True when weighted_score >= 7.0
    - Boundary case: weighted_score == 7.0 should be accepted
    """
    pytest.skip("Awaiting validator agent implementation in plan 01-02")


# Sample test data for future implementation
def _sample_user_request() -> UserRequest:
    """Helper to create sample UserRequest for validation testing."""
    return UserRequest(
        construct_name="Workplace belonging",
        construct_definition=(
            "A sustained sense of acceptance, inclusion, and social connection at work, "
            "reflected in feeling valued and able to participate without exclusion."
        ),
        target_population="Employees",
        response_scale="5-point Likert",
        item_count=5,
    )


def _sample_draft_items() -> list[DraftItem]:
    """Helper to create sample DraftItem list for validation testing."""
    return [
        DraftItem(
            item_text="I feel accepted by my coworkers",
            construct_name="Workplace belonging",
            rationale="Measures direct sense of acceptance, core component of belonging",
            evidence_citations=["SOURCE-001"],
        ),
        DraftItem(
            item_text="I am valued as a team member",
            construct_name="Workplace belonging",
            rationale="Captures feeling valued, key aspect of workplace inclusion",
            evidence_citations=["SOURCE-002"],
        ),
    ]
