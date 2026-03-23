"""Test suite for validation agent.

This module tests the LLM-as-judge validation agent that scores
psychometric items across four dimensions using Claude Opus.
"""

import os
import pytest
from pathlib import Path

os.environ["APP_MODE"] = "mock"

from backend.schemas import UserRequest, DraftItem


# Task 1: Validation prompt tests
def test_prompt_instructs_cot_reasoning():
    """Test 1 for Task 1: Prompt instructs chain-of-thought reasoning before scores."""
    prompt_path = Path("backend/prompts/validator.md")
    assert prompt_path.exists(), "validator.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for chain-of-thought instructions
    assert "chain" in content or "reasoning" in content, "Prompt must mention chain-of-thought or reasoning"
    assert "before" in content, "Prompt must instruct reasoning BEFORE scoring"

    # Task #2: Check for reasoning requirements
    assert "reasoning" in content, "Prompt must require reasoning for dimensions"
    assert "brief" in content or "1-2 sentence" in content, "Prompt must specify reasoning length"


def test_prompt_defines_four_dimensions_with_weights():
    """Test 2 for Task 1: Prompt defines all 4 dimensions with weights."""
    prompt_path = Path("backend/prompts/validator.md")
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
    prompt_path = Path("backend/prompts/validator.md")
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
    prompt_path = Path("backend/prompts/validator.md")
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
    from backend.agents.validator import validate_items

    request = _sample_user_request()
    items = _sample_draft_items()

    result, usage = validate_items(request, items, attempt=1)

    assert len(result.validations) == 2, "Should validate all items"
    for validation in result.validations:
        assert len(validation.dimension_scores) == 4, "Each validation must have exactly 4 dimension scores"

        dimensions = [score.dimension for score in validation.dimension_scores]
        assert "correspondence" in dimensions, "Must include correspondence dimension"
        assert "distinctiveness" in dimensions, "Must include distinctiveness dimension"
        assert "clarity" in dimensions, "Must include clarity dimension"
        assert "specificity" in dimensions, "Must include specificity dimension"


def test_cot_reasoning():
    """Verify each DimensionScore includes chain-of-thought reasoning for failing dimensions.

    Tests VAL-03: Chain-of-thought prompting with explicit reasoning before scores.
    Task #2 Enhancement: Only failing dimensions (score < 7) require reasoning.

    Expected behavior:
    - Each DimensionScore has a 'reasoning' field
    - For passing dimensions (score >= 7): reasoning can be empty string
    - For failing dimensions (score < 7): reasoning must be substantive (min 3 chars)
    - Reasoning explains WHY the score was assigned for failing dimensions
    """
    from backend.agents.validator import validate_items

    request = _sample_user_request()
    items = _sample_draft_items()

    result, usage = validate_items(request, items, attempt=1)

    for validation in result.validations:
        for dim_score in validation.dimension_scores:
            assert hasattr(dim_score, 'reasoning'), "DimensionScore must have reasoning field"

            # Task #2: Only failing dimensions require reasoning
            if dim_score.score < 7:
                assert dim_score.reasoning, f"Failing dimension {dim_score.dimension} must have reasoning"
                assert len(dim_score.reasoning) >= 3, f"Reasoning for failing dimension must be substantive (min 3 chars)"
            # Passing dimensions can have empty reasoning (token optimization)
            # No assertion needed - empty reasoning is valid for passing scores


def test_score_range():
    """Verify all dimension scores are integers between 1-10 inclusive.

    Tests VAL-04: 1-10 categorical scale with clear criterion definitions.

    Expected behavior:
    - Each DimensionScore.score is an integer (not float)
    - All scores are >= 1 and <= 10
    - Pydantic validation enforces range constraints
    - No scores outside valid range (boundary test)
    """
    from backend.agents.validator import validate_items

    request = _sample_user_request()
    items = _sample_draft_items()

    result, usage = validate_items(request, items, attempt=1)

    for validation in result.validations:
        for dim_score in validation.dimension_scores:
            assert isinstance(dim_score.score, int), "Score must be integer"
            assert 1 <= dim_score.score <= 10, f"Score must be 1-10, got {dim_score.score}"


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
    from backend.agents.validator import validate_items

    request = _sample_user_request()
    items = _sample_draft_items()

    result, usage = validate_items(request, items, attempt=1)

    for validation in result.validations:
        # In mock mode, items alternate: idx 0 = 8.0 (accept), idx 1 = 6.5 (reject)
        if validation.weighted_score >= 7.0:
            assert validation.accept is True, f"Item with score {validation.weighted_score} should be accepted"
        else:
            assert validation.accept is False, f"Item with score {validation.weighted_score} should be rejected"


def test_mock_mode_returns_deterministic_results():
    """Test 5 for Task 2: Mock mode returns deterministic validation results."""
    from backend.agents.validator import validate_items

    request = _sample_user_request()
    items = _sample_draft_items()

    result, usage = validate_items(request, items, attempt=1)

    # Mock mode should return deterministic results
    assert len(result.validations) == 2, "Should validate both items"

    # First item (idx 0) should pass with score 8.0
    assert result.validations[0].weighted_score == 8.0, "First item should have score 8.0 in mock mode"
    assert result.validations[0].accept is True, "First item should be accepted"

    # Second item (idx 1) should fail with score 6.5
    assert result.validations[1].weighted_score == 6.5, "Second item should have score 6.5 in mock mode"
    assert result.validations[1].accept is False, "Second item should be rejected"


def test_uses_validator_model():
    """Test 1 for Task 2: Uses get_validator_model() for Claude Opus.

    Tests VAL-07: Validation uses Claude Opus 4-6 for highest accuracy.

    Note: This test verifies the function exists and can be called.
    Actual model usage tested via integration tests (not in mock mode).
    """
    from backend.agents.llm_factory import get_validator_model

    # In mock mode, we just verify the function exists and configuration is correct
    from backend.settings import settings

    assert settings.VALIDATOR_MODEL == "claude-opus-4-6", "Validator should use Claude Opus 4-6"

    # Verify get_validator_model exists (will raise ValueError in mock mode without API key, which is expected)
    # This test just confirms the function is available for real mode
    assert callable(get_validator_model), "get_validator_model must be callable"


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


def test_detect_identical_scores():
    """Identical dimension scores across all items should be detected."""
    from backend.agents.validator import _detect_identical_scores
    from backend.schemas import ItemValidation, DimensionScore

    # All identical — should detect
    identical = [
        ItemValidation(
            item_index=i,
            item_text=f"Item {i}",
            dimension_scores=[
                DimensionScore(dimension="correspondence", reasoning="", score=6),
                DimensionScore(dimension="distinctiveness", reasoning="", score=8),
                DimensionScore(dimension="clarity", reasoning="", score=9),
                DimensionScore(dimension="specificity", reasoning="", score=9),
            ],
            weighted_score=7.25,
            accept=True,
            attempt=1,
        )
        for i in range(5)
    ]
    assert _detect_identical_scores(identical) is True

    # Varied scores — should not detect
    varied = list(identical)  # copy
    varied[2] = ItemValidation(
        item_index=2,
        item_text="Item 2",
        dimension_scores=[
            DimensionScore(dimension="correspondence", reasoning="", score=7),
            DimensionScore(dimension="distinctiveness", reasoning="", score=8),
            DimensionScore(dimension="clarity", reasoning="", score=9),
            DimensionScore(dimension="specificity", reasoning="", score=9),
        ],
        weighted_score=7.75,
        accept=True,
        attempt=1,
    )
    assert _detect_identical_scores(varied) is False

    # Too few items — should not detect
    assert _detect_identical_scores(identical[:2]) is False
    assert _detect_identical_scores([]) is False


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
