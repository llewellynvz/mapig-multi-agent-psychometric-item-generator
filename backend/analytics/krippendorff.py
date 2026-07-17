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
from typing import Iterable, List, Optional

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


def cohens_kappa(
    a: np.ndarray,
    b: np.ndarray,
    weighted: bool = True,
    categories: Optional[Iterable[float]] = None,
) -> float:
    """Compute (linear-weighted) Cohen's κ for two raters' ratings.

    Args:
        a: 1D array of rater A's ratings.
        b: 1D array of rater B's ratings (same length as a).
        weighted: If True, use linear weights for ordinal data. If False,
            use unweighted κ (treat ratings as nominal).
        categories: The full ordinal scale (e.g., range(1, 6) for a 1-5
            rubric). Weights are then based on category VALUES, so unused
            scale points keep their true distance — raters using only {1, 3, 5}
            are 2 scale points apart between 1 and 3, not adjacent. When None,
            falls back to the observed unique values (legacy behavior, only
            safe when every scale point appears).

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

    if categories is not None:
        cats = np.asarray(sorted(float(c) for c in categories), dtype=float)
        observed = set(np.concatenate([a_v, b_v]).tolist())
        if not observed.issubset(set(cats.tolist())):
            raise ValueError(
                f"Ratings contain values outside the declared categories: "
                f"{sorted(observed - set(cats.tolist()))}"
            )
    else:
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
        # Linear weights on category VALUES (standard weighted-kappa
        # definition); equals index-based weights only for evenly spaced,
        # fully observed scales.
        span = float(cats[-1] - cats[0])
        w = 1.0 - np.abs(cats[:, None] - cats[None, :]) / span
        po = float((w * obs).sum())
        pe = float((w * expected).sum())
    else:
        po = float(np.trace(obs))
        pe = float(np.trace(expected))

    if pe == 1.0:
        # Chance agreement is total (e.g., both raters constant): κ = 0/0.
        # Undefined — report NaN rather than claiming perfect or zero agreement.
        return float("nan")
    return float((po - pe) / (1.0 - pe))


def pairwise_kappa_matrix(
    ratings: np.ndarray,
    role_labels: Iterable[str],
    categories: Optional[Iterable[float]] = None,
) -> dict[str, Optional[float]]:
    """Compute Cohen's κ for every pair of raters.

    Args:
        ratings: 2D array (n_raters, n_items) with NaN for missing ratings.
        role_labels: Per-rater role labels of length n_raters.
        categories: Full ordinal scale passed through to cohens_kappa.

    Returns:
        Dict mapping "role_a|role_b" -> κ, or None when κ is not estimable
        (e.g., zero variance) — never collapsed to 0.0.
    """
    arr = np.asarray(ratings, dtype=float)
    labels = list(role_labels)
    out: dict[str, Optional[float]] = {}
    n_raters = arr.shape[0]
    for i in range(n_raters):
        for j in range(i + 1, n_raters):
            try:
                k = cohens_kappa(arr[i], arr[j], weighted=True, categories=categories)
            except Exception as e:
                logger.warning("κ computation failed for %s vs %s: %s", labels[i], labels[j], e)
                k = float("nan")
            key = f"{labels[i]}|{labels[j]}"
            out[key] = round(float(k), 3) if not np.isnan(k) else None
    return out


def spearman_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Compute Spearman rank-correlation between two rating vectors.

    Robust to differences in absolute scale — measures whether two raters
    agree on the RELATIVE ORDERING of items even when their score
    distributions differ. This is the right metric for inter-rater
    reliability when raters use DIFFERENT rubrics (e.g., MAPIG's
    psychometric / domain / localization experts), because their absolute
    scores are not expected to match but their item rankings often should.

    Args:
        a, b: 1D arrays of equal length. NaN entries are treated as missing
            (pairs with NaN in either vector are dropped before ranking).

    Returns:
        Spearman ρ in [-1, 1]. NaN if too few valid pairs (< 3) or zero
        variance in either rank vector.
    """
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    if a_arr.shape != b_arr.shape:
        raise ValueError(
            f"Spearman shape mismatch: {a_arr.shape} vs {b_arr.shape}"
        )

    mask = ~(np.isnan(a_arr) | np.isnan(b_arr))
    a_v = a_arr[mask]
    b_v = b_arr[mask]
    if len(a_v) < 3:
        return float("nan")

    # Convert raw values to ranks (average ranking for ties — standard Spearman)
    a_ranks = _average_ranks(a_v)
    b_ranks = _average_ranks(b_v)

    # Pearson correlation on ranks = Spearman ρ
    a_mean = a_ranks.mean()
    b_mean = b_ranks.mean()
    a_dev = a_ranks - a_mean
    b_dev = b_ranks - b_mean
    num = float(np.sum(a_dev * b_dev))
    den = float(np.sqrt(np.sum(a_dev**2) * np.sum(b_dev**2)))
    if den == 0.0:
        return float("nan")
    return float(np.clip(num / den, -1.0, 1.0))


def _average_ranks(values: np.ndarray) -> np.ndarray:
    """Convert values to average ranks (ties get the mean of their rank slots).

    Pure-NumPy alternative to scipy.stats.rankdata to avoid adding scipy as a
    direct dependency in the IRR module.
    """
    n = len(values)
    order = np.argsort(values, kind="stable")
    sorted_vals = values[order]
    ranks = np.zeros(n, dtype=float)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        # Items from i..j (inclusive) are tied — assign average of ranks i+1..j+1
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pairwise_spearman_matrix(
    ratings: np.ndarray,
    role_labels: Iterable[str],
) -> dict[str, Optional[float]]:
    """Spearman ρ for every pair of raters. Same shape contract as
    pairwise_kappa_matrix. Not-estimable pairs (zero variance, too few
    ratings) are reported as None, never collapsed to 0.0.
    """
    arr = np.asarray(ratings, dtype=float)
    labels = list(role_labels)
    out: dict[str, Optional[float]] = {}
    n_raters = arr.shape[0]
    for i in range(n_raters):
        for j in range(i + 1, n_raters):
            try:
                rho = spearman_correlation(arr[i], arr[j])
            except Exception as e:
                logger.warning(
                    "Spearman ρ failed for %s vs %s: %s",
                    labels[i], labels[j], e,
                )
                rho = float("nan")
            key = f"{labels[i]}|{labels[j]}"
            out[key] = round(float(rho), 3) if not np.isnan(rho) else None
    return out


def krippendorff_alpha_nominal(ratings: list[list[str | int]]) -> float:
    """Krippendorff's α for nominal categorical data (strings or ints).

    Use this for verdict-level agreement (accept/revise/reject_set) where
    raters' categorical decisions are the unit of analysis, not numeric scores.

    Args:
        ratings: 2D list of shape (n_raters, n_items). Use None for missing.

    Returns:
        α in [-∞, 1]. NaN if insufficient data.
    """
    if not ratings or len(ratings) < 2:
        return float("nan")
    n_items = len(ratings[0])
    if n_items < 2:
        return float("nan")

    # Map categories to ints
    all_values: list[str | int] = []
    for row in ratings:
        for v in row:
            if v is not None:
                all_values.append(v)
    if not all_values:
        return float("nan")
    cats = sorted(set(all_values), key=str)
    cat_to_int = {c: i for i, c in enumerate(cats)}

    # Build numeric array with NaN for missing
    n_raters = len(ratings)
    arr = np.full((n_raters, n_items), np.nan, dtype=float)
    for r in range(n_raters):
        for c in range(n_items):
            v = ratings[r][c]
            if v is not None:
                arr[r, c] = float(cat_to_int[v])

    # Nominal distance: 0 if equal, 1 if different
    items_with_pairs: list[np.ndarray] = []
    for j in range(n_items):
        col = arr[:, j]
        valid = col[~np.isnan(col)]
        if len(valid) >= 2:
            items_with_pairs.append(valid)
    if not items_with_pairs:
        return float("nan")

    # Observed disagreement
    observed_num = 0.0
    pair_count_total = 0
    for valid in items_with_pairs:
        m = len(valid)
        weight = 1.0 / (m - 1) if m > 1 else 1.0
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                if valid[a] != valid[b]:
                    observed_num += weight
        pair_count_total += m

    # Expected disagreement (nominal)
    all_valid = np.concatenate(items_with_pairs)
    n_total = len(all_valid)
    if n_total < 2:
        return float("nan")
    unique_values, counts = np.unique(all_valid, return_counts=True)
    expected_sum = 0.0
    for ci, c in enumerate(unique_values):
        for ki, k in enumerate(unique_values):
            if ci == ki:
                continue
            expected_sum += counts[ci] * counts[ki]  # nominal distance = 1

    Do = observed_num / max(pair_count_total, 1)
    De = expected_sum / max(n_total * (n_total - 1), 1)
    if De == 0:
        return 1.0
    return float(1.0 - Do / De)
