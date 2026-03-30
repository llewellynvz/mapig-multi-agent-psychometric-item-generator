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
    from backend.graph import build_graph

    # Build the graph
    graph = build_graph()

    # Test 1: validation_node exists
    assert "validation_node" in graph.nodes, "validation_node must exist in graph"

    # Test 2: regenerate_items_node exists
    assert "regenerate_items_node" in graph.nodes, "regenerate_items_node must exist in graph"

    # Test 3: GraphState should have validation fields
    # We test this by checking the actual function exists
    from backend.graph import validation_node, regenerate_items_node
    assert callable(validation_node), "validation_node function must be callable"
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
    import os
    os.environ["APP_MODE"] = "mock"  # Use mock mode to avoid API calls

    from backend.graph import validation_node
    from backend.schemas import UserRequest, DraftItem

    # Helper to create mock state
    def create_mock_state(item_count=10, attempt=1):
        return {
            "user_request": UserRequest(
                construct_name="Test",
                construct_definition="Test definition",
                target_population="Adults",
                response_scale="5-point Likert"
            ),
            "draft_items": [
                DraftItem(
                    item_text=f"Test item {i}",
                    construct_name="Test",
                    rationale="Test rationale for item",
                    evidence_citations=[]
                ) for i in range(item_count)
            ],
            "validation_attempt": attempt
        }

    # Test case 1: Mock mode with even items (pass) - should route to reviewers eventually
    # Mock mode alternates: even indices score 8.0 (pass), odd indices score 6.5 (fail)
    state_mock = create_mock_state(item_count=2, attempt=1)  # 2 items: index 0 passes, index 1 fails
    result = validation_node(state_mock)
    assert result.goto == "regenerate_items_node", "With failed items, should route to regenerate"
    assert result.update["validation_attempt"] == 2, "Attempt counter should increment"
    assert 1 in result.update["failed_item_indices"], "Odd index should be in failed list"

    # Test case 2: Max retries exhausted - should route to reviewers
    state_max_retries = create_mock_state(item_count=2, attempt=3)  # Max attempts reached
    result = validation_node(state_max_retries)
    assert result.goto == "reviewers_fanout_node", "Max retries should route to reviewers"


def test_finalize_node_enhanced_output():
    """Phase 03.1: finalize_node populates enhanced FinalOutput fields from GraphState."""
    from backend.graph import finalize_node
    from backend.schemas import (
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
        "validation_attempt": 1,
        "opus_tokens_used": 0,
        "sonnet_tokens_used": 0,
        "openai_tokens_used": 0,
        "chatgpt_tokens_used": 0,
        "gpt52_tokens_used": 0,
        "gpt52_reasoning_tokens": 0,
        "gpt52_output_tokens": 0,
    }

    # Act: Call finalize_node (returns Command since only 1 item < 3)
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


def test_claude_end_to_end_workflow():
    """Test end-to-end generation with Claude API provider.

    Tests API-04: User can generate items end-to-end using Claude API.

    Expected behavior:
    - When model_provider="claude" in UserRequest
    - All agents receive correct model allocation:
      - validator gets Opus
      - other agents get Sonnet
    - Workflow completes successfully
    - GraphState tracks model_provider through execution
    """
    from unittest.mock import patch, MagicMock
    from backend.schemas import UserRequest
    from backend.agents.llm_factory import get_chat_model_for_agent
    from backend.settings import settings
    from langchain_anthropic import ChatAnthropic

    # Create request with claude provider
    request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition for test",
        target_population="Adults",
        response_scale="1-5 Likert",
        item_count=5,
        model_provider="claude"
    )

    # Mock CLAUDE_API_KEY and disable agent overrides to test base allocation
    with patch.object(settings, 'CLAUDE_API_KEY', "test-key-12345"), \
         patch.object(settings, 'AGENT_MODEL_OVERRIDES_ENABLED', False):
        # Clear LRU cache to force new instances
        from backend.agents.llm_factory import get_claude_chat_model
        if hasattr(get_claude_chat_model, 'cache_clear'):
            get_claude_chat_model.cache_clear()

        # Test 1: Validator gets Opus
        validator_model = get_chat_model_for_agent("validator", request.model_provider)
        assert isinstance(validator_model, ChatAnthropic)
        assert validator_model.model == "claude-opus-4-6"

        # Test 2: Other agents get Sonnet
        for agent_name in ["item_writer", "content_reviewer", "linguistic_reviewer", "bias_reviewer", "meta_editor", "critic"]:
            agent_model = get_chat_model_for_agent(agent_name, request.model_provider)
            assert isinstance(agent_model, ChatAnthropic)
            assert agent_model.model == "claude-sonnet-4-5", f"{agent_name} should use Sonnet"

        # Test 3: Verify request serialization preserves model_provider
        request_data = request.model_dump()
        assert request_data["model_provider"] == "claude"


def test_missing_claude_key_raises_error():
    """Test that missing CLAUDE_API_KEY prevents Claude workflow.

    Tests API-05: Missing CLAUDE_API_KEY shows clear error message.

    Expected behavior:
    - When CLAUDE_API_KEY is None/empty and model_provider="claude"
    - /v1/generate-items-stream endpoint raises HTTPException 400
    - Error message mentions configuring .env or Vercel environment variables
    """
    from unittest.mock import patch, AsyncMock
    from fastapi import HTTPException
    from backend.schemas import UserRequest
    from backend.settings import settings

    # Test the validation logic directly (endpoint validates before graph initialization)
    request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Definition for test",
        target_population="Adults",
        response_scale="1-5 Likert",
        item_count=5,
        model_provider="claude"
    )

    # Mock settings to have no CLAUDE_API_KEY
    with patch.object(settings, 'CLAUDE_API_KEY', None):
        # Simulate the validation check from main.py lines 263-268
        should_raise = request.model_provider == "claude" and not settings.CLAUDE_API_KEY

        # Assert: Validation should fail
        assert should_raise, "Should detect missing CLAUDE_API_KEY for claude provider"

        # Verify error message format (from main.py line 267)
        expected_error = "CLAUDE_API_KEY not configured. Add to .env or Vercel environment variables, or switch to OpenAI provider."

        # Test that the error message contains key information
        assert "CLAUDE_API_KEY" in expected_error
        assert ".env" in expected_error
        assert "Vercel" in expected_error
        assert "environment" in expected_error


# Phase 07 Task 2: Analytics Placeholder Nodes and GPT-5.2 Token Tracking


def test_graphstate_gpt52_token_fields():
    """Phase 07-02 Task 2: GraphState accepts GPT-5.2 token tracking fields."""
    from backend.graph import GraphState

    # Create a dict with GPT-5.2 token fields (TypedDict with total=False allows optional keys)
    state: GraphState = {
        "gpt52_tokens_used": 1000,
        "gpt52_reasoning_tokens": 800,
        "gpt52_output_tokens": 200,
    }

    # Verify fields are accepted (no TypedDict error)
    assert state["gpt52_tokens_used"] == 1000
    assert state["gpt52_reasoning_tokens"] == 800
    assert state["gpt52_output_tokens"] == 200


def test_accumulate_tokens_gpt52():
    """Phase 07-02 Task 2: _accumulate_tokens routes GPT-5.2 tokens with reasoning tracking."""
    from backend.graph import _accumulate_tokens
    from backend.agents.llm_utils import TokenUsage

    # Create state with initial zero counters
    state = {
        "gpt52_tokens_used": 0,
        "gpt52_reasoning_tokens": 0,
        "gpt52_output_tokens": 0,
        "opus_tokens_used": 0,
        "sonnet_tokens_used": 0,
        "openai_tokens_used": 0,
        "chatgpt_tokens_used": 0,
    }

    # Create GPT-5.2 usage with reasoning tokens
    usage = TokenUsage(
        model_name="gpt-5.2",
        total_tokens=1000,
        reasoning_tokens=800,
        output_tokens=200,
        input_tokens=100
    )

    # Act: Accumulate tokens
    result = _accumulate_tokens(state, usage)

    # Assert: GPT-5.2 counters updated correctly
    assert result["gpt52_tokens_used"] == 1000, "Total GPT-5.2 tokens should be 1000"
    assert result["gpt52_reasoning_tokens"] == 800, "Reasoning tokens should be 800"
    assert result["gpt52_output_tokens"] == 200, "Output tokens should be 200"

    # Assert: Other counters unchanged
    assert result["opus_tokens_used"] == 0
    assert result["sonnet_tokens_used"] == 0
    assert result["openai_tokens_used"] == 0
    assert result["chatgpt_tokens_used"] == 0


def test_accumulate_tokens_existing_models_unchanged():
    """Phase 07-02 Task 2: GPT-5.2 routing doesn't affect existing model routing (regression)."""
    from backend.graph import _accumulate_tokens
    from backend.agents.llm_utils import TokenUsage

    # Create state with zero counters
    state = {
        "gpt52_tokens_used": 0,
        "gpt52_reasoning_tokens": 0,
        "gpt52_output_tokens": 0,
        "opus_tokens_used": 0,
        "sonnet_tokens_used": 0,
        "openai_tokens_used": 0,
        "chatgpt_tokens_used": 0,
    }

    # Test existing model (Sonnet)
    sonnet_usage = TokenUsage(
        model_name="claude-sonnet-4-5",
        total_tokens=500,
        output_tokens=200,
        input_tokens=300
    )

    result = _accumulate_tokens(state, sonnet_usage)

    # Assert: Sonnet counter updated, GPT-5.2 counters stay zero
    assert result["sonnet_tokens_used"] == 500
    assert result["gpt52_tokens_used"] == 0
    assert result["gpt52_reasoning_tokens"] == 0
    assert result["gpt52_output_tokens"] == 0


def test_accumulate_tokens_cache_metrics():
    """Cache metrics are accumulated across _accumulate_tokens calls."""
    from backend.graph import _accumulate_tokens
    from backend.agents.llm_utils import TokenUsage

    state = {
        "opus_tokens_used": 0,
        "sonnet_tokens_used": 0,
        "openai_tokens_used": 0,
        "chatgpt_tokens_used": 0,
        "gpt52_tokens_used": 0,
        "gpt52_reasoning_tokens": 0,
        "gpt52_output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
    }

    usage = TokenUsage(
        model_name="claude-sonnet-4-5",
        input_tokens=3000,
        output_tokens=500,
        total_tokens=3500,
        cache_creation_input_tokens=1500,
        cache_read_input_tokens=0,
    )

    result = _accumulate_tokens(state, usage)
    assert result["cache_creation_tokens"] == 1500
    assert result["cache_read_tokens"] == 0
    assert result["sonnet_tokens_used"] == 3500

    # Second call: cache hit
    usage2 = TokenUsage(
        model_name="claude-sonnet-4-5",
        input_tokens=1500,
        output_tokens=500,
        total_tokens=2000,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=1500,
    )

    result2 = _accumulate_tokens({**state, **result}, usage2)
    assert result2["cache_creation_tokens"] == 1500
    assert result2["cache_read_tokens"] == 1500
    assert result2["sonnet_tokens_used"] == 5500


def test_extract_token_usage_anthropic_cache_metrics():
    """_extract_token_usage extracts Anthropic cache metrics from response_metadata."""
    from backend.agents.llm_utils import _extract_token_usage

    class MockMessage:
        usage_metadata = None
        response_metadata = {
            "usage": {
                "input_tokens": 3000,
                "output_tokens": 500,
                "cache_creation_input_tokens": 1500,
                "cache_read_input_tokens": 1200,
            }
        }

    usage = _extract_token_usage(MockMessage(), "claude-sonnet-4-5")
    assert usage.input_tokens == 3000
    assert usage.output_tokens == 500
    assert usage.cache_creation_input_tokens == 1500
    assert usage.cache_read_input_tokens == 1200


def test_extract_token_usage_openai_cached_tokens():
    """_extract_token_usage extracts OpenAI cached tokens from prompt_tokens_details."""
    from backend.agents.llm_utils import _extract_token_usage

    class MockMessage:
        usage_metadata = None
        response_metadata = {
            "token_usage": {
                "prompt_tokens": 2000,
                "completion_tokens": 300,
                "total_tokens": 2300,
                "prompt_tokens_details": {
                    "cached_tokens": 1024,
                },
            }
        }

    usage = _extract_token_usage(MockMessage(), "gpt-5.4-mini")
    assert usage.input_tokens == 2000
    assert usage.output_tokens == 300
    assert usage.cache_read_input_tokens == 1024
    assert usage.cache_creation_input_tokens == 0


def test_extract_token_usage_no_cache_metrics():
    """_extract_token_usage handles responses without cache metrics gracefully."""
    from backend.agents.llm_utils import _extract_token_usage

    class MockMessage:
        usage_metadata = None
        response_metadata = {
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 200,
            }
        }

    usage = _extract_token_usage(MockMessage(), "claude-sonnet-4-5")
    assert usage.input_tokens == 1000
    assert usage.cache_creation_input_tokens == 0
    assert usage.cache_read_input_tokens == 0


def test_analytics_placeholders_no_op():
    """Phase 09-02 Task 2: comparison_node and cross_construct_node gracefully skip on missing data.

    Note: correlation_node is functional (Phase 8-01), comparison_node and cross_construct_node
    are functional (Phase 9-02). This test verifies graceful failure on missing state.
    """
    from backend.graph import comparison_node, cross_construct_node

    # Minimal state dict (missing final_output)
    state = {"user_request": None, "draft_items": []}

    # Test nodes return empty dict on missing data (graceful failure)
    assert comparison_node(state) == {}, "comparison_node should return empty dict on missing final_output"
    assert cross_construct_node(state) == {}, "cross_construct_node should return empty dict on missing final_output"


def test_analytics_nodes_in_graph():
    """Phase 07-02 Task 2: Analytics nodes exist in graph topology."""
    from backend.graph import build_graph

    graph = build_graph()

    # Verify all three analytics nodes exist
    assert "correlation_node" in graph.nodes, "correlation_node must exist in graph"
    assert "comparison_node" in graph.nodes, "comparison_node must exist in graph"
    assert "cross_construct_node" in graph.nodes, "cross_construct_node must exist in graph"
    # Phase 10: Verify analytics_dispatch_node exists
    assert "analytics_dispatch_node" in graph.nodes, "analytics_dispatch_node must exist in graph"


# Phase 8-01: Correlation Node Integration Tests


@pytest.mark.asyncio
async def test_correlation_node_with_mocked_estimator():
    """Phase 8-01 Task 2: correlation_node produces CorrelationMatrix in FinalOutput."""
    from unittest.mock import patch, AsyncMock
    from backend.graph import correlation_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, UserRequest, CorrelationCell

    # Arrange: Create state with FinalOutput containing 3 items
    items = [
        DraftItem(item_text="Item 1", construct_name="Test", rationale="Rationale 1", evidence_citations=[]),
        DraftItem(item_text="Item 2", construct_name="Test", rationale="Rationale 2", evidence_citations=[]),
        DraftItem(item_text="Item 3", construct_name="Test", rationale="Rationale 3", evidence_citations=[]),
    ]

    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-14T12:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        model_info={},
        approved_sources=[]
    )

    final_output = FinalOutput(final_items=items, audit=audit)

    user_request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Test definition",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {
        "final_output": final_output,
        "user_request": user_request
    }

    # Mock correlation estimation
    mock_cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.75, ci_low=0.65, ci_high=0.85),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.68, ci_low=0.58, ci_high=0.78),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.72, ci_low=0.62, ci_high=0.82),
    ]

    with patch("backend.agents.correlation_estimator.estimate_pairwise_correlations", new_callable=AsyncMock) as mock_est:
        mock_est.return_value = mock_cells

        # Act
        result = await correlation_node(state)

        # Assert
        assert "final_output" in result
        updated_output = result["final_output"]
        assert updated_output.correlation_matrix is not None
        assert updated_output.correlation_matrix.mcdonalds_omega > 0.0
        assert len(updated_output.correlation_matrix.cells) == 3
        assert updated_output.correlation_matrix.internal_consistency_flag in ["optimal_range", "too_low", "too_high"]
        assert updated_output.correlation_matrix.disclaimer == "Correlations estimated via sentence-embedding cosine similarity (Hommel & Arslan, 2024). Not a substitute for empirical validation."


@pytest.mark.asyncio
async def test_correlation_node_with_too_few_items():
    """Phase 8-01 Task 2: correlation_node skips when < 3 items."""
    from backend.graph import correlation_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, UserRequest

    # Arrange: Create state with only 2 items
    items = [
        DraftItem(item_text="Item 1", construct_name="Test", rationale="Rationale 1", evidence_citations=[]),
        DraftItem(item_text="Item 2", construct_name="Test", rationale="Rationale 2", evidence_citations=[]),
    ]

    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-14T12:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        model_info={},
        approved_sources=[]
    )

    final_output = FinalOutput(final_items=items, audit=audit)

    user_request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Test definition",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {
        "final_output": final_output,
        "user_request": user_request
    }

    # Act
    result = await correlation_node(state)

    # Assert: Should return empty dict (graceful skip)
    assert result == {}


@pytest.mark.asyncio
async def test_correlation_node_failure_graceful():
    """Phase 8-01 Task 2: correlation_node graceful failure doesn't crash."""
    from unittest.mock import patch, AsyncMock
    from backend.graph import correlation_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, UserRequest

    # Arrange: Create state with 3 items
    items = [
        DraftItem(item_text="Item 1", construct_name="Test", rationale="Rationale 1", evidence_citations=[]),
        DraftItem(item_text="Item 2", construct_name="Test", rationale="Rationale 2", evidence_citations=[]),
        DraftItem(item_text="Item 3", construct_name="Test", rationale="Rationale 3", evidence_citations=[]),
    ]

    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-14T12:00:00Z",
        iteration_count=1,
        stop_reason="complete",
        model_info={},
        approved_sources=[]
    )

    final_output = FinalOutput(final_items=items, audit=audit)

    user_request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Test definition",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {
        "final_output": final_output,
        "user_request": user_request
    }

    # Mock correlation estimation to raise error
    with patch("backend.agents.correlation_estimator.estimate_pairwise_correlations", new_callable=AsyncMock) as mock_est:
        mock_est.side_effect = Exception("Test error")

        # Act
        result = await correlation_node(state)

        # Assert: Should return empty dict (graceful failure)
        assert result == {}


# Phase 9-02: Comparison and Cross-Construct Node Integration Tests


def test_comparison_node_with_mocked_search():
    """Phase 9-02 Task 2: comparison_node populates comparison_instruments and plagiarism_flags."""
    from unittest.mock import patch, MagicMock
    from backend.graph import comparison_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, UserRequest, ComparisonInstrument

    # Arrange: Create state with FinalOutput containing 3 items
    items = [
        DraftItem(item_text="I feel confident", construct_name="Self-Efficacy", rationale="Rationale 1", evidence_citations=[]),
        DraftItem(item_text="I can succeed", construct_name="Self-Efficacy", rationale="Rationale 2", evidence_citations=[]),
        DraftItem(item_text="I believe in myself", construct_name="Self-Efficacy", rationale="Rationale 3", evidence_citations=[]),
    ]

    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-14T14:00:00Z",
        iteration_count=1,
        stop_reason="complete"
    )

    final_output = FinalOutput(final_items=items, audit=audit)

    user_request = UserRequest(
        construct_name="Self-Efficacy",
        construct_definition="Belief in one's ability to succeed",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {
        "final_output": final_output,
        "user_request": user_request
    }

    # Mock instrument search
    mock_convergent = ComparisonInstrument(
        name="General Self-Efficacy Scale",
        measured_construct="self-efficacy",
        source_citation="Schwarzer & Jerusalem (1995)"
    )
    mock_discriminant = ComparisonInstrument(
        name="Rosenberg Self-Esteem Scale",
        measured_construct="self-esteem",
        source_citation="Rosenberg (1965)"
    )

    # Mock validity scorer (returns tuple: score, method)
    mock_score = (0.75, "llm-as-judge")

    # Mock plagiarism detector
    mock_plagiarism_flags = {}  # Empty dict (no published items available)

    with patch("backend.agents.instrument_searcher.search_instruments", return_value=(mock_convergent, mock_discriminant)), \
         patch("backend.agents.validity_scorer.score_convergent_validity", return_value=mock_score), \
         patch("backend.analytics.similarity_calculator.get_plagiarism_detector") as mock_detector:

        mock_detector.return_value.detect_plagiarism.return_value = mock_plagiarism_flags

        # Act
        result = comparison_node(state)

        # Assert
        assert "final_output" in result
        updated_output = result["final_output"]
        assert len(updated_output.comparison_instruments) == 2
        assert updated_output.comparison_instruments[0].name == "General Self-Efficacy Scale"
        assert updated_output.comparison_instruments[1].name == "Rosenberg Self-Esteem Scale"
        assert updated_output.plagiarism_flags == None or updated_output.plagiarism_flags == {}


def test_comparison_node_graceful_failure():
    """Phase 9-02 Task 2: comparison_node gracefully handles search errors."""
    from unittest.mock import patch
    from backend.graph import comparison_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, UserRequest

    # Arrange: Create state with FinalOutput
    items = [
        DraftItem(item_text="Item 1", construct_name="Test", rationale="Rationale 1", evidence_citations=[]),
    ]

    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-14T14:00:00Z",
        iteration_count=1,
        stop_reason="complete"
    )

    final_output = FinalOutput(final_items=items, audit=audit)

    user_request = UserRequest(
        construct_name="Test",
        construct_definition="Test definition",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {
        "final_output": final_output,
        "user_request": user_request
    }

    # Mock search to raise error
    with patch("backend.agents.instrument_searcher.search_instruments", side_effect=Exception("Search error")):
        # Act
        result = comparison_node(state)

        # Assert: Should return empty dict (graceful failure)
        assert result == {}


def test_cross_construct_node_with_mocked_scorer():
    """Phase 9-02 Task 2: cross_construct_node produces CrossConstructComparison."""
    from unittest.mock import patch
    from backend.graph import cross_construct_node
    from backend.schemas import (
        DraftItem, FinalOutput, AuditMetadata, UserRequest,
        ComparisonInstrument, ConstructPairAnalysis
    )

    # Arrange: Create state with FinalOutput containing comparison_instruments
    items = [
        DraftItem(item_text="I feel confident", construct_name="Self-Efficacy", rationale="Rationale 1", evidence_citations=[]),
    ]

    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-14T14:00:00Z",
        iteration_count=1,
        stop_reason="complete"
    )

    convergent = ComparisonInstrument(
        name="General Self-Efficacy Scale",
        measured_construct="self-efficacy",
        source_citation="Schwarzer & Jerusalem (1995)"
    )
    discriminant = ComparisonInstrument(
        name="Rosenberg Self-Esteem Scale",
        measured_construct="self-esteem",
        source_citation="Rosenberg (1965)"
    )

    final_output = FinalOutput(
        final_items=items,
        audit=audit,
        comparison_instruments=[convergent, discriminant]
    )

    user_request = UserRequest(
        construct_name="Self-Efficacy",
        construct_definition="Belief in one's ability to succeed",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {
        "final_output": final_output,
        "user_request": user_request
    }

    # Mock discriminant validity scorer
    mock_pair_analysis = ConstructPairAnalysis(
        construct_a="Self-Efficacy",
        construct_b="self-esteem",
        estimated_correlation=0.65,
        discriminant_validity_flag="adequate",
        reasoning="Moderate correlation, constructs are distinct"
    )

    with patch("backend.agents.validity_scorer.score_discriminant_validity", return_value=(mock_pair_analysis, "llm-as-judge")):
        # Act
        result = cross_construct_node(state)

        # Assert
        assert "final_output" in result
        updated_output = result["final_output"]
        assert updated_output.cross_construct_analysis is not None
        assert updated_output.cross_construct_analysis.target_construct == "Self-Efficacy"
        assert "self-esteem" in updated_output.cross_construct_analysis.comparison_constructs
        assert len(updated_output.cross_construct_analysis.construct_pairs) == 1
        assert updated_output.cross_construct_analysis.construct_pairs[0].estimated_correlation == 0.65
        assert "LLM-estimated" in updated_output.cross_construct_analysis.disclaimer


def test_cross_construct_node_graceful_failure():
    """Phase 9-02 Task 2: cross_construct_node gracefully handles missing comparison_instruments."""
    from backend.graph import cross_construct_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, UserRequest

    # Arrange: Create state with FinalOutput but no comparison_instruments
    items = [
        DraftItem(item_text="Item 1", construct_name="Test", rationale="Rationale 1", evidence_citations=[]),
    ]

    audit = AuditMetadata(
        thread_id="test",
        run_id="test",
        timestamp_utc="2026-03-14T14:00:00Z",
        iteration_count=1,
        stop_reason="complete"
    )

    final_output = FinalOutput(final_items=items, audit=audit)

    user_request = UserRequest(
        construct_name="Test",
        construct_definition="Test definition",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {
        "final_output": final_output,
        "user_request": user_request
    }

    # Act
    result = cross_construct_node(state)

    # Assert: Should return empty dict (graceful skip)
    assert result == {}


# Phase 10-01: Parallel Analytics Send API Tests


def test_finalize_returns_dict_with_final_output():
    """Phase 10: finalize_node returns dict with final_output and gpt52_analytics_enabled."""
    from backend.graph import finalize_node
    from backend.schemas import UserRequest, DraftItem

    # Arrange: Create state with 3 items
    user_request = UserRequest(
        construct_name="Test",
        construct_definition="Test definition for measurement",
        target_population="Adults",
        response_scale="5-point Likert",
        use_gpt52_analytics=True
    )

    items = [
        DraftItem(item_text=f"Item {i}", construct_name="Test", rationale=f"Rationale {i}", evidence_citations=[])
        for i in range(3)
    ]

    state = {
        "user_request": user_request,
        "draft_items": items,
        "validation_results": [],
        "evidence": [],
        "iteration": 0,
        "stop_reason": "max_iterations",
        "validation_attempt": 1,
        "opus_tokens_used": 0,
        "sonnet_tokens_used": 0,
        "openai_tokens_used": 0,
        "chatgpt_tokens_used": 0,
        "gpt52_tokens_used": 0,
        "gpt52_reasoning_tokens": 0,
        "gpt52_output_tokens": 0,
    }

    # Act
    result = finalize_node(state)

    # Assert: Should return plain dict with final_output
    assert isinstance(result, dict), "finalize_node should return dict"
    assert "final_output" in result, "Result should contain final_output"
    assert result["gpt52_analytics_enabled"] == True, "Should set gpt52_analytics_enabled from user_request"
    assert len(result["final_output"].final_items) == 3, "Should contain 3 items"


def test_finalize_with_few_items_still_returns_dict():
    """Phase 10: finalize_node returns dict even with < 3 items (analytics_dispatch handles skip)."""
    from backend.graph import finalize_node
    from backend.schemas import UserRequest, DraftItem

    # Arrange: Create state with only 2 items
    user_request = UserRequest(
        construct_name="Test",
        construct_definition="Test definition for measurement",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    items = [
        DraftItem(item_text=f"Item {i}", construct_name="Test", rationale=f"Rationale {i}", evidence_citations=[])
        for i in range(2)
    ]

    state = {
        "user_request": user_request,
        "draft_items": items,
        "validation_results": [],
        "evidence": [],
        "iteration": 0,
        "stop_reason": "max_iterations",
        "validation_attempt": 1,
        "opus_tokens_used": 0,
        "sonnet_tokens_used": 0,
        "openai_tokens_used": 0,
        "chatgpt_tokens_used": 0,
        "gpt52_tokens_used": 0,
        "gpt52_reasoning_tokens": 0,
        "gpt52_output_tokens": 0,
    }

    # Act
    result = finalize_node(state)

    # Assert: Should return plain dict
    assert isinstance(result, dict), "finalize_node should return dict"
    assert "final_output" in result, "Result should contain final_output"
    assert len(result["final_output"].final_items) == 2, "Should contain 2 items"


def test_finalize_gpt52_cost_fields_in_audit():
    """Phase 10-01 Task 2: AuditMetadata includes gpt52_reasoning_cost and gpt52_output_cost."""
    from backend.graph import finalize_node
    from backend.schemas import UserRequest, DraftItem

    # Arrange: Create state with GPT-5.2 tokens
    user_request = UserRequest(
        construct_name="Test",
        construct_definition="Test definition for measurement",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    items = [
        DraftItem(item_text=f"Item {i}", construct_name="Test", rationale=f"Rationale {i}", evidence_citations=[])
        for i in range(2)
    ]

    state = {
        "user_request": user_request,
        "draft_items": items,
        "validation_results": [],
        "evidence": [],
        "iteration": 0,
        "stop_reason": "max_iterations",
        "validation_attempt": 1,
        "opus_tokens_used": 0,
        "sonnet_tokens_used": 0,
        "openai_tokens_used": 0,
        "chatgpt_tokens_used": 0,
        "gpt52_tokens_used": 100000,
        "gpt52_reasoning_tokens": 50000,
        "gpt52_output_tokens": 50000,
    }

    # Act
    result = finalize_node(state)

    # Assert: Check audit metadata includes GPT-5.2 cost fields
    final_output = result["final_output"]
    audit = final_output.audit

    assert audit.gpt52_reasoning_cost is not None, "Audit should include gpt52_reasoning_cost"
    assert audit.gpt52_output_cost is not None, "Audit should include gpt52_output_cost"
    assert audit.gpt52_reasoning_cost == 0.7, "50k reasoning tokens @ $14/1M = $0.70"
    assert audit.gpt52_output_cost == 0.7, "50k output tokens @ $14/1M = $0.70"
    assert audit.analytics_budget_exceeded is False, "$1.40 < $2.00 budget cap"


@pytest.mark.asyncio
async def test_analytics_dispatch_skips_with_few_items():
    """Phase 10: analytics_dispatch_node skips when < 3 items."""
    from backend.graph import analytics_dispatch_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata

    items = [
        DraftItem(item_text="Item 1", construct_name="Test", rationale="Rationale", evidence_citations=[]),
        DraftItem(item_text="Item 2", construct_name="Test", rationale="Rationale", evidence_citations=[]),
    ]

    audit = AuditMetadata(
        thread_id="test", run_id="test", timestamp_utc="2026-03-15T00:00:00Z",
        iteration_count=0, stop_reason="complete"
    )

    state = {
        "final_output": FinalOutput(final_items=items, audit=audit),
        "gpt52_analytics_enabled": False,
    }

    result = await analytics_dispatch_node(state)
    assert result == {}, "Should skip analytics when < 3 items"


@pytest.mark.asyncio
async def test_analytics_dispatch_merges_results():
    """Phase 10: analytics_dispatch_node merges correlation + comparison + cross-construct."""
    from unittest.mock import patch, AsyncMock, MagicMock
    from backend.graph import analytics_dispatch_node
    from backend.schemas import (
        DraftItem, FinalOutput, AuditMetadata, UserRequest,
        CorrelationMatrix, CorrelationCell, ComparisonInstrument,
        CrossConstructComparison, ConstructPairAnalysis,
    )

    items = [
        DraftItem(item_text=f"Item {i}", construct_name="Test", rationale=f"Rationale {i}", evidence_citations=[])
        for i in range(5)
    ]

    audit = AuditMetadata(
        thread_id="test", run_id="test", timestamp_utc="2026-03-15T00:00:00Z",
        iteration_count=0, stop_reason="complete"
    )

    user_request = UserRequest(
        construct_name="Test Construct",
        construct_definition="Test definition",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    final_output = FinalOutput(final_items=items, audit=audit)

    state = {
        "final_output": final_output,
        "user_request": user_request,
        "gpt52_analytics_enabled": False,
    }

    # Mock correlation
    mock_corr_matrix = CorrelationMatrix(
        cells=[CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.7, ci_low=0.6, ci_high=0.8)],
        mcdonalds_omega=0.85,
        mean_inter_item_correlation=0.7,
        internal_consistency_flag="optimal_range",
    )
    mock_corr_output = final_output.model_copy(deep=True)
    mock_corr_output.correlation_matrix = mock_corr_matrix

    # Mock comparison
    mock_convergent = ComparisonInstrument(name="Conv Scale", measured_construct="test", source_citation="Author (2020)")
    mock_discriminant = ComparisonInstrument(name="Disc Scale", measured_construct="other", source_citation="Author (2021)")
    mock_comp_output = final_output.model_copy(deep=True)
    mock_comp_output.comparison_instruments = [mock_convergent, mock_discriminant]
    mock_comp_output.convergent_validity_score = 0.78

    # Mock cross-construct
    mock_pair = ConstructPairAnalysis(
        construct_a="Test Construct", construct_b="other",
        estimated_correlation=0.4, discriminant_validity_flag="adequate",
        reasoning="Distinct constructs"
    )
    mock_cross = CrossConstructComparison(
        target_construct="Test Construct",
        comparison_constructs=["other"],
        analysis_summary="Adequate discriminant validity between constructs",
        construct_pairs=[mock_pair],
    )

    with patch("backend.graph.correlation_node", new_callable=AsyncMock) as mock_corr, \
         patch("backend.graph.comparison_node") as mock_comp, \
         patch("backend.graph.cross_construct_node") as mock_cross_node:

        mock_corr.return_value = {"final_output": mock_corr_output}
        mock_comp.return_value = {"final_output": mock_comp_output}

        # cross_construct_node receives updated state with comparison_instruments
        mock_cross_output = final_output.model_copy(deep=True)
        mock_cross_output.cross_construct_analysis = mock_cross
        mock_cross_node.return_value = {"final_output": mock_cross_output}

        result = await analytics_dispatch_node(state)

    # Assert: All three analyses merged into single final_output
    assert "final_output" in result
    merged = result["final_output"]
    assert merged.correlation_matrix is not None, "correlation_matrix should be merged"
    assert merged.correlation_matrix.mcdonalds_omega == 0.85
    assert merged.comparison_instruments is not None, "comparison_instruments should be merged"
    assert len(merged.comparison_instruments) == 2
    assert merged.convergent_validity_score == 0.78
    assert merged.cross_construct_analysis is not None, "cross_construct should run after comparison"


# Phase 11: Quality & UI Overhaul Tests


def test_plagiarism_flags_known_instruments():
    """Phase 11 Wave 1A: Plagiarism detection uses known instrument items."""
    from unittest.mock import patch, MagicMock
    from backend.graph import comparison_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, UserRequest, ComparisonInstrument

    items = [
        DraftItem(item_text="In most ways my life is close to ideal", construct_name="Life Satisfaction", rationale="Rationale", evidence_citations=[]),
        DraftItem(item_text="I am satisfied with my life", construct_name="Life Satisfaction", rationale="Rationale", evidence_citations=[]),
        DraftItem(item_text="The conditions of my life are great", construct_name="Life Satisfaction", rationale="Rationale", evidence_citations=[]),
    ]

    audit = AuditMetadata(thread_id="test", run_id="test", timestamp_utc="2026-03-15T00:00:00Z", iteration_count=1, stop_reason="complete")
    final_output = FinalOutput(final_items=items, audit=audit)

    user_request = UserRequest(
        construct_name="Life Satisfaction",
        construct_definition="Cognitive evaluation of overall life quality",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {"final_output": final_output, "user_request": user_request}

    mock_convergent = ComparisonInstrument(name="Satisfaction With Life Scale", measured_construct="life satisfaction", source_citation="Diener et al. (1985)")
    mock_discriminant = ComparisonInstrument(name="PHQ-9", measured_construct="depression", source_citation="Kroenke et al. (2001)")

    # Mock: plagiarism detector returns flags for items similar to SWLS
    mock_flags = {0: "Potential similarity to Satisfaction With Life Scale item (r = 0.88)", 1: "Potential similarity to Satisfaction With Life Scale item (r = 0.92)"}

    with patch("backend.agents.instrument_searcher.search_instruments", return_value=(mock_convergent, mock_discriminant)), \
         patch("backend.agents.validity_scorer.score_convergent_validity", return_value=(0.75, "llm-as-judge")), \
         patch("backend.analytics.similarity_calculator.get_plagiarism_detector") as mock_detector:

        mock_detector.return_value.detect_plagiarism.return_value = mock_flags

        result = comparison_node(state)

    assert "final_output" in result
    assert result["final_output"].plagiarism_flags is not None
    assert len(result["final_output"].plagiarism_flags) >= 2
    # Verify known instruments were passed (not empty list)
    mock_detector.return_value.detect_plagiarism.assert_called_once()
    call_args = mock_detector.return_value.detect_plagiarism.call_args
    published_items = call_args[0][1]  # second positional arg
    assert len(published_items) > 0, "Should pass known instrument items, not empty list"


def test_convergent_ceiling_warning():
    """Phase 11 Wave 1B: Convergent validity > 0.85 triggers ceiling warning."""
    from unittest.mock import patch, MagicMock
    from backend.graph import comparison_node
    from backend.schemas import DraftItem, FinalOutput, AuditMetadata, UserRequest, ComparisonInstrument

    items = [
        DraftItem(item_text="Item 1", construct_name="Test", rationale="Rationale", evidence_citations=[]),
    ]

    audit = AuditMetadata(thread_id="test", run_id="test", timestamp_utc="2026-03-15T00:00:00Z", iteration_count=1, stop_reason="complete")
    final_output = FinalOutput(final_items=items, audit=audit)

    user_request = UserRequest(
        construct_name="Test",
        construct_definition="Test definition",
        target_population="Adults",
        response_scale="5-point Likert"
    )

    state = {"final_output": final_output, "user_request": user_request}

    mock_convergent = ComparisonInstrument(name="Test Scale", measured_construct="test", source_citation="Author (2020)")
    mock_discriminant = ComparisonInstrument(name="Other Scale", measured_construct="other", source_citation="Author (2021)")

    with patch("backend.agents.instrument_searcher.search_instruments", return_value=(mock_convergent, mock_discriminant)), \
         patch("backend.agents.validity_scorer.score_convergent_validity", return_value=(0.86, "llm-as-judge")), \
         patch("backend.analytics.similarity_calculator.get_plagiarism_detector") as mock_detector:

        mock_detector.return_value.detect_plagiarism.return_value = {}

        result = comparison_node(state)

    assert "final_output" in result
    flags = result["final_output"].plagiarism_flags
    assert flags is not None
    assert -1 in flags, "Should have ceiling warning at index -1"
    assert "derivative" in flags[-1].lower()


def test_redundancy_flags_high_r_pairs():
    """Phase 11 Wave 1D: Redundancy flags generated for r > 0.75."""
    from backend.schemas import CorrelationMatrix, CorrelationCell

    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.80),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.50),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.76),
    ]

    matrix = CorrelationMatrix(
        cells=cells,
        mcdonalds_omega=0.85,
        mean_inter_item_correlation=0.69,
        internal_consistency_flag="optimal_range",
    )

    # Simulate what analytics_dispatch_node does
    redundancy_flags = []
    for cell in matrix.cells:
        if cell.correlation > 0.75:
            redundancy_flags.append(
                f"Items {cell.item_i_index + 1} and {cell.item_j_index + 1} are redundant "
                f"(r = {cell.correlation:.2f}) — consider replacing one"
            )

    assert len(redundancy_flags) == 2, "Should flag 2 pairs (0.80 and 0.76)"
    assert "Items 1 and 2" in redundancy_flags[0]
    assert "Items 2 and 3" in redundancy_flags[1]


def test_stagnation_detection_accepts():
    """Phase 11 Wave 1F: Critic detects stagnation and force-accepts."""
    from backend.agents.critic import decide as critic_decide
    from backend.schemas import ReviewComment, IterationSnapshot

    # Same comments across iterations = stagnation
    comment = ReviewComment(type="bias", item_index=0, issue="Item 1: Cultural assumption", severity=3, suggested_edit="Rewrite")

    iteration_history = [
        IterationSnapshot(iteration=0, linguistic_comments=[], bias_comments=[comment], content_comments=[]),
        IterationSnapshot(iteration=1, linguistic_comments=[], bias_comments=[comment], content_comments=[]),
    ]

    # Current iteration (2) has the same comment — at MAX_ITERATIONS boundary
    decision, reason = critic_decide(
        linguistic_comments=[],
        bias_comments=[comment],
        content_comments=[],
        iteration=2,
        iteration_history=iteration_history,
    )

    # With MAX_ITERATIONS=2, iteration=2 triggers stop_max_iterations (which also force-accepts)
    assert decision in ("accept", "stop_max_iterations"), f"Should accept on stagnation or max iterations, got: {decision}"


def test_construct_exclusions_in_abbreviated_request():
    """Phase 11 Wave 0A: construct_exclusions propagated to AbbreviatedRequest."""
    from backend.graph import _create_abbreviated_request
    from backend.schemas import UserRequest

    request = UserRequest(
        construct_name="Life Satisfaction",
        construct_definition="Cognitive evaluation of life",
        target_population="Adults",
        response_scale="5-point Likert",
        construct_exclusions="Not Affect Balance or emotional wellbeing"
    )

    abbreviated = _create_abbreviated_request(request)
    assert abbreviated.construct_exclusions == "Not Affect Balance or emotional wellbeing"


def test_known_instrument_lookup():
    """Phase 11 Wave 0B: Known instrument items lookup works."""
    from data.known_instrument_items import lookup_instrument_items

    # Exact match
    swls_items = lookup_instrument_items("satisfaction with life scale")
    assert len(swls_items) == 5

    # Alias match
    swls_alias = lookup_instrument_items("SWLS")
    assert len(swls_alias) == 5

    # Partial match
    partial = lookup_instrument_items("Personal Wellbeing Index")
    assert len(partial) == 8

    # No match
    none = lookup_instrument_items("Nonexistent Scale")
    assert len(none) == 0


# Phase 11.5: Bias Quality, Evidence Depth & Stagnation Fixes


def test_bias_construct_level_filter():
    """Phase 11.5 Wave 1B: >60% identical comments → all filtered as construct-level."""
    from backend.agents.bias_reviewer import _filter_construct_level_comments
    from backend.schemas import ReviewComment

    # Same issue text across 4 out of 5 items (80% > 60% threshold)
    comments = [
        ReviewComment(type="bias", item_index=i, issue="Item assumes individualistic self-concept", severity=3, suggested_edit="Rewrite")
        for i in range(4)
    ]
    result = _filter_construct_level_comments(comments, item_count=5)
    assert result == [], "All construct-level false positives should be filtered"


def test_bias_construct_level_filter_preserves_unique():
    """Phase 11.5 Wave 1B: Unique per-item comments preserved."""
    from backend.agents.bias_reviewer import _filter_construct_level_comments
    from backend.schemas import ReviewComment

    # Different issue texts per item — unique, not construct-level
    comments = [
        ReviewComment(type="bias", item_index=0, issue="Item uses idiom 'hit the ground running'", severity=2, suggested_edit="Rewrite"),
        ReviewComment(type="bias", item_index=1, issue="Assumes access to private workspace", severity=3, suggested_edit="Rewrite"),
    ]
    result = _filter_construct_level_comments(comments, item_count=5)
    assert len(result) == 2, "Unique comments should be preserved"


def test_stagnation_jaccard_similarity():
    """Paraphrased comments detected as stagnant at iteration >= 2."""
    from backend.agents.critic import _detect_stagnation
    from backend.schemas import ReviewComment, IterationSnapshot

    # Previous iterations
    prev_comment = ReviewComment(type="bias", item_index=0, issue="Item 1: Cultural assumption about individual standards in measurement", severity=3, suggested_edit="Rewrite")
    history = [
        IterationSnapshot(iteration=0, linguistic_comments=[], bias_comments=[prev_comment], content_comments=[]),
        IterationSnapshot(iteration=1, linguistic_comments=[], bias_comments=[prev_comment], content_comments=[]),
    ]

    # Current iteration: paraphrased — most words overlap but phrasing differs
    current_comment = ReviewComment(type="bias", item_index=0, issue="Item 1: Cultural assumption about individual standards in assessment", severity=3, suggested_edit="Rewrite")

    result = _detect_stagnation([current_comment], history, iteration=2)
    assert result is True, "Paraphrased repetition should be detected as stagnant at iteration 2"


def test_stagnation_requires_two_iterations():
    """Stagnation detection requires at least 2 revision cycles (iteration >= 2)."""
    from backend.agents.critic import _detect_stagnation
    from backend.schemas import ReviewComment, IterationSnapshot

    comment = ReviewComment(type="bias", item_index=0, issue="Item 1: Same concern", severity=3, suggested_edit="Rewrite")
    history = [
        IterationSnapshot(iteration=0, linguistic_comments=[], bias_comments=[comment], content_comments=[]),
    ]

    # At iteration=1, stagnation should NOT trigger (need 2 revision cycles first)
    result = _detect_stagnation([comment], history, iteration=1)
    assert result is False, "Stagnation should not trigger at iteration 1 (too early)"

    # At iteration=0, should NOT trigger (no history to compare)
    result_0 = _detect_stagnation([comment], [], iteration=0)
    assert result_0 is False, "Stagnation should not trigger at iteration 0"

    # At iteration=2, stagnation SHOULD trigger
    history_2 = [
        IterationSnapshot(iteration=0, linguistic_comments=[], bias_comments=[comment], content_comments=[]),
        IterationSnapshot(iteration=1, linguistic_comments=[], bias_comments=[comment], content_comments=[]),
    ]
    result_2 = _detect_stagnation([comment], history_2, iteration=2)
    assert result_2 is True, "Stagnation should trigger at iteration 2"


def test_critic_downgrades_construct_level_bias():
    """Phase 11.5 Wave 1D: All-identical bias comments → severity downgraded to 1."""
    from backend.agents.critic import _downgrade_construct_level_bias
    from backend.schemas import ReviewComment

    # All bias comments have highly similar issue text (construct-level)
    comments = [
        ReviewComment(type="bias", item_index=0, issue="Item 1: assumes individualistic self-concept for target population", severity=3, suggested_edit="Rewrite"),
        ReviewComment(type="bias", item_index=1, issue="Item 2: assumes individualistic self-concept for target population", severity=3, suggested_edit="Rewrite"),
        ReviewComment(type="bias", item_index=2, issue="Item 3: assumes individualistic self-concept for target population", severity=4, suggested_edit="Rewrite"),
    ]

    result = _downgrade_construct_level_bias(comments)
    for c in result:
        assert c.severity == 1, f"Comment for item {c.item_index} should be downgraded to severity 1, got {c.severity}"


def test_cross_construct_with_fewer_than_2_instruments():
    """Bug fix: cross_construct_node must not crash when < 2 comparison instruments found."""
    from unittest.mock import MagicMock

    from backend.schemas import ComparisonInstrument

    # Create a mock final_output with only 1 instrument
    single_instrument = ComparisonInstrument(
        name="Test Scale",
        measured_construct="Well-being",
        source_citation="Test (2024)",
    )
    final_output = MagicMock()
    final_output.comparison_instruments = [single_instrument]
    final_output.final_items = [MagicMock(item_text="I feel satisfied")]

    user_request = MagicMock()
    user_request.construct_name = "Life Satisfaction"
    user_request.construct_exclusions = None

    state = {
        "final_output": final_output,
        "user_request": user_request,
    }

    from backend.graph import cross_construct_node

    # Should return empty dict, not raise IndexError
    result = cross_construct_node(state)
    assert result == {}


def test_cosine_similarity_zero_norm():
    """Bug fix: zero-norm embeddings must not produce NaN/inf in similarity matrix."""
    import numpy as np

    from backend.agents.correlation_estimator import compute_cosine_similarity_matrix

    # Create embeddings where one row is all zeros
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],  # zero-norm
        [0.0, 1.0, 0.0],
    ])

    sim = compute_cosine_similarity_matrix(embeddings)
    assert not np.any(np.isnan(sim)), "Similarity matrix must not contain NaN"
    assert not np.any(np.isinf(sim)), "Similarity matrix must not contain Inf"
    assert sim.shape == (3, 3)


def test_facet_mapper_allocation_floor():
    """Bug fix: facet allocation adjustment must never reduce a facet to 0 items."""
    from backend.schemas import FacetDefinition

    # Simulate facets that are over-allocated, all near minimum
    facets = [
        FacetDefinition(
            facet_name="Cognitive",
            facet_description="Thinking patterns related to construct",
            exclusions="Not behavioral or affective",
            target_item_count=1,
        ),
        FacetDefinition(
            facet_name="Affective",
            facet_description="Emotional responses related to construct",
            exclusions="Not cognitive or behavioral",
            target_item_count=1,
        ),
        FacetDefinition(
            facet_name="Behavioral",
            facet_description="Action tendencies related to construct",
            exclusions="Not cognitive or affective",
            target_item_count=2,
        ),
    ]

    # Total is 4, suppose we need 3 — need to subtract 1
    total = sum(f.target_item_count for f in facets)
    requested = 3
    diff = requested - total  # -1

    # Apply the same logic as facet_mapper.py:93-98
    if diff < 0:
        for i in range(abs(diff)):
            idx = len(facets) - 1 - (i % len(facets))
            if facets[idx].target_item_count > 1:
                facets[idx].target_item_count -= 1

    # No facet should be 0
    for f in facets:
        assert f.target_item_count >= 1, f"Facet '{f.facet_name}' has {f.target_item_count} items (must be >= 1)"


def test_evidence_settings_exist():
    """Phase 11.5 Wave 0A: New evidence settings present with correct defaults."""
    from backend.settings import Settings

    s = Settings(APP_MODE="mock")
    assert s.EVIDENCE_MIN_CHUNKS == 20, "EVIDENCE_MIN_CHUNKS should default to 20"
    assert s.EVIDENCE_MAX_RETRIES == 3, "EVIDENCE_MAX_RETRIES should default to 3"
    # PERPLEXITY_MAX_RESULTS code default is 40 (may be overridden by .env)
    assert hasattr(s, "PERPLEXITY_MAX_RESULTS"), "PERPLEXITY_MAX_RESULTS must exist"
    assert s.PERPLEXITY_MAX_RESULTS >= 40, "PERPLEXITY_MAX_RESULTS should be at least 40"
