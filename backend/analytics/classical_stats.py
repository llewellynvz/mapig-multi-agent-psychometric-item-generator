"""Classical psychometric statistics on a respondents x items rating matrix.

Unlike the embedding-based pre-data estimates elsewhere in the pipeline,
these formulas assume a real sample of N respondents, so confidence
intervals and significance tests are mathematically valid here. When the
matrix comes from the synthetic-respondent pilot, the interpretive caveat
is the data source, not the math.
"""

from __future__ import annotations

import logging
import math
import warnings
from typing import Optional

import numpy as np
from scipy import stats

from backend.agents.pfa_estimator import compute_pseudo_omega, ensure_sklearn_compat

logger = logging.getLogger("mapig.classical_stats")


def pearson_matrix(data: np.ndarray) -> np.ndarray:
    """Item-by-item Pearson correlation matrix; cells for zero-variance
    items are NaN rather than raising."""
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = np.corrcoef(data, rowvar=False)
    return np.atleast_2d(corr)


def fisher_ci(
    r: float, n: int, confidence: float = 0.95
) -> tuple[Optional[float], Optional[float]]:
    """Fisher-z confidence interval for a Pearson correlation.

    Returns (None, None) when not estimable: n <= 3, NaN, or |r| >= 1
    (arctanh diverges).
    """
    if n <= 3 or not np.isfinite(r) or abs(r) >= 1.0:
        return None, None
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    crit = float(stats.norm.ppf(0.5 + confidence / 2.0))
    return float(math.tanh(z - crit * se)), float(math.tanh(z + crit * se))


def cronbach_alpha(data: np.ndarray) -> Optional[float]:
    """Cronbach's alpha from raw scores: k/(k-1) * (1 - sum(item var)/var(total)).

    Returns None when not estimable: fewer than 2 items or 2 respondents,
    or zero total-score variance.
    """
    n, k = data.shape
    if k < 2 or n < 2:
        return None
    item_vars = data.var(axis=0, ddof=1)
    total_var = data.sum(axis=1).var(ddof=1)
    if total_var <= 0:
        return None
    return float(k / (k - 1) * (1.0 - item_vars.sum() / total_var))


def bartlett_sphericity(
    corr: np.ndarray, n: int
) -> tuple[Optional[float], Optional[float]]:
    """Bartlett's test of sphericity: chi2 = -[(n-1) - (2k+5)/6] * ln|R|.

    Returns (chi2, p_value), or (None, None) when the determinant is
    non-positive or the matrix contains non-finite cells.
    """
    if not np.isfinite(corr).all():
        return None, None
    k = corr.shape[0]
    sign, logdet = np.linalg.slogdet(corr)
    if sign <= 0:
        return None, None
    chi2 = -(n - 1 - (2 * k + 5) / 6.0) * logdet
    df = k * (k - 1) / 2.0
    return float(chi2), float(stats.chi2.sf(chi2, df))


def parallel_analysis(
    data: np.ndarray,
    n_iter: int = 100,
    percentile: float = 95.0,
    seed: int = 42,
) -> tuple[Optional[int], list[float], list[float]]:
    """Horn's parallel analysis on PCA eigenvalues of the correlation matrix.

    Retains factors whose observed eigenvalue exceeds the given percentile
    of eigenvalues from random normal data of the same shape. Returns
    (n_retained, observed_eigenvalues, threshold_eigenvalues), or
    (None, [], []) when the observed matrix is not estimable.
    """
    n, k = data.shape
    observed = pearson_matrix(data)
    if not np.isfinite(observed).all():
        return None, [], []
    rng = np.random.default_rng(seed)
    random_eigs = np.empty((n_iter, k))
    for i in range(n_iter):
        r = np.corrcoef(rng.standard_normal((n, k)), rowvar=False)
        random_eigs[i] = np.sort(np.linalg.eigvalsh(r))[::-1]
    thresholds = np.percentile(random_eigs, percentile, axis=0)
    real_eigs = np.sort(np.linalg.eigvalsh(observed))[::-1]
    n_retained = int(np.sum(real_eigs > thresholds))
    return (
        n_retained,
        [float(e) for e in real_eigs],
        [float(t) for t in thresholds],
    )


def kmo(corr: np.ndarray) -> Optional[float]:
    """Kaiser-Meyer-Olkin sampling adequacy on a real correlation matrix.

    Same anti-image formula as the semantic heuristic, but on a matrix
    with a genuine N this is the standard KMO statistic.
    """
    if not np.isfinite(corr).all():
        return None
    from backend.agents.pfa_estimator import compute_semantic_kmo

    return compute_semantic_kmo(corr)


def efa_omega(data: np.ndarray, n_factors: int) -> Optional[float]:
    """McDonald's omega-total from a minres EFA on the raw score matrix
    (oblimin when n_factors > 1). Returns None when the fit fails or the
    solution is degenerate (Heywood case)."""
    n, k = data.shape
    degrees_of_freedom = ((k - n_factors) ** 2 - (k + n_factors)) / 2
    if k < 3 or n < 5 or n_factors < 1 or degrees_of_freedom < 0:
        return None
    ensure_sklearn_compat()
    from factor_analyzer import FactorAnalyzer

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fa = FactorAnalyzer(
                n_factors=n_factors,
                rotation="oblimin" if n_factors > 1 else None,
                method="minres",
            )
            fa.fit(data)
    except Exception as exc:
        logger.warning("EFA_OMEGA fit failed: %s", exc)
        return None
    loadings = np.asarray(fa.loadings_)
    phi = getattr(fa, "phi_", None)
    return compute_pseudo_omega(loadings, np.asarray(phi) if phi is not None else None)
