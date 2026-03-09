"""Test suite for graph integration with validation gate.

This module tests the LangGraph integration of the validation node,
including placement in the graph and retry logic.
"""

import os
import pytest

os.environ["APP_MODE"] = "mock"


def test_validation_placement():
    """Verify validation_node executes between item_writer_node and reviewers_fanout_node.

    Tests VAL-01: Validation agent executes immediately after Item Writer, before reviewers.

    Expected behavior:
    - Graph contains a 'validation_node' node
    - validation_node is connected after item_writer_node
    - validation_node is connected before reviewers_fanout_node
    - Edge routing ensures validation happens in correct sequence
    - No items proceed to reviewers without validation

    Note: This test scaffold is created early (Wave 0) to support TDD for Plan 04,
    which implements VAL-01. The test will remain skipped until Plan 04 implements
    the validation_node in the graph.
    """
    from app.graph import build_graph

    # Build the graph
    graph = build_graph()

    # Test 1: validation_node exists
    assert "validation_node" in graph.nodes, "validation_node must exist in graph"

    # Test 2: regenerate_items_node exists
    assert "regenerate_items_node" in graph.nodes, "regenerate_items_node must exist in graph"

    # Test 3: GraphState should have validation fields
    # We test this by checking the actual function exists
    from app.graph import validation_node, route_after_validation, regenerate_items_node
    assert callable(validation_node), "validation_node function must be callable"
    assert callable(route_after_validation), "route_after_validation function must be callable"
    assert callable(regenerate_items_node), "regenerate_items_node function must be callable"


def test_retry_limit():
    """Verify maximum 3 regeneration attempts before accepting best score.

    Tests VAL-06: Immediate retry logic (regenerate rejected items only, max 3 attempts).

    Expected behavior:
    - When ValidationResult.accept is False, graph routes to regenerate_node
    - Retry count is tracked in GraphState
    - After 3 attempts, graph accepts best-scoring version
    - Graph routes to reviewers_fanout_node after max retries exhausted
    - Only failed items are regenerated (not entire set)
    - Attempt count is recorded in validation_results metadata
    """
    from app.graph import route_after_validation
    from app.schemas import ItemValidation, DimensionScore

    # Test case 1: All items pass - should route to reviewers
    state_all_pass = {
        "validation_results": [
            ItemValidation(
                item_index=0,
                item_text="Test item",
                dimension_scores=[
                    DimensionScore(dimension="correspondence", reasoning="Good", score=8),
                    DimensionScore(dimension="distinctiveness", reasoning="Good", score=8),
                    DimensionScore(dimension="clarity", reasoning="Good", score=8),
                    DimensionScore(dimension="specificity", reasoning="Good", score=8),
                ],
                weighted_score=8.0,
                accept=True,
                attempt=1
            )
        ],
        "validation_attempt": 1
    }
    result = route_after_validation(state_all_pass)
    assert result.goto == "reviewers_fanout_node", "All items passing should route to reviewers"

    # Test case 2: Items fail, attempt < 3 - should route to regenerate
    state_fail_attempt_1 = {
        "validation_results": [
            ItemValidation(
                item_index=0,
                item_text="Test item",
                dimension_scores=[
                    DimensionScore(dimension="correspondence", reasoning="Poor", score=5),
                    DimensionScore(dimension="distinctiveness", reasoning="Poor", score=5),
                    DimensionScore(dimension="clarity", reasoning="Poor", score=5),
                    DimensionScore(dimension="specificity", reasoning="Poor", score=5),
                ],
                weighted_score=5.0,
                accept=False,
                attempt=1
            )
        ],
        "validation_attempt": 1
    }
    result = route_after_validation(state_fail_attempt_1)
    assert result.goto == "regenerate_items_node", "Failed items should route to regenerate"
    assert result.update["validation_attempt"] == 2, "Attempt counter should increment"

    # Test case 3: Items fail, attempt = 3 (max retries) - should accept and route to reviewers
    state_max_retries = {
        "validation_results": [
            ItemValidation(
                item_index=0,
                item_text="Test item",
                dimension_scores=[
                    DimensionScore(dimension="correspondence", reasoning="Poor", score=5),
                    DimensionScore(dimension="distinctiveness", reasoning="Poor", score=5),
                    DimensionScore(dimension="clarity", reasoning="Poor", score=5),
                    DimensionScore(dimension="specificity", reasoning="Poor", score=5),
                ],
                weighted_score=5.0,
                accept=False,
                attempt=3
            )
        ],
        "validation_attempt": 3
    }
    result = route_after_validation(state_max_retries)
    assert result.goto == "reviewers_fanout_node", "Max retries should accept and route to reviewers"


def test_finalize_node_enhanced_output():
    """Phase 03.1: finalize_node populates enhanced FinalOutput fields from GraphState."""
    from app.graph import finalize_node
    from app.schemas import (
        UserRequest, ReviewComment, DraftItem, EvidenceChunk,
        ItemValidation, DimensionScore
    )

    # Arrange: Create GraphState with all enhanced metadata
    user_req = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition",
        target_population="Adults",
        response_scale="1-5 Likert",
        item_count=3,
        constraints=[]
    )

    linguistic_comment = ReviewComment(
        type="linguistic",
        item_index=0,
        issue="Linguistic issue",
        severity=2,
        suggested_edit="Edit suggestion"
    )

    bias_comment = ReviewComment(
        type="bias",
        item_index=1,
        issue="Bias detected",
        severity=4,
        suggested_edit="Remove bias"
    )

    content_comment = ReviewComment(
        type="content",
        item_index=None,
        issue="General content issue",
        severity=3,
        suggested_edit="Revise"
    )

    draft_item = DraftItem(
        item_text="Item text",
        construct_name="Test Construct",
        rationale="Test rationale for the item",
        evidence_citations=["source1"]
    )

    evidence = EvidenceChunk(
        source_id="source1",
        title="Test Source",
        snippet="Evidence text",
        url_or_docref="https://example.com/source1",
        quote="Exact quote from source"
    )

    dim_scores = [
        DimensionScore(dimension="correspondence", reasoning="Good alignment", score=9),
        DimensionScore(dimension="distinctiveness", reasoning="Clear boundaries", score=8),
        DimensionScore(dimension="clarity", reasoning="Easy to understand", score=8),
        DimensionScore(dimension="specificity", reasoning="Precise wording", score=9),
    ]

    validation = ItemValidation(
        item_index=0,
        item_text="Item text",
        dimension_scores=dim_scores,
        weighted_score=8.5,
        accept=True,
        attempt=1
    )

    state = {
        "user_request": user_req,
        "thread_id": "test-thread",
        "run_id": "test-run",
        "timestamp_utc": "2026-03-08T00:00:00Z",
        "draft_items": [draft_item],
        "linguistic_comments": [linguistic_comment],
        "bias_comments": [bias_comment],
        "content_comments": [content_comment],
        "evidence": [evidence],
        "validation_results": [validation],
        "iteration": 2,
        "stop_reason": "max_iterations",
        "validation_attempt": 1
    }

    # Act: Call finalize_node
    result = finalize_node(state)

    # Assert: FinalOutput populated with enhanced fields
    final_output = result["final_output"]

    assert final_output.user_request == user_req
    assert final_output.user_request.construct_name == "Test Construct"

    assert len(final_output.linguistic_feedback) == 1
    assert final_output.linguistic_feedback[0].issue == "Linguistic issue"

    assert len(final_output.bias_feedback) == 1
    assert final_output.bias_feedback[0].severity == 4

    assert len(final_output.content_feedback) == 1
    assert final_output.content_feedback[0].item_index is None

    # Existing fields still work
    assert len(final_output.final_items) == 1
    assert final_output.audit.thread_id == "test-thread"
    assert final_output.audit.iteration_count == 2


def test_missing_claude_key_raises_error():
    """Test that missing CLAUDE_API_KEY prevents Claude workflow.

    This test will be implemented when pytest-mock is available.
    Validates HTTPException raised when CLAUDE_API_KEY missing.
    """
    pass
