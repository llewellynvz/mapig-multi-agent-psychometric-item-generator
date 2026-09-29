"""Regression tests for code-review fixes in the graph, API and statistics."""

import json
import math

import numpy as np

from backend import main
from backend.analytics.classical_stats import bartlett_sphericity, efa_omega
from backend.graph import _enforce_facet_floor
from backend.schemas import DraftItem


def _item(text: str, facet: str) -> DraftItem:
    return DraftItem(
        item_text=f"{text} item",
        construct_name="Test Construct",
        rationale="Targets the assigned facet.",
        facet_name=facet,
    )


def test_facet_floor_restores_facet_that_dedup_emptied():
    # Facet B's two items were both dropped; B is absent from ``kept``.
    original = [_item(f"A{n}", "A") for n in range(3)] + [_item(f"B{n}", "B") for n in range(2)]
    dropped = [3, 4]
    kept = original[:3]

    final, still_dropped, warnings = _enforce_facet_floor(kept, original, dropped, min_per_facet=3)

    assert [it.facet_name for it in final].count("B") == 2
    assert still_dropped == []
    assert len(warnings) == 1 and "'B'" in warnings[0]


def test_json_safe_replaces_non_finite_floats():
    payload = {"a": float("nan"), "b": [1.0, float("inf")], "c": {"d": -float("inf")}, "e": "x"}

    safe = main._json_safe(payload)

    assert safe == {"a": None, "b": [1.0, None], "c": {"d": None}, "e": "x"}
    json.dumps(safe, allow_nan=False)


def test_bartlett_and_omega_not_estimable_when_n_not_above_k():
    rng = np.random.default_rng(0)
    data = rng.standard_normal((6, 20))
    corr = np.corrcoef(data, rowvar=False)

    assert bartlett_sphericity(corr, n=6) == (None, None)
    assert efa_omega(data, n_factors=1) is None


def test_synthetic_pilot_reverse_scores_before_alpha(monkeypatch):
    from backend.agents import synthetic_respondents as sr
    from backend.schemas import UserRequest

    rng = np.random.default_rng(1)
    trait = rng.integers(1, 6, size=50)
    reverse = {4, 5}
    # Respondents answer as worded: reverse-keyed items mirror the trait.
    raw = np.array(
        [[(6 - t) if i in reverse else t for i in range(6)] for t in trait], dtype=float
    )
    monkeypatch.setattr(sr, "_collect_matrix", lambda *a, **k: (raw.copy(), 0, sr.TokenUsage()))

    items = [
        DraftItem(
            item_text=f"Item number {i}",
            construct_name="Trait",
            rationale="Targets the trait.",
            polarity="-" if i in reverse else "+",
        )
        for i in range(6)
    ]
    request = UserRequest(
        construct_name="Trait",
        construct_definition="A single test trait for the pilot.",
        target_population="adults",
        response_scale="5-point Likert",
    )

    result, _ = sr.run_synthetic_pilot(request, items, facet_names=["Trait"])

    assert result is not None
    assert result.cronbach_alpha is not None and math.isclose(result.cronbach_alpha, 1.0)
