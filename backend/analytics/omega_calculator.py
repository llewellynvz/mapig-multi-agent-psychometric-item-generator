"""Pseudo-alpha calculator (standardized Cronbach's alpha on semantic similarity).

Computes the standardized-alpha formula
    alpha = (k * r_bar) / (1 + (k - 1) * r_bar)
where k = number of items and r_bar = the mean off-diagonal embedding cosine
similarity, treated as a pseudo inter-item correlation (Hommel & Arslan, 2024).

This is NOT McDonald's omega (which requires factor loadings and error
variances) and NOT respondent-based reliability. It is a pre-data semantic
estimate — a heuristic for triaging item pools before any human data exists.
A loading-based pseudo-omega is reported separately from the PFA solution.
"""

import logging
import numpy as np
from typing import Dict, List, Optional

logger = logging.getLogger("lmaig")


def calculate_pseudo_alpha(cells: List, num_items: int) -> Dict[str, Optional[float]]:
    """Calculate pseudo-alpha from semantic-similarity matrix cells.

    Args:
        cells: List of CorrelationCell objects (upper-triangular pairwise
            embedding cosine similarities).
        num_items: Number of items in the scale.

    Returns:
        Dict with:
            - pseudo_alpha: standardized alpha on the semantic matrix, or None
              when not estimable. NOT clamped — a negative value is reported
              as-is because it signals a degenerate (incoherent) item set.
            - mean_inter_item_correlation: mean pairwise cosine similarity.
            - internal_consistency_flag: "optimal_range" (0.15-0.50),
              "too_low" (<0.15), "too_high" (>0.50), or "calculation_failed".
            - guidance: interpretation text.
    """
    try:
        # Build symmetric NxN similarity matrix from flat cells list
        matrix = np.eye(num_items)

        for cell in cells:
            i = cell.item_i_index
            j = cell.item_j_index
            r = cell.correlation

            matrix[i, j] = r
            matrix[j, i] = r

        off_diagonal = []
        for i in range(num_items):
            for j in range(i + 1, num_items):
                off_diagonal.append(matrix[i, j])

        mean_r = np.mean(off_diagonal) if off_diagonal else 0.0

        # Flag bands follow Clark & Watson (1995) mean inter-item r guidance,
        # applied heuristically to semantic similarity.
        if mean_r < 0.15:
            flag = "too_low"
            guidance = "Items may not measure the same construct consistently. Consider revising items for stronger construct alignment."
        elif mean_r > 0.50:
            flag = "too_high"
            guidance = (
                "Items may be measuring too narrow a facet (Clark & Watson, 1995 recommend .15-.50 mean inter-item r). "
                "Diversify item content across different facets of the construct."
            )
        else:
            flag = "optimal_range"
            guidance = "Within optimal range for mean inter-item correlation (Clark & Watson, 1995: .15-.50)."

        k = num_items
        r_bar = mean_r

        if k < 2:
            logger.warning("Pseudo-alpha undefined for a single item.")
            return {
                "pseudo_alpha": None,
                "mean_inter_item_correlation": mean_r,
                "internal_consistency_flag": "calculation_failed",
                "guidance": "Pseudo-alpha not estimable: fewer than 2 items.",
            }

        if r_bar <= -1.0 / (k - 1):
            # The equicorrelation matrix is not positive semi-definite here;
            # standardized alpha is undefined.
            logger.warning(f"Mean similarity {r_bar:.3f} too negative for {k} items. Pseudo-alpha undefined.")
            return {
                "pseudo_alpha": None,
                "mean_inter_item_correlation": float(mean_r),
                "internal_consistency_flag": "calculation_failed",
                "guidance": "Pseudo-alpha not estimable: mean similarity too negative. Items do not form a coherent scale.",
            }

        pseudo_alpha = (k * r_bar) / (1 + (k - 1) * r_bar)

        logger.info(f"Pseudo-alpha calculation successful: pseudo_alpha={pseudo_alpha:.3f}, mean_r={mean_r:.3f}, flag={flag}")

        return {
            "pseudo_alpha": float(pseudo_alpha),
            "mean_inter_item_correlation": float(mean_r),
            "internal_consistency_flag": flag,
            "guidance": guidance,
        }

    except Exception as e:
        logger.error(f"Pseudo-alpha calculation error: {e}")
        return {
            "pseudo_alpha": None,
            "mean_inter_item_correlation": 0.0,
            "internal_consistency_flag": "calculation_failed",
            "guidance": f"Pseudo-alpha calculation error: {e}",
        }
