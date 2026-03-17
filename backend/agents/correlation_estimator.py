"""Correlation estimation agent using embedding cosine similarity.

Based on Hommel & Arslan (2024) methodology: sentence transformer embeddings
with cosine similarity provide validated accuracy (r=.71 items, r=.89 scales,
r=.86 reliability) for estimating inter-item correlations.

Uses OpenAI text-embedding-3-small via the existing OPENAI_API_KEY.
"""

import logging
from typing import List

import numpy as np
from openai import AsyncOpenAI, OpenAI

from backend.schemas import CorrelationCell
from backend.settings import settings

logger = logging.getLogger("lmaig")


async def embed_items(items: List[str]) -> np.ndarray:
    """Get embeddings for all items in a single API call."""
    logger.info(
        "EMBED_ITEMS calling OpenAI embeddings api_key_set=%s base_url=%s",
        bool(settings.OPENAI_API_KEY),
        settings.OPENAI_BASE_URL or "default",
    )
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
    )
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


async def compute_cross_scale_validity(
    generated_items: List[str],
    published_items: List[str],
) -> dict:
    """Compute embedding-based cross-scale validity between two item sets.

    Embeds both sets of items and computes:
    - Item-level cross-correlation matrix (N_gen x N_pub)
    - Mean cross-correlation (aggregate convergent/discriminant score)
    - Scale-level centroid similarity (cosine sim of mean embeddings)

    Args:
        generated_items: The generated items
        published_items: Items from the published comparison instrument

    Returns:
        Dict with keys: mean_cross_r, centroid_r, cross_matrix (list of lists)
    """
    logger.info(
        "CROSS_SCALE_VALIDITY computing gen=%d pub=%d",
        len(generated_items), len(published_items),
    )

    # Embed both sets in a single batch for efficiency
    all_items = generated_items + published_items
    all_embeddings = await embed_items(all_items)

    gen_emb = all_embeddings[: len(generated_items)]
    pub_emb = all_embeddings[len(generated_items) :]

    # L2-normalize
    gen_norms = np.linalg.norm(gen_emb, axis=1, keepdims=True)
    gen_norms = np.where(gen_norms == 0, 1, gen_norms)
    gen_normed = gen_emb / gen_norms

    pub_norms = np.linalg.norm(pub_emb, axis=1, keepdims=True)
    pub_norms = np.where(pub_norms == 0, 1, pub_norms)
    pub_normed = pub_emb / pub_norms

    # Item-level cross-correlation matrix (N_gen x N_pub)
    cross_sim = np.clip(gen_normed @ pub_normed.T, -1.0, 1.0)
    mean_cross_r = float(cross_sim.mean())

    # Scale-level centroid similarity
    gen_centroid = gen_emb.mean(axis=0)
    pub_centroid = pub_emb.mean(axis=0)
    gen_c_norm = np.linalg.norm(gen_centroid)
    pub_c_norm = np.linalg.norm(pub_centroid)
    if gen_c_norm > 0 and pub_c_norm > 0:
        centroid_r = float(
            np.clip(np.dot(gen_centroid, pub_centroid) / (gen_c_norm * pub_c_norm), -1.0, 1.0)
        )
    else:
        centroid_r = 0.0

    logger.info(
        "CROSS_SCALE_VALIDITY mean_cross_r=%.3f centroid_r=%.3f",
        mean_cross_r, centroid_r,
    )

    return {
        "mean_cross_r": round(mean_cross_r, 4),
        "centroid_r": round(centroid_r, 4),
        "cross_matrix": [[round(float(cross_sim[i, j]), 4) for j in range(cross_sim.shape[1])] for i in range(cross_sim.shape[0])],
    }


def compute_cross_scale_validity_sync(
    generated_items: List[str],
    published_items: List[str],
) -> dict:
    """Synchronous version of compute_cross_scale_validity.

    Used by validity_scorer which runs in a thread pool (asyncio.to_thread).
    """
    logger.info(
        "CROSS_SCALE_VALIDITY_SYNC computing gen=%d pub=%d",
        len(generated_items), len(published_items),
    )

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
    )

    all_items = generated_items + published_items
    resp = client.embeddings.create(model="text-embedding-3-small", input=all_items)
    sorted_data = sorted(resp.data, key=lambda x: x.index)
    all_embeddings = np.array([e.embedding for e in sorted_data])

    gen_emb = all_embeddings[: len(generated_items)]
    pub_emb = all_embeddings[len(generated_items) :]

    # L2-normalize
    gen_norms = np.linalg.norm(gen_emb, axis=1, keepdims=True)
    gen_norms = np.where(gen_norms == 0, 1, gen_norms)
    gen_normed = gen_emb / gen_norms

    pub_norms = np.linalg.norm(pub_emb, axis=1, keepdims=True)
    pub_norms = np.where(pub_norms == 0, 1, pub_norms)
    pub_normed = pub_emb / pub_norms

    # Item-level cross-correlation matrix
    cross_sim = np.clip(gen_normed @ pub_normed.T, -1.0, 1.0)
    mean_cross_r = float(cross_sim.mean())

    # Scale-level centroid similarity
    gen_centroid = gen_emb.mean(axis=0)
    pub_centroid = pub_emb.mean(axis=0)
    gen_c_norm = np.linalg.norm(gen_centroid)
    pub_c_norm = np.linalg.norm(pub_centroid)
    if gen_c_norm > 0 and pub_c_norm > 0:
        centroid_r = float(
            np.clip(np.dot(gen_centroid, pub_centroid) / (gen_c_norm * pub_c_norm), -1.0, 1.0)
        )
    else:
        centroid_r = 0.0

    logger.info(
        "CROSS_SCALE_VALIDITY_SYNC mean_cross_r=%.3f centroid_r=%.3f",
        mean_cross_r, centroid_r,
    )

    return {
        "mean_cross_r": round(mean_cross_r, 4),
        "centroid_r": round(centroid_r, 4),
        "cross_matrix": [[round(float(cross_sim[i, j]), 4) for j in range(cross_sim.shape[1])] for i in range(cross_sim.shape[0])],
    }
