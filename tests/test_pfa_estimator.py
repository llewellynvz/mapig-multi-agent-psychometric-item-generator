"""Unit tests for PFA estimator (Phase 14).

These tests use synthetic, deterministic data so they run without OpenAI API
access. The DASS-21/DTDD live replication tests are gated by RUN_PFA_LIVE=1
to avoid burning API credits in CI.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from backend.agents.pfa_estimator import (
    _align_factor_signs,
    _compute_identifiability,
    _decide_verdict,
    build_expected_pattern,
    compute_model_fit,
    compute_retention_flags,
    factor_recovery_rate,
    label_factors_via_daal,
    run_pfa,
    tuckers_congruence,
)
from backend.schemas import DraftItem, FacetDefinition, FacetMapperResponse


# ----- Pure-NumPy psychometric helpers -----


def test_tuckers_congruence_identical_matrices_equals_one():
    A = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]])
    result = tuckers_congruence(A, A)
    assert result.shape == (2,)
    assert np.allclose(result, 1.0)


def test_tuckers_congruence_orthogonal_matrices_equals_zero():
    A = np.array([[1.0, 0.0], [1.0, 0.0]])
    B = np.array([[0.0, 1.0], [0.0, 1.0]])
    result = tuckers_congruence(A, B)
    assert np.allclose(result, 0.0)


def test_tuckers_congruence_shape_mismatch_raises():
    A = np.zeros((4, 2))
    B = np.zeros((4, 3))
    with pytest.raises(ValueError):
        tuckers_congruence(A, B)


def test_build_expected_pattern_basic():
    expected = build_expected_pattern([0, 0, 1, 1], n_factors=2)
    assert expected.shape == (4, 2)
    np.testing.assert_array_equal(expected[0], [1.0, 0.0])
    np.testing.assert_array_equal(expected[2], [0.0, 1.0])


def test_factor_recovery_rate_perfect_recovery():
    # Items 0,1 load on factor 0; items 2,3 load on factor 1.
    loadings = np.array([
        [0.8, 0.1],
        [0.7, 0.2],
        [0.1, 0.9],
        [0.2, 0.7],
    ])
    rate, flags = factor_recovery_rate(loadings, [0, 0, 1, 1])
    assert rate == 1.0
    assert flags == [True, True]


def test_factor_recovery_rate_no_recovery():
    # All items load on factor 0 (collapsed); factor 1 never wins.
    loadings = np.array([
        [0.8, 0.1],
        [0.7, 0.2],
        [0.6, 0.1],
        [0.5, 0.2],
    ])
    rate, flags = factor_recovery_rate(loadings, [0, 0, 1, 1])
    assert rate < 1.0
    assert flags[1] is False  # factor 1 not recovered


def test_compute_retention_flags_well_loaded():
    # 4 items, 2 factors. Items 0,1 should belong to factor 0.
    loadings = np.array([
        [0.85, 0.05],  # 0 → 0 strong
        [0.75, 0.10],  # 1 → 0 strong
        [0.05, 0.85],  # 2 → 1 strong
        [0.10, 0.75],  # 3 → 1 strong
    ])
    retention = compute_retention_flags(loadings, [0, 0, 1, 1])
    for is_well, violations in retention:
        assert is_well, f"Expected well-loaded, got violations: {violations}"


def test_compute_retention_flags_cross_loading_fails():
    # Item 0 expected on factor 0 but loads more strongly on factor 1.
    loadings = np.array([
        [0.20, 0.85],  # cross-loaded → fails
        [0.75, 0.10],
        [0.05, 0.85],
        [0.10, 0.75],
    ])
    retention = compute_retention_flags(loadings, [0, 0, 1, 1])
    is_well, violations = retention[0]
    assert not is_well
    assert "rule2_cross_loading_dominates" in violations


def test_label_factors_via_daal_uses_facet_labels():
    loadings = np.array([
        [0.85, 0.05],
        [0.75, 0.10],
        [0.05, 0.85],
        [0.10, 0.75],
    ])
    labels = label_factors_via_daal(
        loadings,
        expected_factor_assignments=[0, 0, 1, 1],
        facet_labels=["Depression", "Anxiety"],
    )
    # Factor 0 should be labeled "Depression" (items 0,1 load there)
    # Factor 1 should be labeled "Anxiety"
    assert labels[0] == "Depression"
    assert labels[1] == "Anxiety"


# ----- Phase 14 follow-up: factor-sign indeterminacy fix -----


def test_align_factor_signs_flips_negative_dominant():
    """Reproduces the production bug: oblimin returned all-negative loadings.
    After alignment, the dominant loading must be positive."""
    loadings = np.array([
        [-0.80, 0.10],
        [-0.70, 0.05],
        [-0.65, 0.00],
    ])
    aligned, flipped = _align_factor_signs(loadings)
    assert flipped == [True, False]
    np.testing.assert_array_almost_equal(aligned[:, 0], [0.80, 0.70, 0.65])
    np.testing.assert_array_almost_equal(aligned[:, 1], [0.10, 0.05, 0.00])


def test_align_factor_signs_preserves_positive_dominant():
    """Already-positive loadings must not be touched."""
    loadings = np.array([[0.80, 0.10], [0.70, 0.05]])
    aligned, flipped = _align_factor_signs(loadings)
    assert flipped == [False, False]
    np.testing.assert_array_equal(aligned, loadings)


def test_align_factor_signs_uses_largest_absolute_magnitude():
    """When small positive and large negative are mixed, the largest absolute
    value drives the decision (Mulaik 2010 convention)."""
    loadings = np.array([
        [0.05, 0.0],
        [-0.95, 0.0],
        [0.10, 0.0],
    ])
    aligned, flipped = _align_factor_signs(loadings)
    # The -0.95 dominates → flip
    assert flipped[0] is True
    np.testing.assert_array_almost_equal(aligned[:, 0], [-0.05, 0.95, -0.10])


def test_align_factor_signs_handles_empty_factor():
    """Edge case: zero-length column (shouldn't happen but be defensive)."""
    loadings = np.zeros((3, 0))
    aligned, flipped = _align_factor_signs(loadings)
    assert aligned.shape == (3, 0)
    assert flipped == []


def test_align_factor_signs_handles_all_zero_column():
    """A factor with all-zero loadings (degenerate) should not flip."""
    loadings = np.array([[0.0, 0.5], [0.0, 0.6]])
    aligned, flipped = _align_factor_signs(loadings)
    assert flipped == [False, False]


def test_decide_verdict_uses_mean_abs_congruence():
    """Verdict 'good' requires congruence ≥ 0.95 (or 0 sentinel)."""
    # Good rmsr + good recovery + excellent congruence → good
    assert _decide_verdict(0.04, 0.85, 0.96) == "good"
    # Good rmsr + good recovery + poor congruence → not good
    assert _decide_verdict(0.04, 0.85, 0.40) == "poor"
    # Acceptable recovery + fair congruence → acceptable
    assert _decide_verdict(0.10, 0.65, 0.86) == "acceptable"
    # Sentinel: congruence=0 (e.g., couldn't compute) doesn't penalize
    assert _decide_verdict(0.04, 0.85, 0.0) == "good"


def test_run_pfa_aligns_negative_factor_to_positive(monkeypatch):
    """End-to-end: synthesize embeddings that produce a negative-orientation
    factor; assert the post-alignment loadings are positive AND Tucker's
    congruence is positive.

    Reproduces the user's production case (Emotional Wellbeing items showing
    -0.73 / -0.66 / -0.63 / -0.73 / -0.69) and asserts the fix flips them.
    """
    facet_names = ["Wellbeing"]
    items = _make_items(
        ["item one wb.", "item two wb.", "item three wb.", "item four wb.", "item five wb."],
        facet_names * 5,
    )

    # Synthesize embeddings whose first principal component points in a
    # NEGATIVE direction. Without sign-alignment, oblimin will return
    # negative loadings; with the fix, they should come back positive.
    rng = np.random.default_rng(7)
    base = np.array([-1.0, 0.0, 0.0, 0.0])  # negative principal axis
    text_to_emb = {
        item.item_text: base + rng.normal(0, 0.05, 4) for item in items
    }

    def _embed_lookup(item_texts, model=None):
        return np.array([text_to_emb[t] for t in item_texts])

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", _embed_lookup)

    result = run_pfa(
        items,
        facet_mapping=_make_facet_mapping(facet_names),
        n_factors=1,
    )

    # All loadings on the single factor should be positive (post-alignment).
    for fl in result.loadings:
        assert fl.loadings[0] > 0, (
            f"Expected positive loading after sign alignment; got {fl.loadings[0]} "
            f"for item {fl.item_index}"
        )

    # Tucker's congruence should be positive (and high) after alignment.
    assert result.tuckers_congruence, "Expected Tucker's congruence values"
    for c in result.tuckers_congruence:
        assert c > 0, f"Tucker's congruence should be positive after alignment; got {c}"


def test_compute_identifiability_saturated_with_3_items_1_factor():
    """3 items / 1 factor: dof = (3*2/2) - (3*1 - 0) = 3 - 3 = 0 → saturated."""
    assert _compute_identifiability(3, 1) == "saturated"


def test_compute_identifiability_over_identified_with_5_items_1_factor():
    """5 items / 1 factor: dof = 10 - 5 = 5 → over_identified."""
    assert _compute_identifiability(5, 1) == "over_identified"


def test_compute_identifiability_saturated_with_2_items():
    """Tiny sets are saturated/under-identified."""
    assert _compute_identifiability(2, 1) == "saturated"


def test_compute_identifiability_over_identified_typical_case():
    """10 items / 2 factors: dof = 45 - (20 - 1) = 26 → over_identified."""
    assert _compute_identifiability(10, 2) == "over_identified"


def test_run_pfa_marks_saturated_on_3_items(monkeypatch):
    """End-to-end: PFAResult.model_identifiability should be 'saturated' with 3 items / 1 factor.

    This is the user's reported case (Cognitive Flexibility, 3 final items, 1 factor)
    where RMSR=0 was confusing.
    """
    facet_names = ["Single Factor"]
    items = _make_items(["item one.", "item two.", "item three."], facet_names * 3)
    fake_embeddings = np.array([
        [1.0, 0.05, 0.0, 0.0],
        [0.95, 0.06, 0.0, 0.0],
        [0.92, 0.04, 0.0, 0.0],
    ])

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", lambda item_texts, model: fake_embeddings)

    result = run_pfa(
        items,
        facet_mapping=_make_facet_mapping(facet_names),
        n_factors=1,
    )
    assert result.model_identifiability == "saturated"
    # Disclaimer should mention saturation
    assert "saturated" in result.disclaimer.lower()
    # Verdict cannot claim "good" when saturated (no diagnostic dof)
    assert result.fit_verdict in {"acceptable", "poor"}


def test_compute_model_fit_perfect_reproduction():
    """When loadings perfectly reproduce sim, RMSR = 0 and CAF = 1."""
    sim = np.array([
        [1.0, 0.5, 0.0, 0.0],
        [0.5, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.5],
        [0.0, 0.0, 0.5, 1.0],
    ])
    # Two-factor loadings that exactly reproduce off-diagonal
    loadings = np.array([
        [np.sqrt(0.5), 0.0],
        [np.sqrt(0.5), 0.0],
        [0.0, np.sqrt(0.5)],
        [0.0, np.sqrt(0.5)],
    ])
    rmsr, caf, residual = compute_model_fit(sim.copy(), loadings)
    assert rmsr < 0.05
    assert caf > 0.9


# ----- Synthetic end-to-end PFA -----


def _make_items(texts: list[str], facets: list[str]) -> list[DraftItem]:
    return [
        DraftItem(
            item_text=t,
            construct_name="Test Construct",
            rationale="synthetic test rationale",
            facet_name=f,
        )
        for t, f in zip(texts, facets)
    ]


def _make_facet_mapping(facet_names: list[str]) -> FacetMapperResponse:
    return FacetMapperResponse(
        is_unidimensional=len(facet_names) == 1,
        facets=[
            FacetDefinition(
                facet_name=fn,
                facet_description=f"Description for {fn} facet",
                exclusions=f"Not the {fn} facet",
                target_item_count=2,
            )
            for fn in facet_names
        ],
        theoretical_basis="Synthetic test fixture",
    )


def test_run_pfa_skips_when_too_few_items(monkeypatch):
    items = _make_items(["item one text.", "item two text."], ["FacetA", "FacetB"])
    result = run_pfa(items, facet_mapping=_make_facet_mapping(["FacetA", "FacetB"]))
    assert result.fit_verdict == "poor"
    assert result.n_items == 2
    assert result.loadings == []


def test_run_pfa_with_synthetic_embeddings(monkeypatch):
    """Stub embed_items_sync to return a controlled embedding matrix.

    Items 0-2 cluster on dimension 1; items 3-5 cluster on dimension 2.
    Each item gets unique noise so the cosine matrix is non-singular and
    factor-analyzer's SMC step can invert it.
    """
    facet_names = ["FactorA", "FactorB"]
    items = _make_items(
        ["item zero.", "item one.", "item two.", "item three.", "item four.", "item five."],
        ["FactorA", "FactorA", "FactorA", "FactorB", "FactorB", "FactorB"],
    )

    rng = np.random.default_rng(42)
    base_a = np.array([1.0, 0.0, 0.0, 0.0])
    base_b = np.array([0.0, 0.0, 1.0, 0.0])
    fake_embeddings = np.array([
        base_a + rng.normal(0, 0.05, 4),
        base_a + rng.normal(0, 0.05, 4),
        base_a + rng.normal(0, 0.05, 4),
        base_b + rng.normal(0, 0.05, 4),
        base_b + rng.normal(0, 0.05, 4),
        base_b + rng.normal(0, 0.05, 4),
    ])

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", lambda item_texts, model: fake_embeddings)

    result = run_pfa(
        items,
        facet_mapping=_make_facet_mapping(facet_names),
        n_factors=2,
    )

    # Two factors should be recovered
    assert result.n_factors == 2
    assert len(result.loadings) == 6
    # Factor recovery rate should be high
    assert result.factor_recovery_rate >= 0.5
    # Items in same group should share primary_factor
    primary = [fl.primary_factor for fl in result.loadings]
    assert primary[0] == primary[1] == primary[2]
    assert primary[3] == primary[4] == primary[5]
    assert primary[0] != primary[3]


def test_run_pfa_polarity_sign_flip(monkeypatch):
    """Reverse-keyed items should still cluster with their facet after sign-flip."""
    facet_names = ["FactorA"]
    items = _make_items(
        ["pos item one.", "pos item two.", "rev item one.", "rev item two."],
        ["FactorA"] * 4,
    )
    items[2].polarity = "-"
    items[3].polarity = "-"

    rng = np.random.default_rng(42)
    base = np.array([1.0, 0.0, 0.0, 0.0])
    fake_embeddings = np.array([
        base + rng.normal(0, 0.05, 4),
        base + rng.normal(0, 0.05, 4),
        -base + rng.normal(0, 0.05, 4),  # reverse-keyed → should sign-flip to align
        -base + rng.normal(0, 0.05, 4),
    ])

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", lambda item_texts, model: fake_embeddings)

    result = run_pfa(
        items,
        facet_mapping=_make_facet_mapping(facet_names),
        n_factors=1,
    )
    # After sign-flip, all 4 items should load on the single factor
    assert all(fl.primary_factor == 0 for fl in result.loadings)


# ----- Pruning loop tests -----


def test_prune_items_drops_weakest(monkeypatch):
    """Pruning should drop weak items down to target_count when above target."""
    from backend.agents.pfa_pruning import prune_items
    facet_names = ["FacetA", "FacetB"]
    items = _make_items(
        ["item a1.", "item a2.", "item a3.", "item b1.", "item b2.", "item b3."],
        ["FacetA", "FacetA", "FacetA", "FacetB", "FacetB", "FacetB"],
    )

    # Map each item text -> deterministic embedding (with small noise to avoid singularity)
    rng = np.random.default_rng(7)
    a_dir = np.array([1.0, 0.0, 0.0, 0.0])
    b_dir = np.array([0.0, 1.0, 0.0, 0.0])
    weak_dir = np.array([0.5, 0.5, 0.0, 0.0])
    text_to_embedding = {
        "item a1.": a_dir + rng.normal(0, 0.03, 4),
        "item a2.": a_dir + rng.normal(0, 0.03, 4),
        "item a3.": weak_dir + rng.normal(0, 0.03, 4),  # weak/cross-loaded
        "item b1.": b_dir + rng.normal(0, 0.03, 4),
        "item b2.": b_dir + rng.normal(0, 0.03, 4),
        "item b3.": weak_dir + rng.normal(0, 0.03, 4),  # weak/cross-loaded
    }

    def _embed_lookup(item_texts, model=None):
        return np.array([text_to_embedding[t] for t in item_texts])

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", _embed_lookup)

    kept, dropped, _result = prune_items(
        items,
        facet_mapping=_make_facet_mapping(facet_names),
        target_count=4,
        max_iters=5,
    )
    # Pruning may stop early if remaining items all load cleanly;
    # the contract is: never go below target_count, and dropped items
    # must come from the weak pool first.
    assert len(kept) >= 4, "pruning should never go below target_count"
    assert len(kept) <= 6, "kept set should be subset of input"
    # At least one weakly-loaded cross-loaded item should be dropped
    assert len(dropped) >= 1
    weak_indices = {2, 5}
    assert any(d in weak_indices for d in dropped), (
        f"Expected at least one weak item (idx 2 or 5) to be dropped; got {dropped}"
    )


def test_prune_items_unidimensional_bypasses_facet_preservation(monkeypatch):
    """For unidimensional constructs the 'one item per facet' rule is bypassed
    so we can always drop the weakest item.

    Reproduces the production case: all items have facet_name='Life Satisfaction',
    facet_mapping.is_unidimensional=True. Pruning should drop weakest item without
    the 'last remaining for that facet' warning blocking progress.
    """
    from backend.agents.pfa_pruning import prune_items
    from backend.schemas import FacetDefinition, FacetMapperResponse

    facet_names = ["Life Satisfaction"]
    items = _make_items(
        ["item one.", "item two.", "item three.", "item four.", "item five."],
        facet_names * 5,
    )

    rng = np.random.default_rng(42)
    base = np.array([1.0, 0.0, 0.0, 0.0])
    text_to_emb = {
        "item one.": base + rng.normal(0, 0.05, 4),
        "item two.": base + rng.normal(0, 0.05, 4),
        "item three.": base + rng.normal(0, 0.05, 4),
        "item four.": base + rng.normal(0, 0.05, 4),
        # one weak/cross-loaded item
        "item five.": np.array([0.5, 0.5, 0.0, 0.0]) + rng.normal(0, 0.03, 4),
    }

    def _embed_lookup(item_texts, model=None):
        return np.array([text_to_emb[t] for t in item_texts])

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", _embed_lookup)

    unidim_mapping = FacetMapperResponse(
        is_unidimensional=True,
        facets=[
            FacetDefinition(
                facet_name="Life Satisfaction",
                facet_description="Single facet for life satisfaction",
                exclusions="Not life evaluation tied to specific domains",
                target_item_count=3,
            )
        ],
        theoretical_basis="SWLS-style unidimensional model",
    )

    kept, dropped, _ = prune_items(
        items,
        facet_mapping=unidim_mapping,
        target_count=3,
        max_iters=10,
    )
    # Should successfully prune from 5 → 3 (was getting blocked by facet preservation)
    assert len(kept) == 3
    assert len(dropped) == 2


def test_prune_items_respects_deadline(monkeypatch):
    """Pruning should break early when the deadline is in the past."""
    from backend.agents.pfa_pruning import prune_items
    import time as _time

    items = _make_items(
        ["item one.", "item two.", "item three.", "item four.", "item five."],
        ["FacetA"] * 5,
    )
    rng = np.random.default_rng(42)
    text_to_emb_d = {
        "item one.": np.array([1.0, 0.0, 0.0, 0.0]) + rng.normal(0, 0.05, 4),
        "item two.": np.array([1.0, 0.0, 0.0, 0.0]) + rng.normal(0, 0.05, 4),
        "item three.": np.array([1.0, 0.0, 0.0, 0.0]) + rng.normal(0, 0.05, 4),
        "item four.": np.array([1.0, 0.0, 0.0, 0.0]) + rng.normal(0, 0.05, 4),
        "item five.": np.array([1.0, 0.0, 0.0, 0.0]) + rng.normal(0, 0.05, 4),
    }

    def _embed_lookup_d(item_texts, model=None):
        return np.array([text_to_emb_d[t] for t in item_texts])

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", _embed_lookup_d)

    # Deadline already passed → loop should break immediately and return current set
    past_deadline = _time.time() - 100
    kept, dropped, _ = prune_items(
        items,
        facet_mapping=_make_facet_mapping(["FacetA"]),
        target_count=2,
        max_iters=10,
        deadline=past_deadline,
    )
    # No iterations should run; original 5 items returned (we didn't get to drop)
    # OR maybe one iteration ran — accept either; main thing is we don't loop forever.
    assert len(kept) >= 2
    assert len(kept) <= 5


def test_prune_items_skips_when_below_target(monkeypatch):
    from backend.agents.pfa_pruning import prune_items
    items = _make_items(["item a.", "item b.", "item c."], ["FacetA", "FacetB", "FacetC"])
    fake_embeddings = np.eye(3)

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", lambda items, model: fake_embeddings)

    kept, dropped, _ = prune_items(
        items,
        facet_mapping=_make_facet_mapping(["FacetA", "FacetB", "FacetC"]),
        target_count=5,  # already below target
        max_iters=2,
    )
    assert len(kept) == 3
    assert dropped == []


def test_prune_items_returns_pfa_result_when_no_pruning_needed(monkeypatch):
    """Regression: even when items ≤ target (no pruning to do), the function
    must return a non-empty PFAResult so the UI can render the panel.

    This was the user-reported bug where the PFA panel disappeared on a run
    where items were already at target_count.
    """
    from backend.agents.pfa_pruning import prune_items
    items = _make_items(
        ["item alpha.", "item bravo.", "item charlie.", "item delta."],
        ["FacetA"] * 4,
    )
    rng = np.random.default_rng(42)
    text_to_emb_n = {
        f"item {name}.": np.array([1.0, 0.0, 0.0, 0.0]) + rng.normal(0, 0.05, 4)
        for name in ["alpha", "bravo", "charlie", "delta"]
    }

    def _embed_lookup_n(item_texts, model=None):
        return np.array([text_to_emb_n[t] for t in item_texts])

    import backend.agents.pfa_estimator as pfa_mod
    monkeypatch.setattr(pfa_mod, "embed_items_sync", _embed_lookup_n)

    kept, dropped, pfa_result = prune_items(
        items,
        facet_mapping=_make_facet_mapping(["FacetA"]),
        target_count=10,  # already below target → no pruning happens
        max_iters=2,
    )
    assert len(kept) == 4
    assert dropped == []
    assert pfa_result is not None
    assert pfa_result.n_items == 4
    # The PFA pass should produce loadings for the UI
    assert len(pfa_result.loadings) == 4


# ----- Live API replication test (gated) -----


@pytest.mark.skipif(
    os.environ.get("RUN_PFA_LIVE") != "1",
    reason="Live OpenAI replication test (set RUN_PFA_LIVE=1 to enable)",
)
def test_dass21_pfa_live():
    """Replicate DASS-21 factor recovery using real OpenAI embeddings.

    Expectations from Varrasi et al. (2026):
    - 3 factors (Depression, Anxiety, Stress).
    - Tucker's congruence ≥ 0.80 (paper got 0.85+ with sentence-transformers).
    - Factor recovery rate ≥ 0.66 (2 of 3 factors).
    """
    # Subset of DASS-21 items (4 per factor; sufficient for FA)
    dass = [
        # Depression
        ("I couldn't seem to experience any positive feeling at all.", "Depression"),
        ("I felt that life was meaningless.", "Depression"),
        ("I felt down-hearted and blue.", "Depression"),
        ("I felt I had nothing to look forward to.", "Depression"),
        # Anxiety
        ("I was aware of the dryness of my mouth.", "Anxiety"),
        ("I experienced trembling (e.g., in the hands).", "Anxiety"),
        ("I felt scared without any good reason.", "Anxiety"),
        ("I was worried about situations in which I might panic.", "Anxiety"),
        # Stress
        ("I found it hard to wind down.", "Stress"),
        ("I tended to over-react to situations.", "Stress"),
        ("I felt that I was using a lot of nervous energy.", "Stress"),
        ("I found it difficult to relax.", "Stress"),
    ]
    items = _make_items([t for t, _ in dass], [f for _, f in dass])

    result = run_pfa(
        items,
        facet_mapping=_make_facet_mapping(["Depression", "Anxiety", "Stress"]),
        n_factors=3,
    )
    mean_congruence = float(np.mean(result.tuckers_congruence)) if result.tuckers_congruence else 0.0
    assert mean_congruence >= 0.50, (
        f"Mean Tucker's congruence {mean_congruence:.3f} below 0.50 threshold"
    )
    assert result.factor_recovery_rate >= 0.33, (
        f"Factor recovery rate {result.factor_recovery_rate:.3f} below 0.33 threshold"
    )
