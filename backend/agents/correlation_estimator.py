"""Correlation estimation agent using embedding cosine similarity.

Based on Hommel & Arslan (2024) methodology: sentence transformer embeddings
with cosine similarity provide validated accuracy (r=.71 items, r=.89 scales,
r=.86 reliability) for estimating inter-item correlations.

Uses the OpenAI embedding model configured by settings.EMBEDDING_MODEL via
the existing OPENAI_API_KEY. All similarity surfaces share this model so
adjacent statistics come from the same embedding space.
"""

import logging
import threading
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

import numpy as np
from openai import AsyncOpenAI, OpenAI

from backend.schemas import CorrelationCell
from backend.settings import settings

logger = logging.getLogger("lmaig")

EMBEDDING_MODEL = settings.EMBEDDING_MODEL


class EmbeddingsUnavailable(RuntimeError):
    """No embedding credentials are configured (e.g. APP_MODE=mock without an
    OPENAI_API_KEY). Raised before any client is built so callers can degrade
    quietly instead of logging an SDK traceback."""


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
    """Return (client_kwargs, model_name, is_azure) for an embeddings call.

    Raises EmbeddingsUnavailable when no embedding credentials are configured.
    """
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
    if not settings.OPENAI_API_KEY:
        raise EmbeddingsUnavailable(
            "embeddings unavailable: OPENAI_API_KEY is not set and no Azure embedding deployment is configured"
        )
    return (
        {
            "api_key": settings.OPENAI_API_KEY,
            "base_url": settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
        },
        model or EMBEDDING_MODEL,
        False,
    )


# Embedding calls are small; don't inherit the SDK's 600s default timeout.
_EMBED_TIMEOUT_SECONDS = 30.0
_EMBED_MAX_RETRIES = 2


# One run embeds the same item texts many times over (dedup, UVA, every PFA
# pruning iteration, correlation, EGA). Keep recent vectors so each distinct
# text costs one network call. Vectors are kept at full float64 precision
# (~24KB for a 3072-dim model, so the full cache stays near 25MB), keyed by
# endpoint and model so an Azure deployment never serves vectors from another
# space.
_EMBED_CACHE_MAX = 1024
_embed_cache: "OrderedDict[Tuple[str, str, str], np.ndarray]" = OrderedDict()
_embed_cache_lock = threading.Lock()


def clear_embedding_cache() -> None:
    with _embed_cache_lock:
        _embed_cache.clear()


def _cache_space(kwargs: dict, model_name: str) -> Tuple[str, str]:
    endpoint = kwargs.get("azure_endpoint") or kwargs.get("base_url") or ""
    return str(endpoint), model_name


def _cache_lookup(space: Tuple[str, str], items: List[str]) -> Dict[str, np.ndarray]:
    with _embed_cache_lock:
        found = {}
        for text in items:
            key = (*space, text)
            vec = _embed_cache.get(key)
            if vec is not None:
                _embed_cache.move_to_end(key)
                found[text] = vec
        return found


def _cache_store(space: Tuple[str, str], texts: List[str], vectors: List[List[float]]) -> Dict[str, np.ndarray]:
    stored = {text: np.asarray(vec, dtype=np.float64) for text, vec in zip(texts, vectors)}
    with _embed_cache_lock:
        for text, vec in stored.items():
            _embed_cache[(*space, text)] = vec
            _embed_cache.move_to_end((*space, text))
        while len(_embed_cache) > _EMBED_CACHE_MAX:
            _embed_cache.popitem(last=False)
    return stored


def _missing_texts(items: List[str], cached: Dict[str, np.ndarray]) -> List[str]:
    """Distinct texts not in the cache, in first-seen order."""
    return [t for t in dict.fromkeys(items) if t not in cached]


def _assemble(items: List[str], vectors: Dict[str, np.ndarray]) -> np.ndarray:
    return np.array([vectors[t] for t in items])


async def embed_items(items: List[str], model: Optional[str] = None) -> np.ndarray:
    """Get embeddings for all items, with at most one API call.

    Args:
        items: List of item texts to embed
        model: OpenAI embedding model name; defaults to settings.EMBEDDING_MODEL.
    """
    kwargs, model_name, is_azure = _embedding_target(model)
    space = _cache_space(kwargs, model_name)
    cached = _cache_lookup(space, items)
    missing = _missing_texts(items, cached)
    if not missing:
        return _assemble(items, cached)
    logger.info(
        "EMBED_ITEMS calling embeddings model=%s provider=%s items=%d cached=%d",
        model_name, "azure" if is_azure else "openai", len(missing), len(items) - len(missing),
    )
    if is_azure:  # TEMPORARY — remove with the Azure evaluation switch
        from openai import AsyncAzureOpenAI

        from backend.agents.azure_auth import azure_token_provider_async

        client = AsyncAzureOpenAI(
            azure_ad_token_provider=azure_token_provider_async,
            timeout=_EMBED_TIMEOUT_SECONDS, max_retries=_EMBED_MAX_RETRIES, **kwargs
        )
    else:
        client = AsyncOpenAI(
            timeout=_EMBED_TIMEOUT_SECONDS, max_retries=_EMBED_MAX_RETRIES, **kwargs
        )
    # Close the per-call client so its HTTP connection pool isn't leaked
    async with client:
        response = await client.embeddings.create(
            model=model_name,
            input=missing,
        )
    # Sort by index to ensure order matches input
    sorted_data = sorted(response.data, key=lambda x: x.index)
    fetched = _cache_store(space, missing, [e.embedding for e in sorted_data])
    return _assemble(items, {**cached, **fetched})


def embed_items_sync(items: List[str], model: Optional[str] = None) -> np.ndarray:
    """Synchronous version of embed_items for use in non-async paths.

    Used by PFA estimator when called from sync graph nodes.
    """
    kwargs, model_name, is_azure = _embedding_target(model)
    space = _cache_space(kwargs, model_name)
    cached = _cache_lookup(space, items)
    missing = _missing_texts(items, cached)
    if not missing:
        return _assemble(items, cached)
    logger.info(
        "EMBED_ITEMS_SYNC calling embeddings model=%s provider=%s items=%d cached=%d",
        model_name, "azure" if is_azure else "openai", len(missing), len(items) - len(missing),
    )
    if is_azure:  # TEMPORARY — remove with the Azure evaluation switch
        from openai import AzureOpenAI

        from backend.agents.azure_auth import azure_token_provider

        client = AzureOpenAI(
            azure_ad_token_provider=azure_token_provider,
            timeout=_EMBED_TIMEOUT_SECONDS, max_retries=_EMBED_MAX_RETRIES, **kwargs
        )
    else:
        client = OpenAI(
            timeout=_EMBED_TIMEOUT_SECONDS, max_retries=_EMBED_MAX_RETRIES, **kwargs
        )
    with client:
        response = client.embeddings.create(model=model_name, input=missing)
    sorted_data = sorted(response.data, key=lambda x: x.index)
    fetched = _cache_store(space, missing, [e.embedding for e in sorted_data])
    return _assemble(items, {**cached, **fetched})


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
