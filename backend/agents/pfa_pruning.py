"""PFA-based item pruning.

Iteratively removes weakly-loaded items from an over-generated pool until either
target_count is reached or all remaining items load cleanly per the 4-rule
retention check (Suárez-Álvarez et al., 2026).

Hard constraints:
- For multi-dimensional constructs, never drop the last remaining item of any
  facet (preserves facet coverage). For unidimensional constructs (a single
  facet) this rule is uninformative and is bypassed.
- Cap iterations at PFA_PRUNING_MAX_ITERS to bound cost.
- Optional time-budget guard to break the loop when the Vercel budget runs low.
"""

from __future__ import annotations

import logging
import time as _time
from typing import List, Optional, Tuple

from backend.agents.pfa_estimator import run_pfa
from backend.schemas import DraftItem, FacetMapperResponse, PFAResult
from backend.settings import settings

logger = logging.getLogger("lmaig.pfa_pruning")


def _facet_counts(items: List[DraftItem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for it in items:
        key = it.facet_name or ""
        counts[key] = counts.get(key, 0) + 1
    return counts


def prune_items(
    items: List[DraftItem],
    facet_mapping: Optional[FacetMapperResponse],
    target_count: int,
    max_iters: Optional[int] = None,
    deadline: Optional[float] = None,
) -> Tuple[List[DraftItem], List[int], PFAResult]:
    """Iteratively prune items via PFA until target_count reached or all clean.

    Args:
        items: Over-generated pool of items.
        facet_mapping: Used by PFA to derive expected factor structure + labels.
        target_count: Desired final count.
        max_iters: Override settings.PFA_PRUNING_MAX_ITERS for testing.
        deadline: Optional Unix timestamp (time.time() + budget) after which
            the loop must stop to preserve the Vercel budget for downstream
            steps. Configured by `settings.PFA_PRUNING_MIN_REMAINING_SECS`
            on the caller side.

    Returns:
        (kept_items, dropped_original_indices, final_pfa_result).
    """
    # Pruning budget should be at least enough to reach the target (each iter drops 1 item).
    # Use settings.PFA_PRUNING_MAX_ITERS as a floor; if we have more excess than that,
    # raise the cap so we don't stop prematurely.
    if max_iters is None:
        max_iters = max(settings.PFA_PRUNING_MAX_ITERS, len(items) - target_count + 2)

    # For unidimensional constructs the "≥1 item per facet" rule reduces to
    # "keep at least one item total" — uninformative and overly restrictive
    # when items have inconsistent facet_name values from the regen path.
    # Bypass the constraint so pruning can always drop the weakest item.
    is_unidimensional = bool(
        facet_mapping is not None
        and getattr(facet_mapping, "is_unidimensional", False)
    )

    if len(items) <= target_count:
        logger.info(
            "PFA pruning skipped: have %d items, target=%d (already at or below target)",
            len(items), target_count,
        )
        result = run_pfa(items, facet_mapping=facet_mapping)
        return items, [], result

    # Track original indices so we can report what was dropped relative to the input list
    current = list(items)
    original_index_of: List[int] = list(range(len(items)))
    dropped_original_indices: List[int] = []

    last_result: Optional[PFAResult] = None

    for iteration in range(max_iters):
        if len(current) <= target_count:
            logger.info("PFA pruning hit target_count=%d at iteration=%d", target_count, iteration)
            break

        # Time-budget guard: stop pruning if we've eaten into the finalize budget.
        if deadline is not None:
            remaining = deadline - _time.time()
            if remaining < settings.PFA_PRUNING_MIN_REMAINING_SECS:
                logger.warning(
                    "PFA_PRUNING_BUDGET remaining=%.0fs (<%ds) — stopping pruning at iteration=%d "
                    "to preserve finalize budget. kept=%d target=%d",
                    remaining, settings.PFA_PRUNING_MIN_REMAINING_SECS,
                    iteration, len(current), target_count,
                )
                break

        result = run_pfa(current, facet_mapping=facet_mapping)
        last_result = result

        if not result.loadings:
            logger.warning("PFA pruning: PFA returned no loadings; aborting prune loop")
            break

        # Prefer items that fail retention checks; if none, fall back to weakest-loaded.
        # Continuing to drop until target_count is reached even when remaining items
        # all "load cleanly" — the user requested a specific count.
        weak = [fl for fl in result.loadings if not fl.is_well_loaded]
        if weak:
            candidates = weak
        else:
            # All items load cleanly but we still need to prune to target.
            # Drop the lowest primary_loading item.
            candidates = list(result.loadings)
            logger.info(
                "PFA pruning iter=%d: all items load cleanly, dropping weakest by primary_loading",
                iteration,
            )

        # Sort weakest first
        candidates.sort(key=lambda fl: fl.primary_loading)

        # Facet-preservation: only enforce for multi-dimensional constructs.
        # Unidimensional constructs have a single facet, so the rule reduces
        # to "keep ≥ 1 item total" which is uninformative and was blocking
        # valid drops when regen-replaced items had inconsistent facet_name.
        item_to_drop_idx: Optional[int] = None
        if is_unidimensional:
            # No facet check — drop the weakest candidate.
            item_to_drop_idx = candidates[0].item_index
        else:
            facet_counts = _facet_counts(current)
            for cand in candidates:
                facet_key = cand.facet_name or ""
                if facet_counts.get(facet_key, 0) > 1:
                    item_to_drop_idx = cand.item_index
                    break
                else:
                    logger.warning(
                        "PFA pruning: would drop weak item idx=%d facet=%s, but it's the last "
                        "remaining for that facet — skipping (facet preservation constraint).",
                        cand.item_index, facet_key,
                    )

        if item_to_drop_idx is None:
            logger.info(
                "PFA pruning: no droppable candidates (all weak items are the last in their facet). Stopping."
            )
            break

        dropped_original_indices.append(original_index_of[item_to_drop_idx])
        del current[item_to_drop_idx]
        del original_index_of[item_to_drop_idx]

        logger.info(
            "PFA pruning iter=%d dropped_idx_in_pool=%d remaining=%d",
            iteration, item_to_drop_idx, len(current),
        )

    # Final PFA pass on remaining set so we report correct loadings + verdict
    final_result = run_pfa(
        current,
        facet_mapping=facet_mapping,
        items_dropped=dropped_original_indices,
    )

    logger.info(
        "PFA pruning complete: kept=%d dropped=%d verdict=%s recovery=%.3f rmsr=%.3f",
        len(current), len(dropped_original_indices),
        final_result.fit_verdict, final_result.factor_recovery_rate, final_result.rmsr,
    )

    return current, dropped_original_indices, final_result
