"""Correlation estimation agent using embedding cosine similarity.

Based on Hommel & Arslan (2024) methodology: sentence transformer embeddings
with cosine similarity provide validated accuracy (r=.71 items, r=.89 scales,
r=.86 reliability) for estimating inter-item correlations.

Uses the OpenAI embedding model configured by settings.EMBEDDING_MODEL via
the existing OPENAI_API_KEY. All similarity surfaces share this model so
adjacent statistics come from the same embedding space.
"""

import logging
from typing import List, Optional

import numpy as np
from openai import AsyncOpenAI, OpenAI

from backend.schemas import CorrelationCell
from backend.settings import settings

logger = logging.getLogger("lmaig")

EMBEDDING_MODEL = settings.EMBEDDING_MODEL


# TEMPORARY — remove with the Azure evaluation switch
def _azure_embedding_deployment() -> Optional[str]:
    """Deployment serving embeddings under the Azure test switch, else None."""
    if settings.AZURE_TEST_OVERRIDE and settings.AZURE_EMBEDDING_DEPLOYMENT:
        return settings.AZURE_EMBEDDING_DEPLOYMENT
    return None


def active_embedding_model(requested: Optional[str] = None) -> str:
    """Label for the model that embeddings actually come from.

    The Azure switch serves a different deployment than the configured OpenAI
    model, so statistics must report the space they were computed in rather
    than the one that was asked for.
    """
    deployment = _azure_embedding_deployment()
    if deployment:  # TEMPORARY — remove with the Azure evaluation switch
        return f"azure/{deployment}"
    return requested or EMBEDDING_MODEL


def _embedding_target(model: Optional[str]) -> tuple:
    """Return (client_kwargs, model_name, is_azure) for an embeddings call."""
    deployment = _azure_embedding_deployment()
    if deployment:  # TEMPORARY — remove with the Azure evaluation switch
        return (
            {
                "azure_endpoint": settings.AZURE_OPENAI_ENDPOINT,
                "api_version": settings.AZURE_OPENAI_API_VERSION,
            },
            deployment,
            True,
        )
    return (
        {
            "api_key": settings.OPENAI_API_KEY,
            "base_url": settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
        },
        model or EMBEDDING_MODEL,
        False,
    )


async def embed_items(items: List[str], model: Optional[str] = None) -> np.ndarray:
    """Get embeddings for all items in a single API call.

    Args:
        items: List of item texts to embed
        model: OpenAI embedding model name; defaults to settings.EMBEDDING_MODEL.
    """
    kwargs, model_name, is_azure = _embedding_target(model)
    logger.info(
        "EMBED_ITEMS calling embeddings model=%s provider=%s items=%d",
        model_name, "azure" if is_azure else "openai", len(items),
    )
    if is_azure:  # TEMPORARY — remove with the Azure evaluation switch
        from openai import AsyncAzureOpenAI

        from backend.agents.azure_auth import azure_token_provider_async

        client = AsyncAzureOpenAI(
            azure_ad_token_provider=azure_token_provider_async, **kwargs
        )
    else:
        client = AsyncOpenAI(**kwargs)
    response = await client.embeddings.create(
        model=model_name,
        input=items,
    )
    # Sort by index to ensure order matches input
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return np.array([e.embedding for e in sorted_data])


def embed_items_sync(items: List[str], model: Optional[str] = None) -> np.ndarray:
    """Synchronous version of embed_items for use in non-async paths.

    Used by PFA estimator when called from sync graph nodes.
    """
    kwargs, model_name, is_azure = _embedding_target(model)
    logger.info(
        "EMBED_ITEMS_SYNC calling embeddings model=%s provider=%s items=%d",
        model_name, "azure" if is_azure else "openai", len(items),
    )
    if is_azure:  # TEMPORARY — remove with the Azure evaluation switch
        from openai import AzureOpenAI

        from backend.agents.azure_auth import azure_token_provider

        client = AzureOpenAI(azure_ad_token_provider=azure_token_provider, **kwargs)
    else:
        client = OpenAI(**kwargs)
    response = client.embeddings.create(model=model_name, input=items)
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return np.array([e.embedding for e in sorted_data])


def compute_cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute NxN cosine similarity matrix."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # Guard against zero-norm embeddings
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

    all_items = generated_items + published_items
    all_embeddings = embed_items_sync(all_items)

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
