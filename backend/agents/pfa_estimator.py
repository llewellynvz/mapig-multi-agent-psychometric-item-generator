"""Pseudo-Factor Analysis (PFA) estimator.

Implements the PFA methodology from Varrasi et al. (2026, Methods in Psychology)
and the practical guide in Suárez-Álvarez et al. (2026, Psicothema).

Method:
1. Embed items via OpenAI (text-embedding-3-large by default for PFA quality).
2. Compute cosine similarity matrix → fill diagonal with 1.0 (treat as correlation).
3. Sign-flip embeddings for reverse-keyed items (DraftItem.polarity == "-").
4. Run EFA via factor-analyzer (oblimin rotation, is_corr_matrix=True).
5. Compute Tucker's congruence vs expected pattern matrix (one-hot from facets).
6. Compute factor recovery rate.
7. Apply 4-rule item retention check from Suárez-Álvarez et al. (2026):
    - Item loads on its parent factor (>= 0.30 absolute).
    - Loads higher on parent factor than on any other factor.
    - Parent loading > average of cross-loadings on other factors.
    - Parent loading > average of all other items' loadings on the parent factor.
8. Label factors via DAAL (Dominant Average Absolute Loading).
9. Compute model-free fit indices: RMSR (residual matrix RMS), CAF (common-part).
10. Emit a PFAResult.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Tuple

import numpy as np

from backend.agents.correlation_estimator import (
    compute_cosine_similarity_matrix,
    embed_items_sync,
)
from backend.schemas import (
    DraftItem,
    FacetMapperResponse,
    FactorLoading,
    PFAResult,
)
from backend.settings import settings

logger = logging.getLogger("lmaig.pfa_estimator")


# ----- Pure-NumPy psychometric helpers -----


def tuckers_congruence(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Per-column Tucker's congruence between loading matrices A and B.

    A, B: (n_items × n_factors). Returns array of length n_factors.
    Reference: Lorenzo-Seva & ten Berge (2006). >0.85 fair, >0.95 excellent.
    """
    if A.shape != B.shape:
        raise ValueError(f"Shape mismatch in tuckers_congruence: {A.shape} vs {B.shape}")
    num = (A * B).sum(axis=0)
    den = np.sqrt((A ** 2).sum(axis=0) * (B ** 2).sum(axis=0))
    return num / np.where(den == 0, 1.0, den)


def build_expected_pattern(
    expected_factor_assignments: Sequence[int],
    n_factors: int,
) -> np.ndarray:
    """Build a one-hot pattern matrix matching the expected factor structure.

    Returns: (n_items × n_factors) matrix with 1.0 on each item's parent factor.
    """
    n = len(expected_factor_assignments)
    pattern = np.zeros((n, n_factors), dtype=float)
    for i, f in enumerate(expected_factor_assignments):
        if 0 <= f < n_factors:
            pattern[i, f] = 1.0
    return pattern


def factor_recovery_rate(
    loadings: np.ndarray,
    expected_factor_assignments: Sequence[int],
    threshold: float = 0.30,
) -> Tuple[float, List[bool]]:
    """Compute factor recovery rate.

    A factor is "recovered" if its expected items have their max |loading|
    on that factor with magnitude >= threshold. Returns (rate, per_factor_flag).
    """
    n_factors = loadings.shape[1]
    if n_factors == 0:
        return 0.0, []

    abs_loadings = np.abs(loadings)
    primary_factor_per_item = np.argmax(abs_loadings, axis=1)
    primary_loading_per_item = abs_loadings.max(axis=1)

    recovered_flags: List[bool] = []
    for f in range(n_factors):
        expected_items = [
            i for i, e in enumerate(expected_factor_assignments) if e == f
        ]
        if not expected_items:
            recovered_flags.append(False)
            continue
        # Majority of expected items must load primarily on this factor with abs >= threshold
        hits = 0
        for i in expected_items:
            if (
                primary_factor_per_item[i] == f
                and primary_loading_per_item[i] >= threshold
            ):
                hits += 1
        recovered_flags.append(hits / len(expected_items) >= 0.5)

    rate = float(sum(recovered_flags) / len(recovered_flags))
    return rate, recovered_flags


def compute_retention_flags(
    loadings: np.ndarray,
    expected_factor_assignments: Sequence[int],
    parent_min_abs: float = 0.30,
) -> List[Tuple[bool, List[str]]]:
    """Apply the 4-rule retention check from Suárez-Álvarez et al. (2026).

    Returns list of (is_well_loaded, violation_names) per item.
    """
    abs_loadings = np.abs(loadings)
    n_items, n_factors = loadings.shape
    out: List[Tuple[bool, List[str]]] = []

    # Per-factor: average absolute loading across all items (used in rule 4)
    avg_per_factor_all_items = abs_loadings.mean(axis=0)

    for i in range(n_items):
        parent = (
            expected_factor_assignments[i]
            if 0 <= expected_factor_assignments[i] < n_factors
            else 0
        )
        parent_loading = abs_loadings[i, parent]
        violations: List[str] = []

        # Rule 1: Loads on parent factor at all (above minimum)
        if parent_loading < parent_min_abs:
            violations.append("rule1_below_parent_minimum")

        # Rule 2: Higher on parent than any other factor
        other_max = np.max(np.delete(abs_loadings[i, :], parent)) if n_factors > 1 else 0.0
        if parent_loading <= other_max:
            violations.append("rule2_cross_loading_dominates")

        # Rule 3: Parent loading > mean of cross-loadings (avg of other factors for this item)
        if n_factors > 1:
            mean_others_for_item = float(np.mean(np.delete(abs_loadings[i, :], parent)))
            if parent_loading <= mean_others_for_item:
                violations.append("rule3_below_mean_cross_loadings")

        # Rule 4: Parent loading > average of all other items' loadings on parent factor
        if n_items > 1:
            other_items_on_parent = np.delete(abs_loadings[:, parent], i)
            mean_others_on_parent = float(np.mean(other_items_on_parent))
            if parent_loading <= mean_others_on_parent:
                violations.append("rule4_below_avg_items_on_factor")

        is_well_loaded = len(violations) == 0
        out.append((is_well_loaded, violations))

    return out


def label_factors_via_daal(
    loadings: np.ndarray,
    expected_factor_assignments: Sequence[int],
    facet_labels: Optional[List[str]] = None,
) -> List[str]:
    """Label factors via Dominant Average Absolute Loading.

    For each factor, compute average |loading| of items expected to belong to
    each facet group; factor is labeled with the facet that has the highest avg.
    """
    n_factors = loadings.shape[1]
    if n_factors == 0:
        return []

    abs_loadings = np.abs(loadings)

    # Build groups: facet_idx -> list of item indices expected to belong
    n_facets = max(expected_factor_assignments) + 1 if expected_factor_assignments else n_factors
    facet_groups: dict[int, List[int]] = {f: [] for f in range(n_facets)}
    for i, f in enumerate(expected_factor_assignments):
        if 0 <= f < n_facets:
            facet_groups[f].append(i)

    labels: List[str] = []
    used_facets: set[int] = set()
    for fac in range(n_factors):
        # For this factor column, compute avg |loading| of each facet group
        best_facet = -1
        best_score = -1.0
        for facet_idx, item_ids in facet_groups.items():
            if not item_ids or facet_idx in used_facets:
                continue
            score = float(abs_loadings[item_ids, fac].mean())
            if score > best_score:
                best_score = score
                best_facet = facet_idx
        if best_facet >= 0:
            label = (
                facet_labels[best_facet]
                if facet_labels and best_facet < len(facet_labels)
                else f"Factor {fac + 1}"
            )
            labels.append(label)
            used_facets.add(best_facet)
        else:
            labels.append(f"Factor {fac + 1}")
    return labels


def compute_model_fit(
    sim_matrix: np.ndarray,
    loadings: np.ndarray,
) -> Tuple[float, float, np.ndarray]:
    """Compute RMSR and CAF model-free fit indices.

    RMSR (Root Mean Square Residual): RMS of (sim - loadings @ loadings.T) off-diagonal.
    CAF (Common part Accounted For): 1 - sum(residual_off_diag^2) / sum(sim_off_diag^2).

    Returns (rmsr, caf, residual_matrix).
    """
    reproduced = loadings @ loadings.T
    residual = sim_matrix - reproduced
    np.fill_diagonal(residual, 0.0)

    n = residual.shape[0]
    if n < 2:
        return 0.0, 1.0, residual

    # Use upper triangle only (symmetric matrix; avoid double-counting)
    iu = np.triu_indices(n, k=1)
    res_off = residual[iu]
    sim_off = sim_matrix[iu].copy()
    np.fill_diagonal(sim_matrix, 1.0)  # restore diagonal; sim_off uses off-diagonal anyway

    rmsr = float(np.sqrt(np.mean(res_off ** 2)))

    sim_var = float(np.sum(sim_off ** 2))
    caf = float(1.0 - np.sum(res_off ** 2) / sim_var) if sim_var > 0 else 1.0
    caf = max(0.0, min(1.0, caf))

    return rmsr, caf, residual


# ----- Main estimator -----


def _align_factor_signs(loadings: np.ndarray) -> Tuple[np.ndarray, List[bool]]:
    """Reflect each factor column so its dominant loading is positive.

    Factor analysis has sign indeterminacy: F and -F are equivalent solutions
    (Mulaik, 2010, Foundations of Factor Analysis, ch. 7). Convention from
    Lorenzo-Seva & ten Berge (2006, Methodology, 2(2), 57-64): reflect each
    factor so the loading with greatest absolute magnitude is positive. This
    matches the convention used by SPSS, lavaan, Mplus, and Procrustes target
    rotation, and ensures Tucker's congruence is computed against the
    correctly-oriented factor.

    Without this step, oblimin (used by `factor-analyzer`) can converge to a
    solution where all loadings on a factor are negative — mathematically
    equivalent but visually wrong: items measuring well-being would appear to
    "load negatively" on the well-being factor, and Tucker's congruence
    against a one-hot expected pattern would come back at -0.998 instead of
    +0.998.

    Returns:
        (aligned_loadings, was_flipped_per_factor)
    """
    aligned = loadings.copy()
    n_factors = aligned.shape[1]
    flipped: List[bool] = []
    for j in range(n_factors):
        col = aligned[:, j]
        if col.size == 0:
            flipped.append(False)
            continue
        dominant_idx = int(np.argmax(np.abs(col)))
        dominant_value = float(col[dominant_idx])
        if dominant_value < 0:
            aligned[:, j] = -col
            flipped.append(True)
        else:
            flipped.append(False)
    return aligned, flipped


def _decide_verdict(
    rmsr: float,
    recovery: float,
    mean_abs_congruence: float = 0.0,
) -> str:
    """Decide overall fit verdict.

    Considers RMSR (lower=better), factor recovery rate (higher=better), and
    mean absolute Tucker's congruence (higher=better). Tucker's congruence is
    used as |x| because the sign carries no fit information per Lorenzo-Seva &
    ten Berge (2006) §3 — it only encodes factor orientation, which is
    arbitrary up to a reflection.
    """
    excellent_congruence = mean_abs_congruence >= settings.PFA_TUCKERS_THRESHOLD_EXCELLENT
    fair_congruence = mean_abs_congruence >= settings.PFA_TUCKERS_THRESHOLD_FAIR
    good_rmsr = rmsr < settings.PFA_RMSR_GOOD
    good_recovery = recovery >= settings.PFA_RECOVERY_GOOD
    acceptable_recovery = recovery >= settings.PFA_RECOVERY_ACCEPTABLE

    if good_rmsr and good_recovery and (excellent_congruence or mean_abs_congruence == 0.0):
        return "good"
    if acceptable_recovery and (fair_congruence or mean_abs_congruence == 0.0):
        return "acceptable"
    return "poor"


def _compute_identifiability(n_items: int, n_factors: int) -> str:
    """Return 'saturated' / 'identified' / 'over_identified' for the EFA model.

    Degrees of freedom for EFA on a correlation matrix:
        dof = (p*(p-1)/2) - (p*k - k*(k-1)/2)
    where p = n_items, k = n_factors. dof <= 0 means the model is at least
    just-identified (saturated when dof = 0; under-identified when dof < 0).
    Fit indices like RMSR are uninformative when dof <= 0 because the model
    perfectly reproduces the correlation matrix by construction.
    """
    p = max(int(n_items), 0)
    k = max(int(n_factors), 0)
    if p < 2 or k < 1:
        return "saturated"
    unique_correlations = p * (p - 1) // 2
    free_loadings = p * k - k * (k - 1) // 2
    dof = unique_correlations - free_loadings
    if dof <= 0:
        return "saturated"
    if dof == 1:
        return "identified"
    return "over_identified"


def _facet_assignments_from_mapping(
    items: List[DraftItem],
    facet_mapping: Optional[FacetMapperResponse],
) -> Tuple[List[int], List[str]]:
    """Convert items + facet mapping into expected factor assignments + facet labels.

    Returns (assignments, labels). If no facet_mapping, assigns all items to factor 0.
    """
    if not facet_mapping or not facet_mapping.facets:
        return [0] * len(items), ["Single Factor"]

    facet_names = [f.facet_name for f in facet_mapping.facets]
    name_to_idx = {n: i for i, n in enumerate(facet_names)}

    assignments: List[int] = []
    for item in items:
        idx = name_to_idx.get(item.facet_name or "", 0)
        assignments.append(idx)
    return assignments, facet_names


def run_pfa(
    items: List[DraftItem],
    facet_mapping: Optional[FacetMapperResponse] = None,
    n_factors: Optional[int] = None,
    embedding_model: Optional[str] = None,
    items_dropped: Optional[List[int]] = None,
) -> PFAResult:
    """Run PFA on a list of items.

    Args:
        items: Items to analyze (must have item_text and ideally facet_name).
        facet_mapping: Used to derive expected factor assignments and labels.
        n_factors: Number of factors. Defaults to len(facet_mapping.facets) or 1.
        embedding_model: OpenAI embedding model. Defaults to settings.PFA_EMBEDDING_MODEL.
        items_dropped: Original-set indices that were dropped during pruning (passed through).

    Returns:
        PFAResult with loadings, congruence, recovery, fit indices.
    """
    if len(items) < 3:
        # PFA needs at least 3 items. Return a minimal PFAResult signalling unfit.
        logger.warning("PFA skipped: only %d items (minimum 3)", len(items))
        return PFAResult(
            embedding_model=embedding_model or settings.PFA_EMBEDDING_MODEL,
            n_items=len(items),
            n_factors=1,
            factor_labels=["Single Factor"],
            loadings=[],
            tuckers_congruence=[],
            factor_recovery_rate=0.0,
            rmsr=0.0,
            caf=0.0,
            eigenvalues=[],
            residual_correlation_matrix=[],
            items_dropped=items_dropped or [],
            fit_verdict="poor",
            model_identifiability="saturated",
        )

    embedding_model = embedding_model or settings.PFA_EMBEDDING_MODEL
    expected_assignments, facet_labels = _facet_assignments_from_mapping(items, facet_mapping)
    if n_factors is None:
        n_factors = max(1, len(facet_labels))
    # Cap n_factors to len(items)-1 (math constraint)
    n_factors = max(1, min(n_factors, len(items) - 1))

    item_texts = [it.item_text for it in items]
    polarities = [1.0 if (it.polarity or "+") == "+" else -1.0 for it in items]

    logger.info(
        "PFA start n_items=%d n_factors=%d model=%s reverse_coded=%d",
        len(items), n_factors, embedding_model,
        sum(1 for p in polarities if p < 0),
    )

    # 1-2. Embed and apply polarity sign-flip
    try:
        embeddings = embed_items_sync(item_texts, model=embedding_model)
    except Exception as e:
        logger.error("PFA embedding failed: %s", e, exc_info=True)
        return PFAResult(
            embedding_model=embedding_model,
            n_items=len(items),
            n_factors=n_factors,
            factor_labels=facet_labels[:n_factors],
            loadings=[],
            tuckers_congruence=[],
            factor_recovery_rate=0.0,
            rmsr=0.0,
            caf=0.0,
            eigenvalues=[],
            residual_correlation_matrix=[],
            items_dropped=items_dropped or [],
            fit_verdict="poor",
            model_identifiability=_compute_identifiability(len(items), n_factors),
        )

    logger.info(
        "PFA_EMBED items=%d dims=%d model=%s reverse_coded=%d",
        len(items), int(embeddings.shape[1]), embedding_model,
        sum(1 for p in polarities if p < 0),
    )

    polarity_arr = np.array(polarities).reshape(-1, 1)
    embeddings = embeddings * polarity_arr

    # 3. Cosine similarity → diagonal = 1
    sim = compute_cosine_similarity_matrix(embeddings)
    np.fill_diagonal(sim, 1.0)

    # Log off-diagonal stats — useful for diagnosing degenerate inputs
    iu = np.triu_indices(sim.shape[0], k=1)
    if iu[0].size > 0:
        off_diag = sim[iu]
        logger.info(
            "PFA_COSINE_MATRIX off_diag_min=%.3f off_diag_max=%.3f off_diag_mean=%.3f n=%d",
            float(off_diag.min()), float(off_diag.max()),
            float(off_diag.mean()), int(off_diag.size),
        )

    # 4. EFA via factor-analyzer
    # Workaround for factor-analyzer ↔ scikit-learn 1.8+ incompatibility:
    # FactorAnalyzer calls sklearn.utils.validation.check_array with the
    # deprecated `force_all_finite` kwarg, which was renamed to
    # `ensure_all_finite`. We shim check_array to translate the kwarg.
    try:
        import sklearn.utils.validation as _sk_validation
        if not getattr(_sk_validation, "_pfa_check_array_patched", False):
            _orig_check_array = _sk_validation.check_array

            def _patched_check_array(*args, **kwargs):
                if "force_all_finite" in kwargs and "ensure_all_finite" not in kwargs:
                    kwargs["ensure_all_finite"] = kwargs.pop("force_all_finite")
                return _orig_check_array(*args, **kwargs)

            _sk_validation.check_array = _patched_check_array
            _sk_validation._pfa_check_array_patched = True
            # Also patch other modules that may have imported it directly
            try:
                import factor_analyzer.factor_analyzer as _fa_mod
                if hasattr(_fa_mod, "check_array"):
                    _fa_mod.check_array = _patched_check_array
            except Exception:
                pass
    except Exception:
        pass

    solver_used = "factor_analyzer:oblimin"
    try:
        from factor_analyzer import FactorAnalyzer

        # Use oblimin (oblique) — preferred for psychological constructs
        # is_corr_matrix=True tells FA to treat input as correlation matrix
        fa = FactorAnalyzer(n_factors=n_factors, rotation="oblimin", is_corr_matrix=True)
        fa.fit(sim)
        loadings = np.asarray(fa.loadings_)
        eigenvalues, _ = fa.get_eigenvalues()
        eigenvalues = np.asarray(eigenvalues, dtype=float).tolist()
        logger.info(
            "PFA_EFA_SOLVER chosen=factor_analyzer rotation=oblimin n_factors=%d",
            n_factors,
        )
    except Exception as e:
        logger.error("PFA FactorAnalyzer fit failed: %s", e, exc_info=True)
        solver_used = "svd_fallback"
        # Fall back to PCA via SVD
        try:
            U, S, Vt = np.linalg.svd(sim)
            # Take top n_factors components scaled by sqrt(eigenvalue) → loadings
            loadings = U[:, :n_factors] * np.sqrt(np.abs(S[:n_factors]))
            eigenvalues = S.tolist()
            logger.warning(
                "PFA_EFA_SOLVER chosen=svd_fallback reason=%s",
                type(e).__name__,
            )
        except Exception as e2:
            logger.error("PFA SVD fallback failed: %s", e2)
            return PFAResult(
                embedding_model=embedding_model,
                n_items=len(items),
                n_factors=n_factors,
                factor_labels=facet_labels[:n_factors],
                loadings=[],
                tuckers_congruence=[],
                factor_recovery_rate=0.0,
                rmsr=0.0,
                caf=0.0,
                eigenvalues=[],
                residual_correlation_matrix=[],
                items_dropped=items_dropped or [],
                fit_verdict="poor",
                model_identifiability=_compute_identifiability(len(items), n_factors),
            )

    # 4b. Log raw (pre-alignment) loadings stats per factor — useful for
    # forensic analysis when a run produces unexpected results.
    for j in range(loadings.shape[1]):
        col_raw = loadings[:, j]
        logger.info(
            "PFA_LOADINGS_RAW factor=%d min=%.3f max=%.3f mean=%.3f sum=%.3f",
            j,
            float(col_raw.min()),
            float(col_raw.max()),
            float(col_raw.mean()),
            float(col_raw.sum()),
        )

    # 4c. Sign-align factor columns. Without this, oblimin can converge to a
    # solution where loadings on a factor are all-negative — equivalent up to
    # reflection but visually wrong (Mulaik 2010 ch. 7; Lorenzo-Seva &
    # ten Berge 2006). Convention: dominant loading must be positive.
    loadings, sign_flips = _align_factor_signs(loadings)
    for j, was_flipped in enumerate(sign_flips):
        col_aligned = loadings[:, j]
        dom_idx = int(np.argmax(np.abs(col_aligned))) if col_aligned.size else -1
        dom_val = float(col_aligned[dom_idx]) if dom_idx >= 0 else 0.0
        logger.info(
            "PFA_SIGN_ALIGNMENT factor=%d flipped=%s dominant_idx=%d dominant_value=%.3f",
            j, was_flipped, dom_idx, dom_val,
        )

    # 5. Tucker's congruence vs expected pattern (one-hot). Sign should now be
    # naturally positive after alignment, but we still take abs() in the
    # verdict band as a defensive safety net (per Lorenzo-Seva & ten Berge
    # 2006 §3, only the magnitude carries fit information).
    expected_pattern = build_expected_pattern(expected_assignments, n_factors)
    congruence = tuckers_congruence(loadings, expected_pattern).tolist()
    for j, c in enumerate(congruence):
        abs_c = abs(c)
        if abs_c >= settings.PFA_TUCKERS_THRESHOLD_EXCELLENT:
            band = "excellent"
        elif abs_c >= settings.PFA_TUCKERS_THRESHOLD_FAIR:
            band = "fair"
        else:
            band = "below_threshold"
        logger.info(
            "PFA_TUCKER factor=%d signed=%.3f abs=%.3f band=%s",
            j, c, abs_c, band,
        )

    # 6. Factor recovery rate
    recovery, _ = factor_recovery_rate(loadings, expected_assignments)

    # 7. 4-rule retention check
    retention = compute_retention_flags(loadings, expected_assignments)
    n_well_loaded = sum(1 for is_ok, _ in retention if is_ok)
    logger.info(
        "PFA_RETENTION well_loaded=%d/%d", n_well_loaded, len(retention),
    )

    # 8. DAAL labels
    daal_labels = label_factors_via_daal(loadings, expected_assignments, facet_labels)

    # 9. Fit indices
    rmsr, caf, residual = compute_model_fit(sim, loadings)

    # Build per-item FactorLoading entries
    abs_loadings = np.abs(loadings)
    primary_factors = np.argmax(abs_loadings, axis=1)
    primary_loadings = abs_loadings.max(axis=1)
    factor_loadings: List[FactorLoading] = []
    for i, item in enumerate(items):
        is_well_loaded, violations = retention[i]
        factor_loadings.append(
            FactorLoading(
                item_index=i,
                item_text=item.item_text,
                facet_name=item.facet_name,
                loadings=[float(x) for x in loadings[i].tolist()],
                parent_factor=int(expected_assignments[i]),
                primary_loading=float(primary_loadings[i]),
                primary_factor=int(primary_factors[i]),
                is_well_loaded=is_well_loaded,
                retention_rule_violations=violations,
            )
        )

    identifiability = _compute_identifiability(len(items), n_factors)
    mean_abs_congruence = (
        float(np.mean([abs(c) for c in congruence])) if congruence else 0.0
    )
    verdict = _decide_verdict(rmsr, recovery, mean_abs_congruence=mean_abs_congruence)

    # When the model is saturated, RMSR=0 and CAF=1 trivially — fit_verdict
    # of "good" would be misleading. Downgrade verdict to acknowledge that
    # the structural fit cannot be evaluated.
    if identifiability == "saturated":
        # Don't claim "good" when we have no degrees of freedom
        if verdict == "good":
            verdict = "acceptable"

    # Build a dynamic disclaimer that reflects the saturation case
    if identifiability == "saturated":
        disclaimer = (
            "Model is saturated: with this few items, the EFA reproduces the "
            "correlation matrix exactly (RMSR=0 / CAF=1 by construction). Fit "
            "indices are uninformative; loadings remain interpretable. "
            "Add more items per factor for diagnostic fit."
        )
    else:
        disclaimer = (
            "Pseudo-Factor Analysis on sentence-embedding cosine similarity "
            "(Varrasi et al., 2026). Pre-calibration heuristic; not a substitute "
            "for empirical EFA on respondent data."
        )

    logger.info(
        "PFA_VERDICT solver=%s n_factors=%d recovery=%.3f rmsr=%.3f caf=%.3f "
        "mean_abs_congruence=%.3f congruence=%s verdict=%s identifiability=%s",
        solver_used, n_factors, recovery, rmsr, caf,
        mean_abs_congruence,
        [round(c, 3) for c in congruence], verdict, identifiability,
    )

    return PFAResult(
        embedding_model=embedding_model,
        n_items=len(items),
        n_factors=n_factors,
        factor_labels=daal_labels,
        loadings=factor_loadings,
        tuckers_congruence=congruence,
        factor_recovery_rate=float(recovery),
        rmsr=float(rmsr),
        caf=float(caf),
        eigenvalues=[float(e) for e in eigenvalues[:n_factors]] if eigenvalues else [],
        residual_correlation_matrix=[
            [round(float(residual[i, j]), 4) for j in range(residual.shape[1])]
            for i in range(residual.shape[0])
        ],
        items_dropped=items_dropped or [],
        fit_verdict=verdict,  # type: ignore[arg-type]
        model_identifiability=identifiability,  # type: ignore[arg-type]
        disclaimer=disclaimer,
    )
