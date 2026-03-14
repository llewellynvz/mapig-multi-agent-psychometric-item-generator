"""Test suite for McDonald's omega calculator.

Tests CORR-02 and CORR-06 requirements.
"""

import os
import pytest
import numpy as np

os.environ["APP_MODE"] = "mock"


def test_calculate_omega_basic():
    """Test basic omega calculation with known correlation matrix."""
    from backend.analytics.omega_calculator import calculate_omega
    from backend.schemas import CorrelationCell

    # Arrange: Create 3x3 correlation matrix with known structure
    # Upper triangular: (0,1)=0.6, (0,2)=0.5, (1,2)=0.7
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.6, ci_low=0.5, ci_high=0.7),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.5, ci_low=0.4, ci_high=0.6),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.7, ci_low=0.6, ci_high=0.8),
    ]

    # Act
    result = calculate_omega(cells, num_items=3)

    # Assert
    assert "omega_total" in result
    assert "mean_inter_item_correlation" in result
    assert "internal_consistency_flag" in result
    assert result["omega_total"] is not None
    assert isinstance(result["omega_total"], float)
    assert 0.0 <= result["omega_total"] <= 1.0

    # Mean inter-item correlation should be (0.6 + 0.5 + 0.7) / 3 = 0.6
    assert abs(result["mean_inter_item_correlation"] - 0.6) < 0.01


def test_internal_consistency_flag_optimal_range():
    """Test internal consistency flag = 'optimal_range' when mean r in 0.15-0.50."""
    from backend.analytics.omega_calculator import calculate_omega
    from backend.schemas import CorrelationCell

    # Arrange: Create cells with mean correlation in optimal range (0.3)
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.3, ci_low=0.2, ci_high=0.4),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.3, ci_low=0.2, ci_high=0.4),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.3, ci_low=0.2, ci_high=0.4),
    ]

    # Act
    result = calculate_omega(cells, num_items=3)

    # Assert
    assert result["internal_consistency_flag"] == "optimal_range"
    assert 0.15 <= result["mean_inter_item_correlation"] <= 0.50


def test_internal_consistency_flag_too_low():
    """Test internal consistency flag = 'too_low' when mean r < 0.15."""
    from backend.analytics.omega_calculator import calculate_omega
    from backend.schemas import CorrelationCell

    # Arrange: Create cells with mean correlation too low (0.1)
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.1, ci_low=0.0, ci_high=0.2),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.1, ci_low=0.0, ci_high=0.2),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.1, ci_low=0.0, ci_high=0.2),
    ]

    # Act
    result = calculate_omega(cells, num_items=3)

    # Assert
    assert result["internal_consistency_flag"] == "too_low"
    assert result["mean_inter_item_correlation"] < 0.15


def test_internal_consistency_flag_too_high():
    """Test internal consistency flag = 'too_high' when mean r > 0.50."""
    from backend.analytics.omega_calculator import calculate_omega
    from backend.schemas import CorrelationCell

    # Arrange: Create cells with mean correlation too high (0.8)
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.8, ci_low=0.7, ci_high=0.9),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.8, ci_low=0.7, ci_high=0.9),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=0.8, ci_low=0.7, ci_high=0.9),
    ]

    # Act
    result = calculate_omega(cells, num_items=3)

    # Assert
    assert result["internal_consistency_flag"] == "too_high"
    assert result["mean_inter_item_correlation"] > 0.50


def test_non_positive_definite_matrix_handling():
    """Test graceful handling of non-positive-definite matrices."""
    from backend.analytics.omega_calculator import calculate_omega
    from backend.schemas import CorrelationCell

    # Arrange: Create cells that produce non-positive-definite matrix
    # This is a pathological case with inconsistent correlations
    cells = [
        CorrelationCell(item_i_index=0, item_j_index=1, correlation=0.9, ci_low=0.8, ci_high=1.0),
        CorrelationCell(item_i_index=0, item_j_index=2, correlation=0.9, ci_low=0.8, ci_high=1.0),
        CorrelationCell(item_i_index=1, item_j_index=2, correlation=-0.5, ci_low=-0.6, ci_high=-0.4),  # Inconsistent
    ]

    # Act
    result = calculate_omega(cells, num_items=3)

    # Assert: Should handle gracefully with omega_total=None and flag="calculation_failed"
    # (or return valid omega if reliabiliPy handles it)
    assert "omega_total" in result
    assert "internal_consistency_flag" in result
    # Either calculation succeeds or fails gracefully
    if result["omega_total"] is None:
        assert result["internal_consistency_flag"] == "calculation_failed"
