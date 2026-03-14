"""Test suite for correlation estimation agent.

Tests CORR-01 and CORR-03 requirements.
"""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

os.environ["APP_MODE"] = "mock"


@pytest.mark.asyncio
async def test_estimate_pairwise_correlations_basic():
    """Test basic correlation estimation with mocked LLM."""
    from backend.agents.correlation_estimator import estimate_pairwise_correlations

    # Arrange
    items = ["Item 1", "Item 2", "Item 3"]
    construct_name = "Test Construct"

    # Mock LLM response with properly formatted JSON
    mock_response = MagicMock()
    mock_response.content = """[
        {"item_i_index": 0, "item_j_index": 1, "correlation": 0.75, "ci_low": 0.65, "ci_high": 0.85},
        {"item_i_index": 0, "item_j_index": 2, "correlation": 0.68, "ci_low": 0.58, "ci_high": 0.78},
        {"item_i_index": 1, "item_j_index": 2, "correlation": 0.72, "ci_low": 0.62, "ci_high": 0.82}
    ]"""

    # Mock the LLM model
    with patch("backend.agents.correlation_estimator.get_gpt52_analytics_model") as mock_get_model:
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response
        mock_get_model.return_value = mock_model

        # Act
        cells = await estimate_pairwise_correlations(items, construct_name)

        # Assert
        assert len(cells) == 3  # 3 items = 3 pairs: (0,1), (0,2), (1,2)
        assert all(hasattr(cell, "item_i_index") for cell in cells)
        assert all(hasattr(cell, "item_j_index") for cell in cells)
        assert all(hasattr(cell, "correlation") for cell in cells)
        assert all(hasattr(cell, "ci_low") for cell in cells)
        assert all(hasattr(cell, "ci_high") for cell in cells)

        # Verify correlation indices are correct
        indices = {(cell.item_i_index, cell.item_j_index) for cell in cells}
        expected_indices = {(0, 1), (0, 2), (1, 2)}
        assert indices == expected_indices


@pytest.mark.asyncio
async def test_batching_logic():
    """Test batching works correctly for large item sets."""
    from backend.agents.correlation_estimator import estimate_pairwise_correlations

    # Arrange: 10 items = 45 pairs
    items = [f"Item {i}" for i in range(10)]
    construct_name = "Test Construct"
    batch_size = 20

    # Expected: ceil(45 / 20) = 3 batches

    # Mock LLM response generator
    def generate_mock_response(batch_start, batch_size):
        # Generate properly formatted JSON for a batch
        pairs = []
        pair_idx = 0
        for i in range(10):
            for j in range(i + 1, 10):
                if batch_start <= pair_idx < batch_start + batch_size:
                    pairs.append({
                        "item_i_index": i,
                        "item_j_index": j,
                        "correlation": 0.5 + (pair_idx % 10) * 0.05,
                        "ci_low": 0.4,
                        "ci_high": 0.6
                    })
                pair_idx += 1

        import json
        mock = MagicMock()
        mock.content = json.dumps(pairs)
        return mock

    # Track number of LLM calls
    call_count = 0

    async def mock_ainvoke(messages, **kwargs):
        nonlocal call_count
        batch_start = call_count * batch_size
        call_count += 1
        return generate_mock_response(batch_start, batch_size)

    with patch("backend.agents.correlation_estimator.get_gpt52_analytics_model") as mock_get_model:
        mock_model = AsyncMock()
        mock_model.ainvoke = mock_ainvoke
        mock_get_model.return_value = mock_model

        # Act
        cells = await estimate_pairwise_correlations(items, construct_name, batch_size=batch_size)

        # Assert
        assert len(cells) == 45  # 10 items = C(10,2) = 45 pairs
        assert call_count == 3  # Should have made 3 batched calls (45/20 = 2.25 -> 3)


@pytest.mark.asyncio
async def test_json_parse_error_handling():
    """Test graceful handling of malformed LLM JSON responses."""
    from backend.agents.correlation_estimator import estimate_pairwise_correlations

    # Arrange
    items = ["Item 1", "Item 2", "Item 3"]
    construct_name = "Test Construct"

    # Mock LLM response with invalid JSON
    call_count = 0

    async def mock_ainvoke(messages, **kwargs):
        nonlocal call_count
        call_count += 1

        mock = MagicMock()
        if call_count == 1:
            # First call: return malformed JSON
            mock.content = "This is not valid JSON at all"
        else:
            # Retry: return valid JSON
            mock.content = """[
                {"item_i_index": 0, "item_j_index": 1, "correlation": 0.75, "ci_low": 0.65, "ci_high": 0.85},
                {"item_i_index": 0, "item_j_index": 2, "correlation": 0.68, "ci_low": 0.58, "ci_high": 0.78},
                {"item_i_index": 1, "item_j_index": 2, "correlation": 0.72, "ci_low": 0.62, "ci_high": 0.82}
            ]"""
        return mock

    with patch("backend.agents.correlation_estimator.get_gpt52_analytics_model") as mock_get_model:
        mock_model = AsyncMock()
        mock_model.ainvoke = mock_ainvoke
        mock_get_model.return_value = mock_model

        # Act: Should retry once and succeed
        cells = await estimate_pairwise_correlations(items, construct_name)

        # Assert: Should eventually succeed with retry
        assert len(cells) == 3
        assert call_count == 2  # Initial call + 1 retry
