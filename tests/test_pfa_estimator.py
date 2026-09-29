"""Unit tests for the pure psychometric helpers in pfa_estimator.

These cover the fixed bugs: factor-order alignment (CBI permutation), sign
reflection, and the retention rules. All are pure NumPy — no network, no LLM.
"""

import numpy as np
import pytest

from backend.agents.pfa_estimator import (
    _align_factor_order,
    _align_factor_signs,
    build_expected_pattern,
    compute_model_fit,
    compute_retention_flags,
    factor_recovery_rate,
    label_factors_via_daal,
    tuckers_congruence,
)


# ---- Tucker's congruence ----


def test_tuckers_congruence_identical_is_one():
    A = np.array([[1.0, 0.0], [0.8, 0.1], [0.0, 1.0]])
    assert np.allclose(tuckers_congruence(A, A), [1.0, 1.0])


def test_tuckers_congruence_orthogonal_is_zero():
    A = np.array([[1.0], [0.0]])
    B = np.array([[0.0], [1.0]])
    assert np.allclose(tuckers_congruence(A, B), [0.0])


def test_tuckers_congruence_reflection_is_negative():
    A = np.array([[1.0, 0.5], [0.8, 0.3]])
    assert np.allclose(tuckers_congruence(A, -A), [-1.0, -1.0])


# ---- expected pattern ----


def test_build_expected_pattern_one_hot():
    pattern = build_expected_pattern([0, 1, 0], 2)
    expected = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
    assert np.array_equal(pattern, expected)


# ---- factor recovery ----


def test_factor_recovery_rate_perfect():
    loadings = np.array([[0.9, 0.1], [0.8, 0.2], [0.2, 0.8], [0.1, 0.9]])
    rate, flags = factor_recovery_rate(loadings, [0, 0, 1, 1])
    assert rate == 1.0
    assert flags == [True, True]


def test_factor_recovery_permuted_columns_is_fixed_by_alignment():
    """Regression for the CBI bug: a perfectly-recovered structure read 0.0
    purely because oblimin returned factors in permuted order. Alignment must
    restore recovery to 1.0."""
    loadings = np.array(
        [
            [0.1, 0.9],  # facet-0 item, actually loads on recovered col 1
            [0.2, 0.8],
            [0.8, 0.2],  # facet-1 item, actually loads on recovered col 0
            [0.9, 0.1],
        ]
    )
    expected_assignments = [0, 0, 1, 1]
    # Without alignment: 0.0 (both facets read as unrecovered).
    rate_raw, _ = factor_recovery_rate(loadings, expected_assignments)
    assert rate_raw == 0.0
    # With alignment: columns swap so facet 0 -> col 1, facet 1 -> col 0.
    aligned, perm = _align_factor_order(loadings, expected_assignments, 2)
    assert list(perm) == [1, 0]
    rate_aligned, _ = factor_recovery_rate(aligned, expected_assignments)
    assert rate_aligned == 1.0


# ---- factor-order alignment ----


def test_align_factor_order_identity_when_already_ordered():
    loadings = np.array([[0.9, 0.1], [0.8, 0.2], [0.2, 0.8], [0.1, 0.9]])
    aligned, perm = _align_factor_order(loadings, [0, 0, 1, 1], 2)
    assert list(perm) == [0, 1]
    assert np.allclose(aligned, loadings)


def test_align_factor_order_robust_to_sign_flip():
    # Items loading negatively on their own factor still match their facet.
    loadings = np.array(
        [[-0.9, 0.1], [-0.8, 0.2], [0.2, -0.8], [0.1, -0.9]]
    )
    aligned, perm = _align_factor_order(loadings, [0, 0, 1, 1], 2)
    assert list(perm) == [0, 1]


def test_align_factor_order_single_factor_noop():
    loadings = np.array([[0.9], [0.8], [0.7]])
    aligned, perm = _align_factor_order(loadings, [0, 0, 0], 1)
    assert list(perm) == [0]


# ---- retention flags ----


def test_retention_flags_all_well_loaded():
    loadings = np.array([[0.9, 0.1, 0.1], [0.8, 0.2, 0.1], [0.1, 0.9, 0.1]])
    retention = compute_retention_flags(loadings, [0, 0, 1])
    assert all(ok for ok, _ in retention)


def test_retention_flags_cross_loading_dominates():
    loadings = np.array([[0.3, 0.8], [0.9, 0.1]])  # item 0 loads on wrong factor
    retention = compute_retention_flags(loadings, [0, 0])
    ok0, violations0 = retention[0]
    assert not ok0
    assert "rule2_cross_loading_dominates" in violations0


# ---- DAAL labels ----


def test_label_factors_via_daal():
    loadings = np.array([[0.9, 0.1], [0.8, 0.2], [0.1, 0.9]])
    labels = label_factors_via_daal(loadings, [0, 0, 1], ["Vigor", "Dedication"])
    assert labels == ["Vigor", "Dedication"]


# ---- model fit ----


def test_compute_model_fit_perfect_reproduction():
    loadings = np.full((3, 1), 1.0)
    sim = np.ones((3, 3))
    rmsr, caf, _ = compute_model_fit(sim, loadings, phi=np.eye(1))
    assert rmsr < 1e-9
    assert caf == pytest.approx(1.0)


# ---- sign alignment ----


def test_align_factor_signs_flips_negative_dominant():
    loadings = np.array([[-0.9, 0.5], [-0.8, 0.4]])
    aligned, flipped, signs = _align_factor_signs(loadings)
    assert aligned[0, 0] > 0
    assert flipped == [True, False]
