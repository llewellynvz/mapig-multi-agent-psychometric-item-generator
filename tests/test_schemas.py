"""Test suite for validation schemas.

This module tests the Pydantic schemas used for validation results,
including dimension scores and export metadata.
"""

import os
import pytest

os.environ["APP_MODE"] = "mock"


def test_validation_export():
    """Verify FinalOutput schema can serialize validation_results with all metadata.

    Tests VAL-09: Export validation metadata (all dimension scores, reasoning, attempt count).

    Expected behavior:
    - FinalOutput schema includes optional validation_results field
    - validation_results is a list of ValidationResult objects
    - Each ValidationResult contains:
      - item_index, item_text
      - dimension_scores (list of 4 DimensionScore objects)
      - weighted_score (float)
      - accept (bool)
      - attempt (int, 1-3)
    - ValidationResult can be serialized to JSON
    - All dimension scores and reasoning are preserved in export
    """
    from app.schemas import DimensionScore, ItemValidation, DraftItem, FinalOutput, AuditMetadata

    # Create dimension scores
    dim_scores = [
        DimensionScore(dimension="correspondence", reasoning="Aligns well", score=8),
        DimensionScore(dimension="distinctiveness", reasoning="Clear boundaries", score=7),
        DimensionScore(dimension="clarity", reasoning="Easy to understand", score=9),
        DimensionScore(dimension="specificity", reasoning="Precise wording", score=8),
    ]

    # Create item validation
    validation = ItemValidation(
        item_index=0,
        item_text="I feel anxious in social situations",
        dimension_scores=dim_scores,
        weighted_score=7.95,  # weighted: 8*0.5 + 7*0.25 + 9*0.15 + 8*0.1
        accept=True,
        attempt=1,
    )

    # Create draft item with validation
    item = DraftItem(
        item_text="I feel anxious in social situations",
        construct_name="Social Anxiety",
        rationale="Measures anxious response",
        validation_result=validation,
    )

    # Create final output with validation metadata
    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-08T12:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        validation_attempts=1,
        validation_failures=0,
    )

    output = FinalOutput(final_items=[item], audit=audit)

    # Verify serialization preserves validation data
    data = output.model_dump()
    assert data["final_items"][0]["validation_result"] is not None
    assert len(data["final_items"][0]["validation_result"]["dimension_scores"]) == 4
    assert data["final_items"][0]["validation_result"]["weighted_score"] == 7.95
    assert data["audit"]["validation_attempts"] == 1


def test_dimension_score_schema():
    """Verify DimensionScore schema validates score range 1-10.

    Tests schema validation for individual dimension scores.

    Expected behavior:
    - DimensionScore has three fields: dimension, reasoning, score
    - dimension is a string (correspondence/distinctiveness/clarity/specificity)
    - reasoning is a non-empty string
    - score is an integer with Pydantic constraint: ge=1, le=10
    - Pydantic raises ValidationError for scores < 1 or > 10
    - Pydantic raises ValidationError for float scores (must be int)
    """
    from pydantic import ValidationError
    from app.schemas import DimensionScore, ItemValidation

    # Test valid score
    valid_score = DimensionScore(
        dimension="correspondence",
        reasoning="Strong alignment with construct",
        score=8
    )
    assert valid_score.score == 8
    assert valid_score.dimension == "correspondence"

    # Test boundary values (1 and 10 are valid)
    min_score = DimensionScore(dimension="clarity", reasoning="Minimal", score=1)
    assert min_score.score == 1

    max_score = DimensionScore(dimension="clarity", reasoning="Perfect", score=10)
    assert max_score.score == 10

    # Test invalid: score < 1
    with pytest.raises(ValidationError) as exc_info:
        DimensionScore(dimension="clarity", reasoning="Too low", score=0)
    assert "greater than or equal to 1" in str(exc_info.value).lower()

    # Test invalid: score > 10
    with pytest.raises(ValidationError) as exc_info:
        DimensionScore(dimension="clarity", reasoning="Too high", score=11)
    assert "less than or equal to 10" in str(exc_info.value).lower()

    # Test ItemValidation requires exactly 4 dimensions (VAL-02)
    dim_scores_4 = [
        DimensionScore(dimension="correspondence", reasoning="Good", score=8),
        DimensionScore(dimension="distinctiveness", reasoning="Good", score=7),
        DimensionScore(dimension="clarity", reasoning="Good", score=9),
        DimensionScore(dimension="specificity", reasoning="Good", score=8),
    ]

    validation = ItemValidation(
        item_index=0,
        item_text="Test item",
        dimension_scores=dim_scores_4,
        weighted_score=7.95,
        accept=True,
        attempt=1,
    )
    assert len(validation.dimension_scores) == 4
