import os
import pytest
from pydantic import ValidationError

os.environ["APP_MODE"] = "mock"

# This import will FAIL initially (schemas don't exist yet)
from backend.evaluation.schemas import ComparisonResult, ComparisonDimension, BenchmarkScale


def test_comparison_dimension_validates_score_range():
    """Score must be 1-10."""
    # Valid
    dim = ComparisonDimension(dimension="quality", score=8.5, reasoning="Good clarity and precision")
    assert dim.score == 8.5

    # Invalid: too low
    with pytest.raises(ValidationError):
        ComparisonDimension(dimension="quality", score=0.5, reasoning="Too low")

    # Invalid: too high
    with pytest.raises(ValidationError):
        ComparisonDimension(dimension="quality", score=11.0, reasoning="Too high")


def test_comparison_dimension_requires_reasoning():
    """Reasoning must be non-empty (min_length enforced)."""
    with pytest.raises(ValidationError):
        ComparisonDimension(dimension="quality", score=8.0, reasoning="")


def test_benchmark_scale_validates_items():
    """Scale must have at least one item."""
    with pytest.raises(ValidationError):
        BenchmarkScale(name="Test", author="Doe", year=2020, domain="personality", items=[])


def test_comparison_result_structure():
    """ComparisonResult must have all 4 dimensions and overall score."""
    # Valid result
    result = ComparisonResult(
        quality_parity=ComparisonDimension(
            dimension="quality_parity",
            score=8.0,
            reasoning="Both items are clear and professionally written"
        ),
        construct_fidelity=ComparisonDimension(
            dimension="construct_fidelity",
            score=7.5,
            reasoning="Both measure the same construct"
        ),
        stylistic_similarity=ComparisonDimension(
            dimension="stylistic_similarity",
            score=6.0,
            reasoning="Similar tone and format"
        ),
        psychometric_properties=ComparisonDimension(
            dimension="psychometric_properties",
            score=7.0,
            reasoning="Comparable difficulty and discrimination"
        ),
        overall_score=7.125  # Average of 8.0, 7.5, 6.0, 7.0
    )
    assert result.overall_score == 7.125
    assert result.quality_parity.score == 8.0
