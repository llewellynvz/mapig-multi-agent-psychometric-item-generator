import os
import pytest

os.environ["APP_MODE"] = "mock"

from backend.evaluation.metrics_aggregator import aggregate_comparison_results, EvaluationMetrics
from backend.evaluation.schemas import ComparisonResult, ComparisonDimension

def _sample_comparison(overall: float) -> ComparisonResult:
    """Helper to create sample comparison result."""
    return ComparisonResult(
        quality_parity=ComparisonDimension(dimension="quality_parity", score=overall, reasoning="Test reasoning for quality parity"),
        construct_fidelity=ComparisonDimension(dimension="construct_fidelity", score=overall, reasoning="Test reasoning for construct fidelity"),
        stylistic_similarity=ComparisonDimension(dimension="stylistic_similarity", score=overall, reasoning="Test reasoning for stylistic similarity"),
        psychometric_properties=ComparisonDimension(dimension="psychometric_properties", score=overall, reasoning="Test reasoning for psychometric properties"),
        overall_score=overall
    )

def test_aggregate_25_comparisons():
    """Aggregating 25 comparisons produces 4 dimension scores."""
    comparisons = [_sample_comparison(8.0) for _ in range(25)]

    metrics = aggregate_comparison_results(comparisons)

    assert metrics.total_comparisons == 25
    assert 1.0 <= metrics.item_quality_score <= 10.0
    assert 1.0 <= metrics.agent_performance_score <= 10.0
    assert 1.0 <= metrics.workflow_efficiency_score <= 10.0
    assert 1.0 <= metrics.construct_validity_score <= 10.0
    assert 1.0 <= metrics.overall_score <= 10.0

def test_aggregate_empty_list_raises_error():
    """Empty comparison list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot aggregate empty"):
        aggregate_comparison_results([])

def test_eval_suite_runs_in_mock_mode():
    """Evaluation suite completes in mock mode (APP_MODE=mock is set at top of file)."""
    from backend.evaluation.eval_suite import run_evaluation_suite

    # APP_MODE=mock is set at module level, so agents will use mock responses
    metrics = run_evaluation_suite(model_provider="claude")

    assert isinstance(metrics, EvaluationMetrics)
    assert metrics.total_comparisons > 0
    assert 1.0 <= metrics.overall_score <= 10.0
