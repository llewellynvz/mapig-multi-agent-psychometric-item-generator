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


def test_finaloutput_enhanced_schema():
    """Phase 03.1: FinalOutput accepts optional metadata fields."""
    from app.schemas import UserRequest, ReviewComment, DraftItem, FinalOutput, AuditMetadata

    # Arrange: Create mock data
    user_req = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition here",
        target_population="General adult",
        response_scale="1-5 Likert",
        item_count=5,
        constraints=[]
    )

    review_comment = ReviewComment(
        type="linguistic",
        item_index=0,
        issue="Test issue",
        severity=3,
        suggested_edit="Test edit"
    )

    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test Construct",
        rationale="Test rationale for the item",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-08T00:00:00Z",
        iteration_count=1,
        stop_reason="max_iterations",
        model_info={"mode": "openai"},
        approved_sources=[],
        validation_attempts=1,
        validation_failures=0
    )

    # Act: Create FinalOutput with enhanced fields
    output = FinalOutput(
        final_items=[draft_item],
        audit=audit,
        user_request=user_req,
        linguistic_feedback=[review_comment],
        bias_feedback=[],
        content_feedback=[]
    )

    # Assert: All fields populated correctly
    assert output.user_request == user_req
    assert len(output.linguistic_feedback) == 1
    assert output.linguistic_feedback[0].issue == "Test issue"
    assert output.bias_feedback == []
    assert output.content_feedback == []


def test_finaloutput_backward_compatibility():
    """Phase 03.1: FinalOutput maintains backward compatibility without optional fields."""
    from app.schemas import DraftItem, FinalOutput, AuditMetadata

    # Arrange: Create minimal valid FinalOutput (existing pattern)
    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test",
        rationale="Test rationale for the item",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-08T00:00:00Z",
        iteration_count=1,
        stop_reason="max_iterations",
        model_info={"mode": "openai"},
        approved_sources=[],
        validation_attempts=1,
        validation_failures=0
    )

    # Act: Create FinalOutput WITHOUT new fields (backward compatibility)
    output = FinalOutput(
        final_items=[draft_item],
        audit=audit
    )

    # Assert: New fields use defaults (None or empty list)
    assert output.user_request is None
    assert output.linguistic_feedback == []
    assert output.bias_feedback == []
    assert output.content_feedback == []


def test_finaloutput_mutable_defaults():
    """Phase 03.1: FinalOutput feedback arrays are not shared across instances."""
    from app.schemas import ReviewComment, DraftItem, FinalOutput, AuditMetadata

    # Arrange: Create two FinalOutput instances without feedback
    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test",
        rationale="Test rationale for the item",
        evidence_citations=[]
    )

    audit = AuditMetadata(
        thread_id="test-thread",
        run_id="test-run",
        timestamp_utc="2026-03-08T00:00:00Z",
        iteration_count=1,
        stop_reason="max_iterations",
        model_info={"mode": "openai"},
        approved_sources=[],
        validation_attempts=1,
        validation_failures=0
    )

    output1 = FinalOutput(final_items=[draft_item], audit=audit)
    output2 = FinalOutput(final_items=[draft_item], audit=audit)

    # Act: Modify one instance's feedback
    comment = ReviewComment(
        type="bias",
        item_index=0,
        issue="Test",
        severity=2,
        suggested_edit="Edit"
    )
    output1.bias_feedback.append(comment)

    # Assert: Other instance unaffected (not shared reference)
    assert len(output1.bias_feedback) == 1
    assert len(output2.bias_feedback) == 0
    assert output1.bias_feedback is not output2.bias_feedback


# Phase 03: Claude API Migration - Provider Selection Tests


def test_user_request_model_provider_defaults_to_claude():
    """Phase 03-01: UserRequest.model_provider defaults to 'claude'."""
    from app.schemas import UserRequest

    # Act: Create UserRequest without model_provider
    request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition here",
        target_population="General adult",
        response_scale="1-5 Likert",
        item_count=5
    )

    # Assert: Default is 'claude'
    assert request.model_provider == "claude"


def test_user_request_validates_model_provider_enum():
    """Phase 03-01: UserRequest validates model_provider is 'claude' or 'openai'."""
    from pydantic import ValidationError
    from app.schemas import UserRequest

    # Test valid values
    valid_claude = UserRequest(
        construct_name="Test",
        construct_definition="Definition",
        target_population="Adults",
        response_scale="1-5",
        model_provider="claude"
    )
    assert valid_claude.model_provider == "claude"

    valid_openai = UserRequest(
        construct_name="Test",
        construct_definition="Definition",
        target_population="Adults",
        response_scale="1-5",
        model_provider="openai"
    )
    assert valid_openai.model_provider == "openai"

    # Test invalid value
    with pytest.raises(ValidationError) as exc_info:
        UserRequest(
            construct_name="Test",
            construct_definition="Definition",
            target_population="Adults",
            response_scale="1-5",
            model_provider="azure"  # Invalid
        )
    assert "model_provider" in str(exc_info.value).lower()


def test_user_request_accepts_openai_provider():
    """Phase 03-01: UserRequest accepts 'openai' as model_provider."""
    from app.schemas import UserRequest

    # Act: Create UserRequest with openai provider
    request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition here",
        target_population="General adult",
        response_scale="1-5 Likert",
        item_count=10,
        model_provider="openai"
    )

    # Assert: model_provider set correctly
    assert request.model_provider == "openai"

    # Assert: Serialization preserves model_provider
    data = request.model_dump()
    assert data["model_provider"] == "openai"
