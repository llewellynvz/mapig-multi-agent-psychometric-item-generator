"""Near-duplicate item removal.

MAPIG's meta-editor only detects EXACT-string duplicates (it compares the count
of lowercased item texts before/after an edit pass). It does not catch
near-duplicates — synonym-level rewordings such as "I feel energised when I'm
working" vs "I feel energised while I'm working" — which the item writer emits
under overlapping facets (and which got *worse* with more evidence, since the
retrieved chunks pushed the writer toward a narrow set of safe phrasings).

This module drops near-duplicates (embedding cosine > threshold) before final
output. It is the fix for the "literal duplicate items" finding.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import numpy as np

from backend.schemas import DraftItem

logger = logging.getLogger("lmaig.deduplicator")

DEFAULT_DEDUP_THRESHOLD = 0.85


def deduplicate_items(
    items: List[DraftItem],
    threshold: float = DEFAULT_DEDUP_THRESHOLD,
    embedding_model: Optional[str] = None,
) -> Tuple[List[DraftItem], List[int]]:
    """Drop near-duplicate items, keeping the first occurrence of each cluster.

    Greedy single-pass clustering: an item is dropped if its embedding cosine
    similarity to any already-kept item exceeds ``threshold``. Deterministic and
    order-preserving. Falls back to exact-string (lowercased) dedup when
    embedding is unavailable.

    Args:
        items: Draft items to deduplicate.
        threshold: Cosine similarity at/above which two items are duplicates.
        embedding_model: Embedding model. Defaults to the active PFA model.

    Returns:
        (kept_items, dropped_indices) where dropped_indices are the ORIGINAL
        0-based positions removed. The caller is responsible for any facet-balance
        bookkeeping (this function does not re-balance facets).
    """
    if len(items) <= 1:
        return list(items), []

    texts = [it.item_text for it in items]
    sim: Optional[np.ndarray] = None
    try:
        from backend.agents.correlation_estimator import (
            compute_cosine_similarity_matrix,
            embed_items_sync,
        )
        from backend.settings import settings as _settings

        model = embedding_model or _settings.PFA_EMBEDDING_MODEL
        embeddings = embed_items_sync(texts, model=model)
        sim = compute_cosine_similarity_matrix(embeddings)
    except Exception as e:  # noqa: BLE001 — embedding may be unavailable/offline
        logger.warning(
            "DEDUP embedding unavailable (%s) — falling back to exact-string", e,
        )

    kept: List[DraftItem] = []
    dropped: List[int] = []

    if sim is None:
        seen: set = set()
        for i, it in enumerate(items):
            key = it.item_text.strip().lower()
            if key in seen:
                dropped.append(i)
            else:
                seen.add(key)
                kept.append(it)
        return kept, dropped

    np.fill_diagonal(sim, 0.0)
    kept_indices: List[int] = []
    for i in range(len(items)):
        if kept_indices and any(sim[i, j] > threshold for j in kept_indices):
            dropped.append(i)
        else:
            kept_indices.append(i)
            kept.append(items[i])

    if dropped:
        logger.warning(
            "DEDUP removed %d/%d near-duplicate items (threshold=%.2f)",
            len(dropped), len(items), threshold,
        )
    return kept, dropped
