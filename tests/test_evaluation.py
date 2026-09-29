"""Tests for the evaluation path (/v1/run-evaluation and backend/evaluation)."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.evaluation import eval_suite, item_comparison
from backend.evaluation.baseline_runner import BaselineComparison, _get_baseline_metrics
from backend.evaluation.metrics_aggregator import EvaluationMetrics, aggregate_comparison_results
from backend.evaluation.schemas import ComparisonDimension, ComparisonResult
from backend.settings import settings


def _dim(name: str, score: float) -> ComparisonDimension:
    return ComparisonDimension(dimension=name, score=score, reasoning="Reasoning text for tests.")


def _result(qp=8.0, cf=7.0, ss=6.0, pp=5.0, overall=None) -> ComparisonResult:
    kwargs = dict(
        quality_parity=_dim("quality_parity", qp),
        construct_fidelity=_dim("construct_fidelity", cf),
        stylistic_similarity=_dim("stylistic_similarity", ss),
        psychometric_properties=_dim("psychometric_properties", pp),
    )
    if overall is not None:
        kwargs["overall_score"] = overall
    return ComparisonResult(**kwargs)


def _metrics(score=8.0, failed=None) -> EvaluationMetrics:
    return EvaluationMetrics(score, score, score, score, total_comparisons=5, failed_scales=failed)


# --- schemas: overall_score is recomputed, never rejected --------------------

def test_inconsistent_overall_score_is_recomputed_not_rejected():
    result = _result(8.0, 7.0, 6.0, 5.0, overall=9.9)
    assert result.overall_score == pytest.approx(6.5)


def test_missing_overall_score_is_filled_from_dimensions():
    assert _result(8.0, 8.0, 6.0, 6.0).overall_score == pytest.approx(7.0)


# --- metrics: dimensions reported under their own names ---------------------

def test_aggregate_reports_truthful_dimension_names():
    metrics = aggregate_comparison_results([_result(8, 7, 6, 5), _result(6, 5, 4, 3)])
    assert metrics.dimension_scores() == {
        "quality_parity_score": 7.0,
        "construct_fidelity_score": 6.0,
        "stylistic_similarity_score": 5.0,
        "psychometric_properties_score": 4.0,
    }
    assert metrics.overall_score == pytest.approx(5.5)
    assert not hasattr(metrics, "workflow_efficiency_score")
    assert not hasattr(metrics, "agent_performance_score")


# --- baseline honesty -------------------------------------------------------

def test_synthetic_baseline_leaves_success_undetermined():
    comparison = BaselineComparison(_metrics(8.0), _get_baseline_metrics(), baseline_source="synthetic")
    assert comparison.improvement_basis == "synthetic_reference"
    assert comparison.meets_improvement_threshold is True
    assert comparison.all_dimensions_passing is True
    assert comparison.success is None
    assert "synthetic" in comparison.success_reason
    assert _get_baseline_metrics().total_comparisons == 0


def test_measured_baseline_decides_success():
    comparison = BaselineComparison(_metrics(8.0), _metrics(6.0), baseline_source="measured")
    assert comparison.improvement_basis == "measured_baseline"
    assert comparison.success is True
    assert comparison.success_reason is None


def test_failed_scales_mean_no_success_even_with_measured_baseline():
    failed = [{"name": "PHQ-9", "domain": "clinical", "error": "boom"}]
    comparison = BaselineComparison(_metrics(8.0, failed), _metrics(6.0), baseline_source="measured")
    assert comparison.success is False
    assert "PHQ-9" in comparison.success_reason


# --- pairing ----------------------------------------------------------------

def test_pairing_picks_most_similar_published_item_in_mock_mode(monkeypatch):
    monkeypatch.setattr(settings, "APP_MODE", "mock")
    generated = ["I often feel down and hopeless", "I start conversations easily with people"]
    published = ["I start conversations.", "Feeling down, depressed, or hopeless", "unrelated words"]
    pairs, method = asyncio.run(eval_suite.pair_with_most_similar(generated, published))
    assert pairs == [1, 0]
    assert method == eval_suite.PAIRING_LEXICAL


def test_pairing_ties_are_deterministic(monkeypatch):
    monkeypatch.setattr(settings, "APP_MODE", "mock")
    pairs, _ = asyncio.run(eval_suite.pair_with_most_similar(["zzz"], ["a", "b", "c"]))
    assert pairs == [0]


# --- provider validation ----------------------------------------------------

def test_invalid_provider_is_rejected_not_replaced():
    with pytest.raises(ValueError, match="model_provider"):
        asyncio.run(eval_suite.run_evaluation_suite("gemini"))


# --- async judge calls ------------------------------------------------------

def test_live_comparison_uses_ainvoke(monkeypatch):
    calls = []

    class FakeRunnable:
        def invoke(self, messages):  # pragma: no cover - must not be called
            raise AssertionError("synchronous invoke blocks the event loop")

        async def ainvoke(self, messages):
            calls.append(messages)
            return {"parsed": _result(8, 8, 8, 8, overall=1.0), "raw": None}

    class FakeModel:
        def with_structured_output(self, *args, **kwargs):
            return FakeRunnable()

    monkeypatch.setattr(settings, "APP_MODE", "claude")
    monkeypatch.setattr(item_comparison, "get_chat_model_for_agent", lambda **kw: FakeModel())
    monkeypatch.setattr(item_comparison, "load_prompt", lambda name: "system prompt")

    result = asyncio.run(item_comparison.compare_to_published_item("gen", "pub", "Construct"))
    assert len(calls) == 2  # both orderings
    assert result.overall_score == pytest.approx(8.0)


# --- endpoint ---------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "APP_MODE", "mock")
    monkeypatch.setattr(settings, "MAPIG_API_KEY", None)
    return TestClient(main.app)


def test_endpoint_reports_synthetic_basis_and_truthful_keys(client):
    response = client.post("/v1/run-evaluation?model_provider=claude")
    assert response.status_code == 200
    body = response.json()

    assert body["baseline_source"] == "synthetic"
    assert body["improvement_basis"] == "synthetic_reference"
    assert body["failed_scales"] == []
    assert len(body["evaluated_scales"]) == 5
    assert body["pairing_method"] == eval_suite.PAIRING_LEXICAL
    assert set(body["current"]) == {
        "quality_parity_score", "construct_fidelity_score", "stylistic_similarity_score",
        "psychometric_properties_score", "overall_score", "total_comparisons",
    }
    assert "stylistic_similarity_improvement" in body["improvement"]
    assert body["success_criteria"]["success"] is None
    assert body["success_criteria"]["success_reason"]


def test_endpoint_reports_failed_scales_and_no_success(client, monkeypatch):
    real_compare = eval_suite.compare_to_published_item

    async def flaky_compare(**kwargs):
        if kwargs["construct_name"] == "PHQ-9":
            raise RuntimeError("judge exploded")
        return await real_compare(**kwargs)

    monkeypatch.setattr(eval_suite, "compare_to_published_item", flaky_compare)

    body = client.post("/v1/run-evaluation?model_provider=claude").json()
    assert [f["name"] for f in body["failed_scales"]] == ["PHQ-9"]
    assert "judge exploded" in body["failed_scales"][0]["error"]
    assert "PHQ-9" not in body["evaluated_scales"]
    assert body["current"]["total_comparisons"] == 20
    assert body["success_criteria"]["success"] is False
    assert "PHQ-9" in body["success_criteria"]["success_reason"]


def test_endpoint_rejects_unknown_provider(client):
    assert client.post("/v1/run-evaluation?model_provider=gemini").status_code == 422
