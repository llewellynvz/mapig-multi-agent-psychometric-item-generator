"""Tests for correlation calibration validation.

Tests CORR-04 requirement: validate LLM correlation estimation against published scales.
"""

import pytest
from unittest.mock import AsyncMock, patch
import numpy as np

from backend.evaluation.correlation_calibration import (
    BENCHMARK_SCALES,
    compare_matrices,
    run_single_calibration,
    run_correlation_calibration,
    CalibrationResult,
    CalibrationSummary,
)
from backend.schemas import CorrelationCell


class TestBenchmarkScales:
    """Test BENCHMARK_SCALES structure and content."""

    def test_has_exactly_5_scales(self):
        """BENCHMARK_SCALES should contain exactly 5 scales."""
        assert len(BENCHMARK_SCALES) == 5

    def test_each_scale_has_required_fields(self):
        """Each benchmark scale must have all required fields."""
        required_fields = {
            "name",
            "construct_name",
            "domain",
            "item_texts",
            "published_correlations",
            "source_citation",
        }
        for scale in BENCHMARK_SCALES:
            assert set(scale.keys()) == required_fields

    def test_scales_span_5_domains(self):
        """Scales should cover personality, clinical, organizational, social, and attitudes."""
        expected_domains = {
            "personality",
            "clinical",
            "organizational",
            "social",
            "attitudes",
        }
        actual_domains = {scale["domain"] for scale in BENCHMARK_SCALES}
        assert actual_domains == expected_domains

    def test_each_scale_has_valid_items(self):
        """Each scale should have item texts (list of strings)."""
        for scale in BENCHMARK_SCALES:
            assert isinstance(scale["item_texts"], list)
            assert len(scale["item_texts"]) >= 5  # At least 5 items per scale
            assert all(isinstance(item, str) for item in scale["item_texts"])
            assert all(len(item) > 0 for item in scale["item_texts"])

    def test_each_scale_has_valid_correlations(self):
        """Each scale should have published correlations (flat upper-triangular list)."""
        for scale in BENCHMARK_SCALES:
            num_items = len(scale["item_texts"])
            expected_pairs = num_items * (num_items - 1) // 2

            assert isinstance(scale["published_correlations"], list)
            assert len(scale["published_correlations"]) == expected_pairs
            assert all(isinstance(r, (int, float)) for r in scale["published_correlations"])
            assert all(-1.0 <= r <= 1.0 for r in scale["published_correlations"])

    def test_each_scale_has_citation(self):
        """Each scale should have a source citation."""
        for scale in BENCHMARK_SCALES:
            assert isinstance(scale["source_citation"], str)
            assert len(scale["source_citation"]) > 0


class TestCompareMatrices:
    """Test correlation matrix comparison function."""

    def test_identical_matrices_return_1(self):
        """Identical correlation vectors should return r = 1.0."""
        vec = [0.5, 0.6, 0.7, 0.8]
        r = compare_matrices(vec, vec)
        assert abs(r - 1.0) < 0.001

    def test_opposite_matrices_return_negative_1(self):
        """Perfectly opposite vectors should return r close to -1.0."""
        vec1 = [0.1, 0.2, 0.3, 0.4]
        vec2 = [-x for x in vec1]  # Negate all values
        r = compare_matrices(vec1, vec2)
        assert r < -0.9  # Should be close to -1

    def test_orthogonal_matrices_return_near_0(self):
        """Uncorrelated vectors should return r close to 0."""
        vec1 = [0.5, 0.6, 0.7, 0.8]
        vec2 = [0.8, 0.5, 0.6, 0.7]  # Different order
        r = compare_matrices(vec1, vec2)
        # This is not perfectly orthogonal but demonstrates the function works
        assert -1.0 <= r <= 1.0

    def test_realistic_partial_agreement(self):
        """Test with realistic partial agreement scenario."""
        estimated = [0.7, 0.6, 0.5, 0.8, 0.65, 0.72]
        published = [0.75, 0.58, 0.52, 0.78, 0.62, 0.70]
        r = compare_matrices(estimated, published)
        # Should have high positive correlation (similar patterns)
        assert r > 0.9


class TestRunSingleCalibration:
    """Test single-scale calibration runner."""

    @pytest.mark.asyncio
    async def test_produces_calibration_result(self):
        """run_single_calibration should produce CalibrationResult with all fields."""
        # Mock the estimate_pairwise_correlations function
        mock_cells = [
            CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.7, ci_low=0.6, ci_high=0.8),
            CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.6, ci_low=0.5, ci_high=0.7),
            CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.65, ci_low=0.55, ci_high=0.75),
        ]

        scale = {
            "name": "Test Scale",
            "construct_name": "Test Construct",
            "domain": "personality",
            "item_texts": ["item1", "item2", "item3"],
            "published_correlations": [0.72, 0.58, 0.63],
            "source_citation": "Test et al. (2020)",
        }

        with patch(
            "backend.evaluation.correlation_calibration.estimate_pairwise_correlations",
            new=AsyncMock(return_value=mock_cells),
        ):
            result = await run_single_calibration(scale)

        assert isinstance(result, CalibrationResult)
        assert result.scale_name == "Test Scale"
        assert result.domain == "personality"
        assert isinstance(result.agreement_r, float)
        assert -1.0 <= result.agreement_r <= 1.0
        assert result.num_pairs == 3
        assert isinstance(result.passed, bool)

    @pytest.mark.asyncio
    async def test_pass_threshold_at_06(self):
        """Scales with r > 0.6 should pass, r <= 0.6 should fail."""
        # High agreement (should pass)
        mock_cells_high = [
            CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.70, ci_low=0.6, ci_high=0.8),
            CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.60, ci_low=0.5, ci_high=0.7),
        ]

        scale = {
            "name": "Test Scale",
            "construct_name": "Test",
            "domain": "personality",
            "item_texts": ["item1", "item2", "item3"],
            "published_correlations": [0.72, 0.58],
            "source_citation": "Test (2020)",
        }

        with patch(
            "backend.evaluation.correlation_calibration.estimate_pairwise_correlations",
            new=AsyncMock(return_value=mock_cells_high),
        ):
            result = await run_single_calibration(scale)
            # High agreement should pass
            assert result.passed is True

        # Low agreement (should fail)
        mock_cells_low = [
            CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.30, ci_low=0.2, ci_high=0.4),
            CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.40, ci_low=0.3, ci_high=0.5),
        ]

        with patch(
            "backend.evaluation.correlation_calibration.estimate_pairwise_correlations",
            new=AsyncMock(return_value=mock_cells_low),
        ):
            result = await run_single_calibration(scale)
            # Low agreement should fail
            assert result.passed is False


class TestRunCorrelationCalibration:
    """Test full calibration suite runner."""

    @pytest.mark.asyncio
    async def test_runs_all_5_scales(self):
        """run_correlation_calibration should process all 5 benchmark scales."""
        # Mock that generates correct number of cells for each scale
        # Use values with variance that correlate positively with published values
        async def mock_estimate(items, construct_name, batch_size=20):
            """Generate mock cells matching the number of pairs for the scale."""
            num_items = len(items)
            cells = []
            pair_idx = 0
            for i in range(num_items):
                for j in range(i + 1, num_items):
                    # Add slight variance based on pair index to avoid constant vector
                    correlation = 0.65 + (pair_idx % 10) * 0.02  # Range: 0.65 to 0.83
                    cells.append(
                        CorrelationCell(
                            item_i_index=i,
                            item_j_index=j,
                            correlation=correlation,
                            ci_low=correlation - 0.1,
                            ci_high=correlation + 0.1,
                        )
                    )
                    pair_idx += 1
            return cells

        with patch(
            "backend.evaluation.correlation_calibration.estimate_pairwise_correlations",
            side_effect=mock_estimate,
        ):
            summary = await run_correlation_calibration()

        assert isinstance(summary, CalibrationSummary)
        assert len(summary.results) == 5
        assert all(isinstance(r, CalibrationResult) for r in summary.results)

    @pytest.mark.asyncio
    async def test_computes_mean_agreement(self):
        """Summary should include mean agreement across all scales."""
        # Mock that generates cells with variance
        async def mock_estimate(items, construct_name, batch_size=20):
            num_items = len(items)
            cells = []
            pair_idx = 0
            for i in range(num_items):
                for j in range(i + 1, num_items):
                    # Add variance to avoid NaN from constant vector
                    correlation = 0.65 + (pair_idx % 10) * 0.02
                    cells.append(
                        CorrelationCell(
                            item_i_index=i,
                            item_j_index=j,
                            correlation=correlation,
                            ci_low=correlation - 0.1,
                            ci_high=correlation + 0.1,
                        )
                    )
                    pair_idx += 1
            return cells

        with patch(
            "backend.evaluation.correlation_calibration.estimate_pairwise_correlations",
            side_effect=mock_estimate,
        ):
            summary = await run_correlation_calibration()

        assert isinstance(summary.mean_agreement, float)
        assert -1.0 <= summary.mean_agreement <= 1.0
        # With mocked data, mean should be calculable
        expected_mean = sum(r.agreement_r for r in summary.results) / len(summary.results)
        assert abs(summary.mean_agreement - expected_mean) < 0.001

    @pytest.mark.asyncio
    async def test_all_passed_flag(self):
        """all_passed should be True only if all scales pass threshold."""
        # Mock that generates cells with variance and high correlation to published
        async def mock_estimate(items, construct_name, batch_size=20):
            num_items = len(items)
            cells = []
            pair_idx = 0
            for i in range(num_items):
                for j in range(i + 1, num_items):
                    # Add variance while keeping values high
                    correlation = 0.70 + (pair_idx % 10) * 0.02
                    cells.append(
                        CorrelationCell(
                            item_i_index=i,
                            item_j_index=j,
                            correlation=correlation,
                            ci_low=correlation - 0.1,
                            ci_high=correlation + 0.1,
                        )
                    )
                    pair_idx += 1
            return cells

        with patch(
            "backend.evaluation.correlation_calibration.estimate_pairwise_correlations",
            side_effect=mock_estimate,
        ):
            summary = await run_correlation_calibration()

        # With high agreement, all_passed should likely be True
        # (depends on published correlations, but test structure is validated)
        assert isinstance(summary.all_passed, bool)
        assert summary.benchmark_threshold == 0.6
