"""Synthetic-respondent pilot: LLM-simulated raters produce a real N x k matrix.

Trait-response mediator design from the silicon-sampling literature: each
simulated respondent draws a latent trait level per facet (theta ~ N(0, Phi)),
an LLM answers every item in that respondent's voice, and classical statistics
run on the resulting matrix. The math downstream is valid because a real N
exists; the interpretive caveat is the data source, stated in the required
disclaimer. Flag-gated via settings.SYNTHETIC_PILOT_ENABLED.
"""

from __future__ import annotations

import concurrent.futures
import logging
import re
from typing import List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from backend.agents.llm_utils import TokenUsage, invoke_structured_with_usage
from backend.agents.prompt_loader import load_prompt
from backend.analytics.classical_stats import (
    bartlett_sphericity,
    cronbach_alpha,
    efa_omega,
    fisher_ci,
    kmo,
    parallel_analysis,
    pearson_matrix,
)
from backend.schemas import (
    CorrelationCell,
    DraftItem,
    SyntheticPilotResult,
    UserRequest,
)
from backend.settings import settings

logger = logging.getLogger("mapig.synthetic_respondents")

MAX_RESPONDENTS = 200


class _RespondentRating(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_index: int = Field(..., ge=0)
    rating: int = Field(..., ge=1, le=11)


class _RespondentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ratings: List[_RespondentRating] = Field(default_factory=list)


def _parse_scale_points(response_scale: str) -> int:
    """Extract the number of scale points from the user's free-text response
    scale (e.g. '5-point Likert', '1-7 agreement'). Falls back to 5."""
    match = re.search(r"(\d+)\s*[-–]?\s*point", response_scale, re.IGNORECASE)
    if not match:
        match = re.search(r"1\s*[-–]\s*(\d+)", response_scale)
    if match:
        return max(2, min(11, int(match.group(1))))
    return 5


def _draw_traits(
    n_respondents: int,
    n_facets: int,
    phi: Optional[np.ndarray],
    rng: np.random.Generator,
) -> np.ndarray:
    """Draw latent trait levels theta ~ N(0, Phi); identity when no Phi.

    Uses an eigendecomposition transform with negative eigenvalues clipped to
    zero, so a slightly non-PSD Phi never raises or warns."""
    raw = rng.standard_normal((n_respondents, n_facets))
    if phi is None or phi.shape != (n_facets, n_facets):
        return raw
    sym = (np.asarray(phi, dtype=float) + np.asarray(phi, dtype=float).T) / 2.0
    vals, vecs = np.linalg.eigh(sym)
    transform = vecs @ np.diag(np.sqrt(np.clip(vals, 0.0, None)))
    return raw @ transform.T


def _trait_level_label(z: float) -> str:
    if z < -1.5:
        return "very low"
    if z < -0.5:
        return "low"
    if z <= 0.5:
        return "average"
    if z <= 1.5:
        return "high"
    return "very high"


def _facet_index_for_item(item: DraftItem, facet_names: List[str]) -> int:
    if item.facet_name and item.facet_name in facet_names:
        return facet_names.index(item.facet_name)
    return 0


def _mock_ratings(
    items: List[DraftItem],
    facet_names: List[str],
    theta_row: np.ndarray,
    scale_points: int,
    rng: np.random.Generator,
) -> List[int]:
    """Deterministic simulated ratings: midpoint + trait signal + noise,
    polarity-aware. Produces a matrix with genuine facet structure so
    downstream statistics are exercised for real in mock mode."""
    midpoint = (scale_points + 1) / 2.0
    ratings = []
    for item in items:
        theta = theta_row[_facet_index_for_item(item, facet_names)]
        signed = -theta if item.polarity == "-" else theta
        value = midpoint + signed * (scale_points / 4.0) + rng.normal(0.0, 0.6)
        ratings.append(int(np.clip(round(value), 1, scale_points)))
    return ratings


def _rate_items_for_respondent(
    request: UserRequest,
    items: List[DraftItem],
    facet_names: List[str],
    theta_row: np.ndarray,
    scale_points: int,
) -> Tuple[_RespondentOutput, TokenUsage]:
    system = load_prompt("synthetic_respondent.md")
    trait_profile = [
        {
            "facet": name,
            "level": _trait_level_label(float(theta_row[i])),
            "z_score": round(float(theta_row[i]), 2),
        }
        for i, name in enumerate(facet_names)
    ]
    payload = {
        "construct_name": request.construct_name,
        "construct_definition": request.construct_definition,
        "response_scale": request.response_scale,
        "scale_points": scale_points,
        "trait_profile": trait_profile,
        "items": [
            {
                "item_index": i,
                "item_text": item.item_text,
                "facet": item.facet_name or facet_names[0],
                "polarity": item.polarity,
            }
            for i, item in enumerate(items)
        ],
    }
    human = (
        f"You are ONE respondent with this exact latent trait profile. Rate all "
        f"{len(items)} items on the {scale_points}-point scale described. "
        f"Anchor each rating on the trait level of the item's facet, respect "
        f"polarity, and vary ratings realistically (±1 point) across items of "
        f"the same facet.\n\nINPUT:\n{payload}"
    )
    return invoke_structured_with_usage(
        _RespondentOutput,
        [("system", system), ("human", human)],
        agent_name="synthetic_respondent",
        model_provider=request.model_provider,
    )


def _collect_matrix(
    request: UserRequest,
    items: List[DraftItem],
    facet_names: List[str],
    theta: np.ndarray,
    scale_points: int,
    seed: int,
) -> Tuple[np.ndarray, int, TokenUsage]:
    """Return (valid rows x items matrix, failed respondent count, usage)."""
    n_respondents = theta.shape[0]
    total_usage = TokenUsage(model_name="synthetic_respondent")

    if settings.APP_MODE == "mock":
        rng = np.random.default_rng(seed + 1)
        rows = [
            _mock_ratings(items, facet_names, theta[r], scale_points, rng)
            for r in range(n_respondents)
        ]
        return np.array(rows, dtype=float), 0, total_usage

    rows: List[Optional[List[int]]] = [None] * n_respondents

    def _one(r: int) -> Tuple[int, Optional[List[int]], TokenUsage]:
        try:
            output, usage = _rate_items_for_respondent(
                request, items, facet_names, theta[r], scale_points
            )
        except Exception as exc:
            logger.warning(
                "SYNTHETIC_RESPONDENT_FAIL respondent=%d error_type=%s",
                r, type(exc).__name__,
            )
            return r, None, TokenUsage()
        by_index = {
            rating.item_index: rating.rating
            for rating in output.ratings
            if 0 <= rating.item_index < len(items) and rating.rating <= scale_points
        }
        if len(by_index) != len(items):
            logger.warning(
                "SYNTHETIC_RESPONDENT_INCOMPLETE respondent=%d rated=%d expected=%d",
                r, len(by_index), len(items),
            )
            return r, None, usage
        return r, [by_index[i] for i in range(len(items))], usage

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for r, row, usage in executor.map(_one, range(n_respondents)):
            rows[r] = row
            total_usage.input_tokens += usage.input_tokens
            total_usage.output_tokens += usage.output_tokens
            total_usage.total_tokens += usage.total_tokens

    valid = [row for row in rows if row is not None]
    failed = n_respondents - len(valid)
    if not valid:
        return np.empty((0, len(items))), failed, total_usage
    return np.array(valid, dtype=float), failed, total_usage


def run_synthetic_pilot(
    request: UserRequest,
    items: List[DraftItem],
    facet_names: List[str],
    phi: Optional[np.ndarray] = None,
    n_respondents: int = 50,
    seed: int = 42,
) -> Tuple[Optional[SyntheticPilotResult], TokenUsage]:
    """Simulate a respondent pilot and compute classical statistics on it.

    Returns (None, usage) when no usable matrix could be produced. All
    statistics inside the result are None-honest: not estimable stays None.
    """
    if len(items) < 2 or n_respondents < 2:
        return None, TokenUsage()
    n_respondents = min(n_respondents, MAX_RESPONDENTS)
    if not facet_names:
        facet_names = [request.construct_name]

    scale_points = _parse_scale_points(request.response_scale)
    rng = np.random.default_rng(seed)
    theta = _draw_traits(n_respondents, len(facet_names), phi, rng)

    logger.info(
        "SYNTHETIC_PILOT start n_respondents=%d n_items=%d n_facets=%d scale_points=%d",
        n_respondents, len(items), len(facet_names), scale_points,
    )

    matrix, failed, usage = _collect_matrix(
        request, items, facet_names, theta, scale_points, seed
    )
    if matrix.shape[0] < 5:
        logger.warning(
            "SYNTHETIC_PILOT aborted: only %d valid respondents (need 5)",
            matrix.shape[0],
        )
        return None, usage

    n_valid = matrix.shape[0]
    corr = pearson_matrix(matrix)
    cells: List[CorrelationCell] = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            r_value = float(corr[i, j])
            if not np.isfinite(r_value):
                continue
            ci_low, ci_high = fisher_ci(r_value, n_valid)
            cells.append(
                CorrelationCell(
                    item_i_index=i,
                    item_j_index=j,
                    correlation=float(np.clip(r_value, -1.0, 1.0)),
                    ci_low=ci_low,
                    ci_high=ci_high,
                )
            )

    pa_n, observed_eigs, threshold_eigs = parallel_analysis(matrix, seed=seed)
    chi2, p_value = bartlett_sphericity(corr, n_valid)
    omega = efa_omega(matrix, n_factors=len(facet_names))
    alpha = cronbach_alpha(matrix)
    if alpha is not None:
        # IEEE-754 overshoot (e.g. 1.0000000000000007) violates the schema's le=1.0.
        alpha = min(1.0, alpha)

    result = SyntheticPilotResult(
        n_respondents=n_valid,
        n_items=len(items),
        model_name="mock" if settings.APP_MODE == "mock" else "synthetic_respondent",
        scale_points=scale_points,
        cells=cells,
        cronbach_alpha=alpha,
        omega_total=omega,
        parallel_analysis_n_factors=pa_n,
        observed_eigenvalues=observed_eigs,
        threshold_eigenvalues=threshold_eigs,
        kmo=kmo(corr),
        bartlett_chi2=chi2,
        bartlett_p=p_value,
        failed_respondents=failed,
    )
    logger.info(
        "SYNTHETIC_PILOT done n_valid=%d failed=%d alpha=%s pa_factors=%s",
        n_valid, failed,
        f"{result.cronbach_alpha:.3f}" if result.cronbach_alpha is not None else "None",
        result.parallel_analysis_n_factors,
    )
    return result, usage
