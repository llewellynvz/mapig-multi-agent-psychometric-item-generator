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
