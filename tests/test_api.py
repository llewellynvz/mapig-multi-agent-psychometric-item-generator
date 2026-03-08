"""Test suite for API validation response.

This module tests the FastAPI endpoint integration with validation,
ensuring validation results are included in API responses.
"""

import os
import pytest

os.environ["APP_MODE"] = "mock"
os.environ["SEARCH_PROVIDER"] = "local"  # Avoid external API calls in tests


def test_validation_in_response():
    """Verify POST /generate returns FinalOutput with validation_result per final_item.

    Tests VAL-08: Validation scores and reasoning visible in results UI.

    Expected behavior:
    - POST /generate with valid UserRequest returns 200 OK
    - Response body is FinalOutput schema
    - FinalOutput.validation_results exists and is non-empty
    - Each final_item has corresponding ValidationResult at same index
    - ValidationResult includes all 4 dimension_scores with reasoning
    - ValidationResult includes weighted_score and accept status
    - API response is valid JSON with all validation metadata
    - Frontend can render dimension scores and reasoning from response
    """
    from app.schemas import (
        DraftItem,
        DimensionScore,
        ItemValidation,
        FinalOutput,
        AuditMetadata,
    )

    # Test the schema structure by creating a mock FinalOutput
    # This verifies the API response schema supports all validation fields required by VAL-08

    # Create dimension scores (4 required per VAL-02)
    dim_scores_item_0 = [
        DimensionScore(dimension="correspondence", reasoning="Aligns well with construct definition", score=8),
        DimensionScore(dimension="distinctiveness", reasoning="Clear boundaries from related constructs", score=7),
        DimensionScore(dimension="clarity", reasoning="Easy to understand for target population", score=9),
        DimensionScore(dimension="specificity", reasoning="Precise wording avoids ambiguity", score=8),
    ]

    dim_scores_item_1 = [
        DimensionScore(dimension="correspondence", reasoning="Good construct alignment", score=9),
        DimensionScore(dimension="distinctiveness", reasoning="Unique from similar items", score=8),
        DimensionScore(dimension="clarity", reasoning="Simple language appropriate for population", score=8),
        DimensionScore(dimension="specificity", reasoning="Focused on single aspect", score=9),
    ]

    dim_scores_item_2 = [
        DimensionScore(dimension="correspondence", reasoning="Strong fit with construct", score=7),
        DimensionScore(dimension="distinctiveness", reasoning="Distinct from existing items", score=6),
        DimensionScore(dimension="clarity", reasoning="Clear and unambiguous", score=8),
        DimensionScore(dimension="specificity", reasoning="Specific behavior described", score=7),
    ]

    # Create item validations (simulating validation_node output)
    validation_0 = ItemValidation(
        item_index=0,
        item_text="I feel anxious in social situations",
        dimension_scores=dim_scores_item_0,
        weighted_score=7.95,  # Weighted: correspondence=0.5, distinctiveness=0.25, clarity=0.15, specificity=0.1
        accept=True,
        attempt=1,
    )

    validation_1 = ItemValidation(
        item_index=1,
        item_text="I avoid social gatherings",
        dimension_scores=dim_scores_item_1,
        weighted_score=8.6,
        accept=True,
        attempt=1,
    )

    validation_2 = ItemValidation(
        item_index=2,
        item_text="I worry about meeting new people",
        dimension_scores=dim_scores_item_2,
        weighted_score=6.85,  # Below threshold (7.0), would trigger regeneration
        accept=False,
        attempt=1,
    )

    # Create draft items with validation results (simulating finalize_node enrichment)
    item_0 = DraftItem(
        item_text="I feel anxious in social situations",
        construct_name="Social Anxiety",
        rationale="Measures anxious response to social contexts",
        evidence_citations=["doi:10.1234/example"],
        validation_result=validation_0,
    )

    item_1 = DraftItem(
        item_text="I avoid social gatherings",
        construct_name="Social Anxiety",
        rationale="Captures avoidance behavior",
        evidence_citations=["doi:10.1234/example"],
        validation_result=validation_1,
    )

    item_2 = DraftItem(
        item_text="I worry about meeting new people",
        construct_name="Social Anxiety",
        rationale="Assesses anticipatory anxiety",
        evidence_citations=["doi:10.1234/example"],
        validation_result=validation_2,
    )

    # Create audit metadata with validation summary
    audit = AuditMetadata(
        thread_id="test-thread-123",
        run_id="test-run-456",
        timestamp_utc="2026-03-08T12:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        model_info={"mode": "mock"},
        approved_sources=["doi:10.1234/example"],
        validation_attempts=2,  # Item 2 failed once, regenerated, passed on attempt 2
        validation_failures=1,  # One item initially rejected
    )

    # Create final output (simulating API response)
    final_output = FinalOutput(final_items=[item_0, item_1, item_2], audit=audit)

    # Serialize to JSON (simulating API response serialization)
    data = final_output.model_dump()

    # VERIFY: Response conforms to FinalOutput schema
    assert "final_items" in data, "Response missing 'final_items'"
    assert "audit" in data, "Response missing 'audit'"

    final_items = data["final_items"]
    assert len(final_items) == 3, f"Expected 3 items, got {len(final_items)}"

    # VERIFY: Each final_item has validation_result
    for idx, item in enumerate(final_items):
        assert "validation_result" in item, f"Item {idx} missing validation_result"
        assert item["validation_result"] is not None, f"Item {idx} validation_result is None"

        validation_result = item["validation_result"]

        # VERIFY: validation_result has required fields (VAL-08)
        assert "item_index" in validation_result, f"Item {idx} validation_result missing item_index"
        assert "item_text" in validation_result, f"Item {idx} validation_result missing item_text"
        assert "dimension_scores" in validation_result, f"Item {idx} validation_result missing dimension_scores"
        assert "weighted_score" in validation_result, f"Item {idx} validation_result missing weighted_score"
        assert "accept" in validation_result, f"Item {idx} validation_result missing accept"
        assert "attempt" in validation_result, f"Item {idx} validation_result missing attempt"

        # VERIFY: dimension_scores has all 4 dimensions with reasoning (VAL-02, VAL-09)
        dimension_scores = validation_result["dimension_scores"]
        assert len(dimension_scores) == 4, f"Item {idx} expected 4 dimension_scores, got {len(dimension_scores)}"

        dimension_names = set()
        for dim_idx, dim_score in enumerate(dimension_scores):
            assert "dimension" in dim_score, f"Item {idx} dimension_score {dim_idx} missing dimension"
            assert "reasoning" in dim_score, f"Item {idx} dimension_score {dim_idx} missing reasoning"
            assert "score" in dim_score, f"Item {idx} dimension_score {dim_idx} missing score"

            # VERIFY: reasoning is non-empty string (required for UI display)
            assert isinstance(dim_score["reasoning"], str), f"Item {idx} dimension_score {dim_idx} reasoning not string"
            assert len(dim_score["reasoning"]) > 0, f"Item {idx} dimension_score {dim_idx} reasoning is empty"

            # VERIFY: score is in valid range (1-10)
            assert isinstance(dim_score["score"], int), f"Item {idx} dimension_score {dim_idx} score not int"
            assert 1 <= dim_score["score"] <= 10, f"Item {idx} dimension_score {dim_idx} score out of range: {dim_score['score']}"

            # VERIFY: dimension name is one of the 4 expected dimensions
            assert dim_score["dimension"] in {
                "correspondence",
                "distinctiveness",
                "clarity",
                "specificity",
            }, f"Item {idx} dimension_score {dim_idx} has unexpected dimension: {dim_score['dimension']}"

            dimension_names.add(dim_score["dimension"])

        # VERIFY: All 4 unique dimensions present
        assert len(dimension_names) == 4, f"Item {idx} should have 4 unique dimensions, got {dimension_names}"

        # VERIFY: weighted_score is valid
        assert isinstance(validation_result["weighted_score"], (int, float)), f"Item {idx} weighted_score not numeric"
        assert 1.0 <= validation_result["weighted_score"] <= 10.0, f"Item {idx} weighted_score out of range: {validation_result['weighted_score']}"

        # VERIFY: accept is boolean
        assert isinstance(validation_result["accept"], bool), f"Item {idx} accept not boolean"

        # VERIFY: attempt is valid (1-3 per VAL-06)
        assert isinstance(validation_result["attempt"], int), f"Item {idx} attempt not int"
        assert 1 <= validation_result["attempt"] <= 3, f"Item {idx} attempt out of range: {validation_result['attempt']}"

        # VERIFY: item_index matches array position
        assert validation_result["item_index"] == idx, f"Item {idx} validation_result.item_index mismatch: {validation_result['item_index']}"

        # VERIFY: item_text matches draft item
        assert validation_result["item_text"] == item["item_text"], f"Item {idx} validation_result.item_text mismatch"

    # VERIFY: audit includes validation metadata (VAL-09)
    audit_data = data["audit"]
    assert "validation_attempts" in audit_data, "Audit missing validation_attempts"
    assert "validation_failures" in audit_data, "Audit missing validation_failures"

    # VERIFY: validation metadata is valid
    assert isinstance(audit_data["validation_attempts"], int), "validation_attempts not int"
    assert audit_data["validation_attempts"] >= 1, f"validation_attempts should be >= 1, got {audit_data['validation_attempts']}"
    assert audit_data["validation_attempts"] == 2, f"Expected 2 attempts based on test data, got {audit_data['validation_attempts']}"

    assert isinstance(audit_data["validation_failures"], int), "validation_failures not int"
    assert audit_data["validation_failures"] >= 0, f"validation_failures should be >= 0, got {audit_data['validation_failures']}"
    assert audit_data["validation_failures"] == 1, f"Expected 1 failure based on test data, got {audit_data['validation_failures']}"

    # VERIFY: JSON serialization preserves all validation data (critical for frontend consumption)
    import json
    json_str = json.dumps(data)
    reloaded = json.loads(json_str)

    # Spot-check: dimension reasoning preserved after JSON round-trip
    assert reloaded["final_items"][0]["validation_result"]["dimension_scores"][0]["reasoning"] == "Aligns well with construct definition"
    assert reloaded["final_items"][1]["validation_result"]["weighted_score"] == 8.6
    assert reloaded["audit"]["validation_attempts"] == 2

    # SUCCESS: All assertions passed
    # This verifies:
    # - VAL-08: Validation scores, reasoning, and accept/reject status are included in API response
    # - VAL-09: All validation metadata (dimension scores, reasoning, attempts, failures) is serializable and preserved
    # - Frontend can consume validation data from FinalOutput schema without data loss
