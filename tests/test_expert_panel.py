"""Unit tests for expert panel (Phase 15).

Tests use APP_MODE=mock to avoid real API calls. Schema validation,
IRR computation, and consensus synthesis are tested deterministically.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from backend.agents.expert_panel import (
    _build_rating_matrix,
    _dissent_flags,
    run_expert_panel,
    synthesize_consensus,
)
from backend.analytics.krippendorff import (
    cohens_kappa,
    krippendorff_alpha,
    pairwise_kappa_matrix,
)
from backend.schemas import (
    DraftItem,
    ExpertEvaluation,
    UserRequest,
)


def _make_request() -> UserRequest:
    return UserRequest(
        construct_name="Test Construct",
        construct_definition="An operational definition for testing.",
        target_population="adults",
        response_scale="5-point Likert",
        item_count=4,
        model_provider="openai",
    )


def _make_items(n: int = 4) -> list[DraftItem]:
    return [
        DraftItem(
            item_text=f"I have feeling number {i}.",
            construct_name="Test Construct",
            rationale="synthetic test rationale",
            facet_name="A",
        )
        for i in range(n)
    ]


# ----- Krippendorff α tests -----


def test_krippendorff_perfect_agreement():
    ratings = np.array([[1.0, 2, 3, 4, 5], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5]])
    alpha = krippendorff_alpha(ratings, level="ordinal")
    assert alpha >= 0.99


def test_krippendorff_random_agreement_low():
    rng = np.random.default_rng(42)
    ratings = rng.integers(1, 6, size=(3, 20)).astype(float)
    alpha = krippendorff_alpha(ratings, level="ordinal")
    # Random ratings → α near 0 or below
    assert alpha < 0.4


def test_krippendorff_returns_nan_with_too_few_items():
    ratings = np.array([[1.0]])
    assert np.isnan(krippendorff_alpha(ratings))


def test_krippendorff_handles_missing_data():
    ratings = np.array(
        [[1.0, 2, np.nan, 4], [1, 2, 3, 4], [np.nan, 2, 3, 4]]
    )
    alpha = krippendorff_alpha(ratings)
    assert -1 <= alpha <= 1


def test_cohens_kappa_perfect_agreement():
    a = np.array([1, 2, 3, 4, 5], dtype=float)
    b = np.array([1, 2, 3, 4, 5], dtype=float)
    assert cohens_kappa(a, b) == 1.0


def test_cohens_kappa_disagreement_negative():
    a = np.array([1, 1, 1, 5, 5, 5], dtype=float)
    b = np.array([5, 5, 5, 1, 1, 1], dtype=float)
    k = cohens_kappa(a, b, weighted=True)
    assert k < 0.0


def test_pairwise_kappa_matrix_returns_dict():
    ratings = np.array([[1.0, 2, 3], [1, 2, 3], [3, 2, 1]])
    out = pairwise_kappa_matrix(ratings, ["a", "b", "c"])
    assert "a|b" in out
    assert "b|c" in out
    assert "a|c" in out


# ----- Aggregation helpers -----


def test_build_rating_matrix_basic():
    evals = [
        ExpertEvaluation(
            expert_role="psychometric",
            expert_label="Psychometric",
            item_scores={0: 5, 1: 4, 2: 3},
            overall_verdict="accept",
        ),
        ExpertEvaluation(
            expert_role="domain",
            expert_label="Domain",
            item_scores={0: 4, 1: 5, 2: 4},
            overall_verdict="accept",
        ),
    ]
    matrix, labels = _build_rating_matrix(evals, n_items=3)
    assert matrix.shape == (2, 3)
    assert labels == ["psychometric", "domain"]
    assert matrix[0, 0] == 5.0
    assert matrix[1, 2] == 4.0


def test_dissent_flags_high_sd_items():
    matrix = np.array([[5.0, 5.0, 1.0], [5.0, 5.0, 5.0], [5.0, 5.0, 1.0]])
    flags = _dissent_flags(matrix, sd_threshold=1.0)
    assert 2 in flags
    assert 0 not in flags


# ----- Consensus synthesis -----


def test_synthesize_consensus_unanimous_accept_emits_no_revision():
    items = _make_items(4)
    evals = [
        ExpertEvaluation(
            expert_role="psychometric",
            expert_label="Psychometric",
            item_scores={i: 5 for i in range(4)},
            overall_verdict="accept",
        ),
        ExpertEvaluation(
            expert_role="domain",
            expert_label="Domain",
            item_scores={i: 5 for i in range(4)},
            overall_verdict="accept",
        ),
    ]
    plan = synthesize_consensus(evals, items)
    assert plan.edits == []


def test_synthesize_consensus_critical_score_emits_revision():
    items = _make_items(2)
    evals = [
        ExpertEvaluation(
            expert_role="psychometric",
            expert_label="Psychometric",
            item_scores={0: 5, 1: 1},
            item_comments={1: "Item is unacceptable"},
            overall_verdict="revise",
        ),
        ExpertEvaluation(
            expert_role="domain",
            expert_label="Domain",
            item_scores={0: 4, 1: 3},
            overall_verdict="revise",
        ),
    ]
    plan = synthesize_consensus(evals, items)
    item_indices = [e.item_index for e in plan.edits]
    assert 1 in item_indices  # critical score → revision required


def test_synthesize_consensus_two_concerns_emit_revision():
    items = _make_items(2)
    evals = [
        ExpertEvaluation(
            expert_role="psychometric",
            expert_label="Psychometric",
            item_scores={0: 5, 1: 3},
            item_comments={1: "Concern A"},
            overall_verdict="revise",
        ),
        ExpertEvaluation(
            expert_role="domain",
            expert_label="Domain",
            item_scores={0: 5, 1: 3},
            item_comments={1: "Concern B"},
            overall_verdict="revise",
        ),
    ]
    plan = synthesize_consensus(evals, items)
    assert any(e.item_index == 1 for e in plan.edits)


# ----- Mock-mode end-to-end -----


def test_run_expert_panel_in_mock_mode(monkeypatch):
    monkeypatch.setattr("backend.settings.settings.APP_MODE", "mock")
    request = _make_request()
    items = _make_items(3)

    consensus, _usage = run_expert_panel(
        request=request,
        items=items,
        evidence=[],
        pfa_result=None,
    )

    # In mock mode, all 3 experts return deterministic scores
    assert len(consensus.evaluations) == 3
    roles = [e.expert_role for e in consensus.evaluations]
    assert "psychometric" in roles
    assert "domain" in roles
    assert "localization" in roles

    # IRR should be computable
    if consensus.irr_alpha is not None:
        assert -1.0 <= consensus.irr_alpha <= 1.0


def test_run_expert_panel_disabled(monkeypatch):
    monkeypatch.setattr("backend.settings.settings.EXPERT_PANEL_ENABLED", False)
    request = _make_request()
    items = _make_items(3)
    consensus, _usage = run_expert_panel(
        request=request,
        items=items,
        evidence=[],
        pfa_result=None,
    )
    assert consensus.evaluations == []
    assert "disabled" in consensus.consensus_revisions.summary.lower()
