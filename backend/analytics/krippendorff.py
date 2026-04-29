"""Inter-rater reliability metrics in pure NumPy.

Implements:
- Krippendorff's α (ordinal level) — for multi-rater overall agreement.
- Cohen's κ (linear-weighted, ordinal) — for pairwise agreement matrices.

References:
- Krippendorff, K. (2018). Content Analysis: An Introduction to Its Methodology (4th ed.).
- Cohen, J. (1968). Weighted kappa. Psychological Bulletin.

No external dependencies beyond NumPy.
"""

from __future__ import annotations

import logging
from typing import Iterable, List

import numpy as np

logger = logging.getLogger("lmaig.krippendorff")


def krippendorff_alpha(ratings: np.ndarray, level: str = "ordinal") -> float:
    """Compute Krippendorff's α for an arbitrary number of raters and items.

    Args:
        ratings: 2D array of shape (n_raters, n_items). NaN values represent
            missing ratings.
        level: Distance metric. Currently only "ordinal" is implemented (sufficient
            for our 1-5 Likert use case). For "interval", squared distance is used;
            for "ordinal", a rank-based distance is used.

    Returns:
        Krippendorff's α in [-∞, 1]. ≥0.8 strong, ≥0.667 acceptable, <0.4 poor.
        Returns NaN if there is insufficient data (need ≥ 2 raters and ≥ 2 items
        with at least 2 valid observations each).
    """
    arr = np.asarray(ratings, dtype=float)
    if arr.ndim != 2:
        raise ValueError("ratings must be 2D (n_raters, n_items)")

    n_raters, n_items = arr.shape
    if n_raters < 2 or n_items < 2:
        return float("nan")

    # Reliability data: per item, list of valid ratings
    items_with_pairs: List[np.ndarray] = []
    for j in range(n_items):
        col = arr[:, j]
        valid = col[~np.isnan(col)]
        if len(valid) >= 2:
            items_with_pairs.append(valid)

    if len(items_with_pairs) == 0:
        return float("nan")

    # Build distance function for chosen level
    def _ordinal_distance(c: float, k: float, totals: np.ndarray, values: np.ndarray) -> float:
        # Krippendorff's ordinal distance:
        # d2(c, k) = ( sum_{g=c..k} n_g - (n_c + n_k)/2 )^2  (for c<=k)
        if c == k:
            return 0.0
        a, b = (c, k) if c <= k else (k, c)
        # find indices of a and b in values
        idx_a = np.where(values == a)[0]
        idx_b = np.where(values == b)[0]
        if len(idx_a) == 0 or len(idx_b) == 0:
            return 0.0
        ia, ib = idx_a[0], idx_b[0]
        between = totals[ia : ib + 1]
        diff = float(between.sum() - (totals[ia] + totals[ib]) / 2.0)
        return diff ** 2

    def _interval_distance(c: float, k: float, *_args) -> float:
        return float((c - k) ** 2)

    if level == "ordinal":
        # Build totals across all valid ratings (used by ordinal distance)
        all_valid = np.concatenate(items_with_pairs) if items_with_pairs else np.array([])
        unique_values, counts = np.unique(all_valid, return_counts=True)
        d_func = lambda c, k: _ordinal_distance(c, k, counts.astype(float), unique_values)
    elif level == "interval":
        d_func = lambda c, k: _interval_distance(c, k)
    else:
        raise ValueError(f"Unsupported level: {level}")

    # Observed disagreement: sum over items of pairwise distances within that item
    observed_num = 0.0
    pair_count_total = 0  # total #pairs across all items, used as denominator
    for valid in items_with_pairs:
        m = len(valid)
        weight = 1.0 / (m - 1)  # Krippendorff weighting per pair within item
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                observed_num += weight * d_func(valid[a], valid[b])
        pair_count_total += m

    # Expected disagreement: sum over all pairs across the whole sample (without replacement)
    all_valid = np.concatenate(items_with_pairs) if items_with_pairs else np.array([])
    n_total = len(all_valid)
    if n_total < 2:
        return float("nan")

    # Build coincidence-style expected: sum of d(c,k) * n_c * n_k for all c≠k
    unique_values, counts = np.unique(all_valid, return_counts=True)
    expected_sum = 0.0
    for ci, c in enumerate(unique_values):
        for ki, k in enumerate(unique_values):
            if ci == ki:
                continue
            expected_sum += counts[ci] * counts[ki] * d_func(float(c), float(k))

    # Per Krippendorff: α = 1 - (Do / De)
    Do = observed_num / max(pair_count_total, 1)
    De = expected_sum / max(n_total * (n_total - 1), 1)

    if De == 0:
        # Degenerate case: all values equal → perfect agreement
        return 1.0

    alpha = 1.0 - Do / De
    return float(alpha)


def cohens_kappa(a: np.ndarray, b: np.ndarray, weighted: bool = True) -> float:
    """Compute (linear-weighted) Cohen's κ for two raters' ratings.

    Args:
        a: 1D array of rater A's ratings.
        b: 1D array of rater B's ratings (same length as a).
        weighted: If True, use linear weights for ordinal data. If False,
            use unweighted κ (treat ratings as nominal).

    Returns:
        Cohen's κ in [-1, 1]. NaN if insufficient data.
    """
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    if a_arr.shape != b_arr.shape:
        raise ValueError("a and b must have same shape")

    mask = ~(np.isnan(a_arr) | np.isnan(b_arr))
    a_v = a_arr[mask]
    b_v = b_arr[mask]
    n = len(a_v)
    if n == 0:
        return float("nan")

    # Build joint set of categories
    cats = np.unique(np.concatenate([a_v, b_v]))
    K = len(cats)
    if K <= 1:
        return float("nan")

    cat_to_idx = {c: i for i, c in enumerate(cats)}
    obs = np.zeros((K, K), dtype=float)
    for x, y in zip(a_v, b_v):
        obs[cat_to_idx[x], cat_to_idx[y]] += 1
    obs /= n  # joint frequencies

    # Marginals
    row_marg = obs.sum(axis=1)
    col_marg = obs.sum(axis=0)
    expected = np.outer(row_marg, col_marg)

    if weighted and K > 1:
        # Linear weights
        idx = np.arange(K).astype(float)
        w = 1.0 - np.abs(idx[:, None] - idx[None, :]) / (K - 1)
        po = float((w * obs).sum())
        pe = float((w * expected).sum())
    else:
        po = float(np.trace(obs))
        pe = float(np.trace(expected))

    if pe == 1.0:
        return 1.0 if po == 1.0 else float("nan")
    return float((po - pe) / (1.0 - pe))


def pairwise_kappa_matrix(
    ratings: np.ndarray,
    role_labels: Iterable[str],
) -> dict[str, float]:
    """Compute Cohen's κ for every pair of raters.

    Args:
        ratings: 2D array (n_raters, n_items) with NaN for missing ratings.
        role_labels: Per-rater role labels of length n_raters.

    Returns:
        Dict mapping "role_a|role_b" -> κ.
    """
    arr = np.asarray(ratings, dtype=float)
    labels = list(role_labels)
    out: dict[str, float] = {}
    n_raters = arr.shape[0]
    for i in range(n_raters):
        for j in range(i + 1, n_raters):
            try:
                k = cohens_kappa(arr[i], arr[j], weighted=True)
            except Exception as e:
                logger.warning("κ computation failed for %s vs %s: %s", labels[i], labels[j], e)
                k = float("nan")
            key = f"{labels[i]}|{labels[j]}"
            out[key] = round(float(k), 3) if not np.isnan(k) else 0.0
    return out
