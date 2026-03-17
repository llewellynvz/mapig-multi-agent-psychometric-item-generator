"""Correlation estimation agent using embedding cosine similarity.

Based on Hommel & Arslan (2024) methodology: sentence transformer embeddings
with cosine similarity provide validated accuracy (r=.71 items, r=.89 scales,
r=.86 reliability) for estimating inter-item correlations.

Uses OpenAI text-embedding-3-small via the existing OPENAI_API_KEY.
"""

import logging
from typing import List

import numpy as np
from openai import AsyncOpenAI

from backend.schemas import CorrelationCell
from backend.settings import settings

logger = logging.getLogger("lmaig")


async def embed_items(items: List[str]) -> np.ndarray:
    """Get embeddings for all items in a single API call."""
    kwargs = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    client = AsyncOpenAI(**kwargs)
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=items,
    )
    # Sort by index to ensure order matches input
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return np.array([e.embedding for e in sorted_data])


def compute_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute NxN cosine similarity matrix."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / norms
    sim = normalized @ normalized.T
    np.clip(sim, -1.0, 1.0, out=sim)  # Clamp IEEE 754 floating point overshoot
    return sim


async def estimate_pairwise_correlations(
    items: List[str],
    construct_name: str,  # Kept for API compat, not used by embeddings
    batch_size: int = 20,  # Kept for API compat, not used
) -> List[CorrelationCell]:
    """Estimate pairwise correlations using embedding cosine similarity.

    Args:
        items: List of item texts
        construct_name: Name of the construct (kept for API compatibility)
        batch_size: Not used (kept for API compatibility)

    Returns:
        List of CorrelationCell objects with correlation for each pair
    """
    num_items = len(items)
    logger.info(f"Computing embedding-based correlations for {num_items} items")

    embeddings = await embed_items(items)
    sim_matrix = compute_cosine_similarity_matrix(embeddings)

    # Extract upper-triangular pairs
    cells = []
    for i in range(num_items):
        for j in range(i + 1, num_items):
            cells.append(
                CorrelationCell(
                    item_i_index=i,
                    item_j_index=j,
                    correlation=float(sim_matrix[i, j]),
                    ci_low=None,
                    ci_high=None,
                )
            )

    logger.info(f"Embedding correlation complete: {len(cells)} pairs")
    return cells
