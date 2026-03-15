"""Test suite for correlation estimation agent.

Tests CORR-01 and CORR-03 requirements.
Now uses embedding-based cosine similarity (Hommel & Arslan, 2024).
"""

import os
import pytest
import numpy as np
from unittest.mock import AsyncMock, patch

os.environ["APP_MODE"] = "mock"


@pytest.mark.asyncio
async def test_estimate_pairwise_correlations_basic():
    """Test basic correlation estimation with mocked embeddings."""
    from backend.agents.correlation_estimator import estimate_pairwise_correlations

    # Arrange
    items = ["Item 1", "Item 2", "Item 3"]
    construct_name = "Test Construct"

    # Pre-computed embeddings that produce known cosine similarities
    fake_embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.8, 0.6, 0.0],
        [0.5, 0.5, 0.707],
    ])

    with patch("backend.agents.correlation_estimator.embed_items", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = fake_embeddings

        # Act
        cells = await estimate_pairwise_correlations(items, construct_name)

        # Assert
        assert len(cells) == 3  # 3 items = 3 pairs: (0,1), (0,2), (1,2)
        assert all(hasattr(cell, "item_i_index") for cell in cells)
        assert all(hasattr(cell, "item_j_index") for cell in cells)
        assert all(hasattr(cell, "correlation") for cell in cells)

        # Verify correlation indices are correct
        indices = {(cell.item_i_index, cell.item_j_index) for cell in cells}
        expected_indices = {(0, 1), (0, 2), (1, 2)}
        assert indices == expected_indices

        # Verify correlations are in valid range
        for cell in cells:
            assert -1.0 <= cell.correlation <= 1.0

        # embed_items should be called exactly once
        mock_embed.assert_called_once_with(items)


@pytest.mark.asyncio
async def test_single_api_call_for_embeddings():
    """Test that embed_items is called once regardless of item count (no batching)."""
    from backend.agents.correlation_estimator import estimate_pairwise_correlations

    # Arrange: 10 items = 45 pairs
    items = [f"Item {i}" for i in range(10)]
    construct_name = "Test Construct"

    # Generate random 10x64 embeddings
    rng = np.random.default_rng(42)
    fake_embeddings = rng.standard_normal((10, 64))

    with patch("backend.agents.correlation_estimator.embed_items", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = fake_embeddings

        # Act
        cells = await estimate_pairwise_correlations(items, construct_name)

        # Assert
        assert len(cells) == 45  # 10 items = C(10,2) = 45 pairs
        mock_embed.assert_called_once()  # Single API call, no batching


@pytest.mark.asyncio
async def test_embed_api_error_handling():
    """Test graceful failure when embed_items raises an exception."""
    from backend.agents.correlation_estimator import estimate_pairwise_correlations

    # Arrange
    items = ["Item 1", "Item 2", "Item 3"]
    construct_name = "Test Construct"

    with patch("backend.agents.correlation_estimator.embed_items", new_callable=AsyncMock) as mock_embed:
        mock_embed.side_effect = Exception("API Error: rate limit exceeded")

        # Act & Assert: Should propagate the exception
        with pytest.raises(Exception, match="API Error"):
            await estimate_pairwise_correlations(items, construct_name)
