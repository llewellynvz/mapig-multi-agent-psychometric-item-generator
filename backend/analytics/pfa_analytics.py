"""Post-finalization PFA analytics.

Wrapper called from `analytics_dispatch_node` to compute the final
factor-structure report shown in the UI's PFAPanel. Runs PFA on the
*post-prune* item set (the user-visible final set) and reports loadings,
Tucker's congruence, fit indices.

This is distinct from `pfa_pruning_node`, which uses PFA to *select* items.
This module only *reports* what the final structure looks like.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from backend.agents.pfa_estimator import run_pfa
from backend.schemas import DraftItem, FacetMapperResponse, PFAResult

logger = logging.getLogger("lmaig.pfa_analytics")


def compute_pfa_analytics(
    final_items: List[DraftItem],
    facet_mapping: Optional[FacetMapperResponse] = None,
    items_dropped: Optional[List[int]] = None,
) -> PFAResult:
    """Compute the post-finalization PFA report for the UI.

    Args:
        final_items: Final user-visible items (post-prune).
        facet_mapping: Used by PFA for expected factor structure + DAAL labels.
        items_dropped: Indices of items dropped during pruning (passed through
            so the UI can display "n items dropped during PFA pruning").

    Returns:
        PFAResult with loadings, congruence, fit indices.
    """
    if len(final_items) < 3:
        logger.info("PFA analytics skipped: only %d items (minimum 3 for FA)", len(final_items))
        return PFAResult(
            embedding_model="(skipped — too few items)",
            n_items=len(final_items),
            n_factors=1,
            factor_labels=["Single Factor"],
            loadings=[],
            tuckers_congruence=[],
            factor_recovery_rate=None,
            rmsr=None,
            caf=None,
            eigenvalues=[],
            residual_correlation_matrix=[],
            items_dropped=items_dropped or [],
            fit_verdict="not_estimable",
        )

    return run_pfa(
        final_items,
        facet_mapping=facet_mapping,
        items_dropped=items_dropped,
    )
