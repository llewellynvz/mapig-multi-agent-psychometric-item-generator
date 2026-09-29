"""Regression tests for the psychometric-correctness fixes in PFA, pruning,
EGA/UVA and Krippendorff's alpha.

All tests are offline: embeddings are synthetic and injected via monkeypatch.
"""

import math

import numpy as np
import pytest

from backend.agents import pfa_estimator as pe
from backend.agents import pfa_pruning
from backend.analytics import ega
from backend.analytics.krippendorff import krippendorff_alpha, krippendorff_alpha_nominal
from backend.schemas import (
    DraftItem,
    FacetDefinition,
    FacetMapperResponse,
    FactorLoading,
    PFAResult,
)


def _item(text: str, facet: str, polarity: str = "+") -> DraftItem:
    return DraftItem(
        item_text=f"{text} item",
        construct_name="Test Construct",
        rationale="Targets the assigned facet.",
        facet_name=facet,
        polarity=polarity,
    )


def _mapping(*facet_names: str) -> FacetMapperResponse:
    return FacetMapperResponse(
        is_unidimensional=len(facet_names) == 1,
        facets=[
            FacetDefinition(
                facet_name=name,
                facet_description=f"Operational definition of {name}.",
                exclusions="Not the other facets.",
                target_item_count=3,
            )
            for name in facet_names
        ],
        theoretical_basis="Synthetic test structure for regression tests.",
    )


def _topic_embeddings(assignments, seed=0, dim=64, signal=0.8, noise=0.35):
    """Items share their facet's topic vector (raw, unflipped cosine > 0)."""
    rng = np.random.default_rng(seed)
    topics = np.linalg.qr(rng.normal(size=(dim, dim)))[0][:, : max(assignments) + 1].T
    return np.array(
        [signal * topics[f] + noise * rng.normal(size=dim) / np.sqrt(dim) for f in assignments]
    )


# ---- 1. reverse-keyed items: signed target pattern + sign-corrected omega ----


def test_expected_pattern_carries_item_keys():
    pattern = pe.build_expected_pattern([0, 0, 1, 1, -1], 2, keys=[1, -1, 1, -1, -1])
    expected = np.array([[1, 0], [-1, 0], [0, 1], [0, -1], [0, 0]], dtype=float)
    assert np.array_equal(pattern, expected)


def test_reverse_keyed_loadings_are_congruent_and_reliable():
    # Perfectly keyed unidimensional scale: reverse items load negatively.
    loadings = np.array([[0.7], [0.7], [0.7], [-0.7], [-0.7]])
    keys = [1, 1, 1, -1, -1]
    unsigned = pe.tuckers_congruence(loadings, pe.build_expected_pattern([0] * 5, 1))
    assert unsigned[0] == pytest.approx(0.2)  # the old, wrong reading
    signed = pe.tuckers_congruence(loadings, pe.build_expected_pattern([0] * 5, 1, keys=keys))
    assert signed[0] == pytest.approx(1.0)

    assert pe.compute_pseudo_omega(loadings) == pytest.approx(0.1612, abs=1e-3)
    omega = pe.compute_pseudo_omega(loadings, keys=keys)
    positive = pe.compute_pseudo_omega(np.abs(loadings))
    assert omega == pytest.approx(positive)
    assert omega > 0.8


def test_sign_alignment_is_key_aware():
    # Dominant loading is a reverse-keyed item loading negatively — the
    # factor is already correctly oriented and must not be reflected.
    loadings = np.array([[0.6], [0.5], [-0.9]])
    aligned, flipped, _ = pe._align_factor_signs(loadings, keys=[1, 1, -1])
    assert flipped == [False]
    assert np.allclose(aligned, loadings)


def test_run_pfa_reverse_keyed_items_not_poor(monkeypatch):
    items = [
        _item("A1", "Vigor"), _item("A2", "Vigor"), _item("A3", "Vigor"),
        _item("A4", "Vigor", "-"), _item("A5", "Vigor", "-"),
        _item("B1", "Focus"), _item("B2", "Focus"), _item("B3", "Focus"),
        _item("B4", "Focus", "-"), _item("B5", "Focus", "-"),
    ]
    emb = _topic_embeddings([0] * 5 + [1] * 5, seed=3)
    monkeypatch.setattr(pe, "embed_items_sync", lambda texts, model=None: emb)

    result = pe.run_pfa(items, facet_mapping=_mapping("Vigor", "Focus"))
    assert min(abs(c) for c in result.tuckers_congruence) > 0.95
    assert all(c > 0 for c in result.tuckers_congruence)
    assert result.factor_recovery_rate == 1.0
    assert result.pseudo_omega is not None and result.pseudo_omega > 0.7
    assert result.fit_verdict != "poor"
    # Reverse items keep their (meaningful) negative loadings in the output.
    assert result.loadings[3].loadings[0] < 0
    assert all(fl.is_well_loaded for fl in result.loadings)


# ---- 2. UVA tie-breaker keeps reverse-keyed items in the network ----


def test_uva_redundancy_not_cut_by_polarity(monkeypatch):
    items = [_item(f"I{i}", "Vigor") for i in range(6)]
    items[1] = _item("I1", "Vigor", "-")
    emb = _topic_embeddings([0] * 6, seed=5, signal=0.5, noise=1.0)
    emb[1] = emb[0] + 0.02 * np.random.default_rng(9).normal(size=emb.shape[1])
    monkeypatch.setattr(
        "backend.agents.correlation_estimator.embed_items_sync",
        lambda texts, model=None: emb,
    )
    scores = pfa_pruning._uva_redundancy_scores(items)
    # The reverse-keyed near-duplicate is as redundant as its sibling.
    assert scores[1] == pytest.approx(scores[0], abs=0.05)
    assert scores[1] >= ega.WTO_REDUNDANCY_THRESHOLD
    assert scores[1] > max(scores[i] for i in range(2, 6))


# ---- 3. retention rule 4 compares against other factors' items ----


def test_rule4_single_factor_keeps_good_items():
    loadings = np.array([[0.80], [0.75], [0.70], [0.65], [0.60], [0.55]])
    retention = pe.compute_retention_flags(loadings, [0] * 6)
    assert all(ok for ok, _ in retention)


def test_rule4_uses_items_from_other_factors():
    loadings = np.array(
        [[0.80, 0.10], [0.50, 0.05], [0.45, 0.10], [0.05, 0.70], [0.60, 0.20], [0.10, 0.60]]
    )
    retention = pe.compute_retention_flags(loadings, [0, 0, 0, 1, 1, 1])
    # Item 1 (0.50) is below its sibling 0.80 but well above other-factor items.
    assert retention[1] == (True, [])
    # Item 4 loads mainly on the wrong factor.
    assert "rule2_cross_loading_dominates" in retention[4][1]
    # Item 3's parent loading 0.70 vs other-factor mean on factor 1 (0.10,0.05,0.10)
    assert retention[3] == (True, [])


def test_rule4_flags_parent_loading_below_other_factor_items():
    loadings = np.array([[0.35, 0.30], [0.60, 0.10], [0.50, 0.70], [0.40, 0.65]])
    retention = pe.compute_retention_flags(loadings, [0, 0, 1, 1])
    # Item 0: 0.35 on factor 0 vs other-factor items' mean (0.50+0.40)/2=0.45
    assert "rule4_below_avg_items_on_factor" in retention[0][1]


# ---- 4. unmatched facet names ----


def test_facet_names_match_case_and_whitespace_insensitively(caplog):
    items = [_item("A", " vigor  "), _item("B", "FOCUS"), _item("C", "Mystery")]
    assignments, labels = pe._facet_assignments_from_mapping(
        items, _mapping("Vigor", "Focus")
    )
    assert labels == ["Vigor", "Focus"]
    assert assignments == [0, 1, -1]
    assert "PFA_FACET_UNMATCHED" in caplog.text


def test_single_facet_mapping_assigns_all_items():
    items = [_item("A", "Vigor"), _item("B", "vigour"), _item("C", "")]
    assignments, _ = pe._facet_assignments_from_mapping(items, _mapping("Vigor"))
    assert assignments == [0, 0, 0]


def test_unmatched_items_excluded_from_retention_and_recovery():
    loadings = np.array([[0.9, 0.1], [0.8, 0.1], [0.1, 0.9], [0.1, 0.8], [0.05, 0.05]])
    assignments = [0, 0, 1, 1, -1]
    retention = pe.compute_retention_flags(loadings, assignments)
    # No expected parent: only rule 1 applies, against its strongest factor.
    assert retention[4] == (False, ["rule1_below_parent_minimum"])
    rate, _ = pe.factor_recovery_rate(loadings, assignments)
    assert rate == 1.0


def test_run_pfa_unmatched_item_excluded_from_congruence(monkeypatch):
    items = [_item(f"A{i}", "Vigor") for i in range(4)] + [
        _item(f"B{i}", "Focus") for i in range(4)
    ]
    items.append(_item("X", "Typo Facet"))
    emb = _topic_embeddings([0] * 4 + [1] * 4 + [1], seed=4)
    monkeypatch.setattr(pe, "embed_items_sync", lambda texts, model=None: emb[: len(texts)])
    result = pe.run_pfa(items, facet_mapping=_mapping("Vigor", "Focus"))
    stray = result.loadings[8]
    assert stray.is_well_loaded and stray.retention_rule_violations == []
    assert stray.parent_factor == stray.primary_factor
    matched_only = pe.run_pfa(items[:8], facet_mapping=_mapping("Vigor", "Focus"))
    assert min(result.tuckers_congruence) > 0.95
    assert min(matched_only.tuckers_congruence) > 0.95


# ---- 5. CAF = 1 − KMO(residual matrix) ----


def test_caf_is_one_minus_kmo_of_residual():
    rng = np.random.default_rng(0)
    L = np.zeros((8, 2))
    L[:4, 0] = 0.75
    L[4:, 1] = 0.75
    noise = rng.normal(0, 0.03, (8, 8))
    noise = (noise + noise.T) / 2
    sim = L @ L.T + noise
    np.fill_diagonal(sim, 1.0)

    # Correct two-factor model: residual is noise → CAF high.
    _, caf_good, _ = pe.compute_model_fit(sim, L, phi=np.eye(2))
    residual = sim - L @ L.T
    assert caf_good == pytest.approx(1.0 - pe.compute_semantic_kmo(residual))
    assert caf_good > 0.8

    # Under-factored model leaves common variance in the residual → CAF low.
    one = np.full((8, 1), np.sqrt(0.75 ** 2 / 2))
    _, caf_under, _ = pe.compute_model_fit(sim, one, phi=np.eye(1))
    assert caf_under < 0.5


def test_caf_exact_fit_and_heywood():
    _, caf, _ = pe.compute_model_fit(np.ones((3, 3)), np.ones((3, 1)), phi=np.eye(1))
    assert caf == 1.0
    sim = np.array([[1.0, 0.5, 0.3], [0.5, 1.0, 0.2], [0.3, 0.2, 1.0]])
    _, caf, _ = pe.compute_model_fit(sim, np.array([[1.1], [0.4], [0.3]]), phi=np.eye(1))
    assert caf is None


# ---- 6. pruning continues past weak items blocked by the facet floor ----


def _fake_run_pfa(weak_texts):
    def run(items, facet_mapping=None, items_dropped=None, **_):
        loadings = []
        for i, it in enumerate(items):
            weak = it.item_text in weak_texts
            primary = 0.2 if weak else 0.9 - 0.05 * i
            loadings.append(
                FactorLoading(
                    item_index=i,
                    item_text=it.item_text,
                    facet_name=it.facet_name,
                    loadings=[primary],
                    parent_factor=0,
                    primary_loading=primary,
                    primary_factor=0,
                    is_well_loaded=not weak,
                    retention_rule_violations=["rule1_below_parent_minimum"] if weak else [],
                )
            )
        return PFAResult(
            embedding_model="fake",
            n_items=len(items),
            n_factors=1,
            factor_labels=["F"],
            loadings=loadings,
            tuckers_congruence=[],
            factor_recovery_rate=None,
            rmsr=None,
            caf=None,
            eigenvalues=[],
            residual_correlation_matrix=[],
            items_dropped=items_dropped or [],
            fit_verdict="not_estimable",
        )

    return run


def test_pruning_drops_clean_items_when_weak_are_at_floor(monkeypatch):
    # Facet B is at its floor (1 item) and its only item is weak; facet A has
    # 4 clean items. Target 3 must still be reached by dropping from A.
    items = [_item(f"A{i}", "Fa") for i in range(4)] + [_item("B0", "Fb")]
    monkeypatch.setattr(pfa_pruning, "run_pfa", _fake_run_pfa({"B0 item"}))
    monkeypatch.setattr(pfa_pruning, "_uva_redundancy_scores", lambda items: {})
    kept, dropped, _ = pfa_pruning.prune_items(
        items, _mapping("Fa", "Fb"), target_count=3, min_per_facet=1
    )
    assert len(kept) == 3
    assert "B0 item" in [it.item_text for it in kept]
    # The lowest-loading clean items (latest in A, by the fake's loadings) go first.
    assert dropped == [3, 2]


def test_pruning_stops_when_every_facet_is_at_floor(monkeypatch):
    items = [_item("A0", "Fa"), _item("B0", "Fb"), _item("C0", "Fc"), _item("C1", "Fc")]
    monkeypatch.setattr(pfa_pruning, "run_pfa", _fake_run_pfa({"A0 item"}))
    monkeypatch.setattr(pfa_pruning, "_uva_redundancy_scores", lambda items: {})
    kept, dropped, _ = pfa_pruning.prune_items(
        items, _mapping("Fa", "Fb", "Fc"), target_count=2, min_per_facet=1
    )
    assert dropped == [3]
    assert len(kept) == 3


# ---- 7. EGA: singleton communities are not dimensions ----


def test_isolated_nodes_are_not_dimensions():
    sim = np.full((6, 6), 0.1)
    np.fill_diagonal(sim, 1.0)
    result = ega.build_ega_result(ega.build_semantic_network(sim), "semantic_threshold")
    assert result.n_dimensions == 0
    assert result.communities == []
    # Each unassigned node gets its own index outside `communities`.
    assert sorted(n.community for n in result.nodes) == list(range(6))


def test_singletons_excluded_but_real_communities_counted():
    sim = np.full((7, 7), 0.05)
    sim[:3, :3] = 0.6
    sim[3:6, 3:6] = 0.6
    np.fill_diagonal(sim, 1.0)
    result = ega.build_ega_result(ega.build_semantic_network(sim), "semantic_threshold")
    assert result.n_dimensions == 2
    assert result.communities == [[0, 1, 2], [3, 4, 5]]
    by_item = {n.item_index: n.community for n in result.nodes}
    assert by_item[6] >= result.n_dimensions


# ---- 8. UVA wTO on a partial-correlation network ----


def _dense_sim(n=12, seed=1):
    rng = np.random.default_rng(seed)
    sim = rng.uniform(0.30, 0.55, (n, n))
    sim = (sim + sim.T) / 2
    np.fill_diagonal(sim, 1.0)
    return sim


def test_uva_does_not_flag_dense_ordinary_network():
    sim = _dense_sim()
    # The old zero-order computation flagged every pair.
    zero_order = ega.graph_to_adjacency(ega.build_semantic_network(sim))
    assert len(ega.find_redundant_pairs(zero_order)) == 66
    result = ega.build_ega_result(ega.build_semantic_network(sim), "semantic_threshold")
    assert result.redundant_pairs == []


def test_uva_flags_genuine_near_duplicate():
    sim = _dense_sim()
    rng = np.random.default_rng(2)
    sim[0, 1] = sim[1, 0] = 0.92
    for i in range(2, 12):
        sim[1, i] = sim[i, 1] = sim[0, i] + rng.normal(0, 0.02)
    result = ega.build_ega_result(ega.build_semantic_network(sim), "semantic_threshold")
    assert [(p.item_i_index, p.item_j_index) for p in result.redundant_pairs] == [(0, 1)]


def test_uva_exact_duplicate_uses_ridge():
    sim = _dense_sim()
    sim[1, :] = sim[0, :]
    sim[:, 1] = sim[:, 0]
    sim[0, 1] = sim[1, 0] = 1.0
    np.fill_diagonal(sim, 1.0)
    adjacency = ega.semantic_uva_adjacency(sim)
    assert adjacency is not None
    pairs = ega.find_redundant_pairs(adjacency)
    assert pairs[0][:2] == (0, 1)


# ---- 9. Krippendorff's alpha undefined without variation ----


def test_alpha_nan_when_no_variation():
    assert math.isnan(krippendorff_alpha(np.full((3, 4), 4.0)))
    assert math.isnan(krippendorff_alpha(np.full((3, 4), 4.0), level="interval"))
    assert math.isnan(krippendorff_alpha_nominal([["accept"] * 3 for _ in range(3)]))


def test_alpha_still_one_for_perfect_agreement_with_variation():
    ratings = np.array([[1, 2, 3, 4], [1, 2, 3, 4]], dtype=float)
    assert krippendorff_alpha(ratings) == pytest.approx(1.0)
    assert krippendorff_alpha_nominal([["a", "b", "c"], ["a", "b", "c"]]) == pytest.approx(1.0)
