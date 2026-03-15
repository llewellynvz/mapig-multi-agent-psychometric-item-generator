"""McDonald's omega calculator.

Implements CORR-02 and CORR-06 requirements.

Direct implementation using the simplified omega formula for equally weighted items:
omega = (k * r_bar) / (1 + (k - 1) * r_bar)

Where:
- k = number of items
- r_bar = mean inter-item correlation

This is equivalent to Cronbach's alpha for tau-equivalent items (equal factor loadings).
For Phase 8, this approximation is acceptable for LLM-estimated correlations.
"""

import logging
import numpy as np
from typing import Dict, List, Optional

logger = logging.getLogger("lmaig")


def calculate_omega(cells: List, num_items: int) -> Dict[str, Optional[float]]:
    """Calculate McDonald's omega from correlation matrix cells.

    Uses simplified omega formula for equally weighted items:
    omega = (k * r_bar) / (1 + (k - 1) * r_bar)

    Args:
        cells: List of CorrelationCell objects (upper-triangular pairwise correlations)
        num_items: Number of items in the scale

    Returns:
        Dict with:
            - omega_total: McDonald's omega (0.0-1.0) or None if calculation failed
            - mean_inter_item_correlation: Mean of all pairwise correlations
            - internal_consistency_flag: "optimal_range" (0.15-0.50), "too_low" (<0.15), "too_high" (>0.50), or "calculation_failed"
    """
    try:
        # Build symmetric NxN correlation matrix from flat cells list
        matrix = np.eye(num_items)  # Start with identity (diagonal = 1.0)

        for cell in cells:
            i = cell.item_i_index
            j = cell.item_j_index
            r = cell.correlation

            # Fill both upper and lower triangular (symmetric)
            matrix[i, j] = r
            matrix[j, i] = r

        # Calculate mean inter-item correlation (exclude diagonal)
        off_diagonal = []
        for i in range(num_items):
            for j in range(i + 1, num_items):
                off_diagonal.append(matrix[i, j])

        mean_r = np.mean(off_diagonal) if off_diagonal else 0.0

        # Determine internal consistency flag and guidance based on mean r (CORR-06)
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

        # Calculate McDonald's omega using simplified formula
        # omega = (k * r_bar) / (1 + (k - 1) * r_bar)
        # This is equivalent to Cronbach's alpha for tau-equivalent items
        k = num_items
        r_bar = mean_r

        if r_bar < -1.0 / (k - 1):
            # Edge case: mean correlation too negative for valid omega
            logger.warning(f"Mean correlation {r_bar:.3f} too negative for {k} items. Omega undefined.")
            return {
                "omega_total": None,
                "mean_inter_item_correlation": float(mean_r),
                "internal_consistency_flag": "calculation_failed",
                "guidance": "Omega calculation failed due to negative mean correlation. Items may not form a coherent scale.",
            }

        omega_total = (k * r_bar) / (1 + (k - 1) * r_bar)

        # Clamp omega to [0.0, 1.0] range (should be automatic, but ensure)
        omega_total = max(0.0, min(1.0, omega_total))

        logger.info(f"Omega calculation successful: omega={omega_total:.3f}, mean_r={mean_r:.3f}, flag={flag}")

        return {
            "omega_total": float(omega_total),
            "mean_inter_item_correlation": float(mean_r),
            "internal_consistency_flag": flag,
            "guidance": guidance,
        }

    except Exception as e:
        logger.error(f"Omega calculation error: {e}")
        return {
            "omega_total": None,
            "mean_inter_item_correlation": 0.0,
            "internal_consistency_flag": "calculation_failed",
            "guidance": f"Omega calculation error: {e}",
        }
