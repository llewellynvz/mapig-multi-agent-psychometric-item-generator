"""Exploratory Graph Analysis (EGA) and Unique Variable Analysis (UVA).

Two honestly separated paths:

- Semantic path (always available): a thresholded network on the item
  embedding cosine matrix with seeded Louvain community detection. This is a
  SEMANTIC heuristic dimensionality signal — no sample size exists, so no
  EBIC or likelihood-based claims are made.
- Statistical path (synthetic pilot only): EBIC-tuned graphical lasso on the
  synthetic Pearson matrix, where a real N exists (Golino & Epskamp EGA
  method), then a partial-correlation network and seeded Louvain.

UVA redundancy uses weighted topological overlap (Christensen, Garrido &
Golino) with a 0.25 default threshold, on whichever network exists.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional, Tuple

import networkx as nx
import numpy as np

logger = logging.getLogger("mapig.ega")

LOUVAIN_SEED = 42
SEMANTIC_EDGE_THRESHOLD = 0.30
WTO_REDUNDANCY_THRESHOLD = 0.25
EBIC_GAMMA = 0.5


def _louvain_communities(graph: nx.Graph) -> List[List[int]]:
    if graph.number_of_edges() == 0:
        return [[node] for node in sorted(graph.nodes)]
    communities = nx.community.louvain_communities(
        graph, weight="weight", seed=LOUVAIN_SEED
    )
    return [sorted(community) for community in sorted(communities, key=min)]


def build_semantic_network(
    sim_matrix: np.ndarray,
    threshold: float = SEMANTIC_EDGE_THRESHOLD,
) -> nx.Graph:
    """Thresholded weighted graph from a cosine-similarity matrix: edges keep
    positive similarities at or above the threshold."""
    n_items = sim_matrix.shape[0]
    graph = nx.Graph()
    graph.add_nodes_from(range(n_items))
    for i in range(n_items):
        for j in range(i + 1, n_items):
            weight = float(sim_matrix[i, j])
            if np.isfinite(weight) and weight >= threshold:
                graph.add_edge(i, j, weight=weight)
    return graph


def _ebic(
    precision: np.ndarray, emp_cov: np.ndarray, n: int, gamma: float = EBIC_GAMMA
) -> float:
    p = precision.shape[0]
    sign, logdet = np.linalg.slogdet(precision)
    if sign <= 0:
        return float("inf")
    log_likelihood = (n / 2.0) * (logdet - float(np.trace(emp_cov @ precision)))
    n_edges = int(np.sum(np.abs(np.triu(precision, k=1)) > 1e-8))
    return float(
        -2.0 * log_likelihood
        + n_edges * math.log(n)
        + 4.0 * n_edges * gamma * math.log(p)
    )


def build_ebic_glasso_network(
    pearson_matrix: np.ndarray,
    n_respondents: int,
    gamma: float = EBIC_GAMMA,
) -> Optional[nx.Graph]:
    """EBIC-selected graphical-lasso partial-correlation network. Requires a
    real sample size — only valid on the synthetic pilot's Pearson matrix.
    Returns None when every alpha on the grid fails to converge."""
    if not np.isfinite(pearson_matrix).all() or n_respondents < 10:
        return None
    from sklearn.covariance import graphical_lasso

    best: Optional[Tuple[float, np.ndarray]] = None
    for alpha in np.logspace(-2.5, -0.3, 15):
        try:
            _, precision = graphical_lasso(
                pearson_matrix, alpha=float(alpha), max_iter=200
            )
        except Exception:
            continue
        score = _ebic(precision, pearson_matrix, n_respondents, gamma)
        if best is None or score < best[0]:
            best = (score, precision)
    if best is None:
        logger.warning("EGA_EBIC no alpha converged on the synthetic matrix")
        return None

    precision = best[1]
    d = np.sqrt(np.diag(precision))
    partial = -precision / np.outer(d, d)
    np.fill_diagonal(partial, 0.0)

    n_items = partial.shape[0]
    graph = nx.Graph()
    graph.add_nodes_from(range(n_items))
    for i in range(n_items):
        for j in range(i + 1, n_items):
            weight = float(partial[i, j])
            if abs(weight) > 1e-8:
                graph.add_edge(i, j, weight=abs(weight), partial=weight)
    return graph


def weighted_topological_overlap(adjacency: np.ndarray) -> np.ndarray:
    """wTO_ij = (sum_k a_ik a_jk + a_ij) / (min(k_i, k_j) + 1 - a_ij) on the
    absolute weighted adjacency with zero diagonal."""
    a = np.abs(np.asarray(adjacency, dtype=float))
    np.fill_diagonal(a, 0.0)
    numerator = a @ a + a
    strengths = a.sum(axis=1)
    min_strength = np.minimum.outer(strengths, strengths)
    denominator = min_strength + 1.0 - a
    with np.errstate(invalid="ignore", divide="ignore"):
        wto = numerator / denominator
    np.fill_diagonal(wto, 0.0)
    return np.nan_to_num(wto, nan=0.0)


def find_redundant_pairs(
    adjacency: np.ndarray,
    threshold: float = WTO_REDUNDANCY_THRESHOLD,
) -> List[Tuple[int, int, float]]:
    """UVA redundancy: item pairs whose wTO meets the threshold, strongest
    first."""
    wto = weighted_topological_overlap(adjacency)
    pairs = []
    n_items = wto.shape[0]
    for i in range(n_items):
        for j in range(i + 1, n_items):
            if wto[i, j] >= threshold:
                pairs.append((i, j, float(wto[i, j])))
    pairs.sort(key=lambda pair: -pair[2])
    return pairs


def graph_to_adjacency(graph: nx.Graph) -> np.ndarray:
    n_items = graph.number_of_nodes()
    adjacency = np.zeros((n_items, n_items))
    for i, j, data in graph.edges(data=True):
        adjacency[i, j] = adjacency[j, i] = data.get("weight", 0.0)
    return adjacency


def layout_positions(graph: nx.Graph) -> dict[int, Tuple[float, float]]:
    """Deterministic spring layout normalized to the unit square."""
    positions = nx.spring_layout(graph, seed=LOUVAIN_SEED)
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = (x_max - x_min) or 1.0
    y_span = (y_max - y_min) or 1.0
    return {
        node: (
            float((x - x_min) / x_span),
            float((y - y_min) / y_span),
        )
        for node, (x, y) in positions.items()
    }


def analyze_network(
    graph: nx.Graph,
) -> Tuple[List[List[int]], List[Tuple[int, int, float]], dict[int, Tuple[float, float]]]:
    """Communities, UVA-redundant pairs, and layout for a built network."""
    communities = _louvain_communities(graph)
    redundant = find_redundant_pairs(graph_to_adjacency(graph))
    positions = layout_positions(graph)
    return communities, redundant, positions


SEMANTIC_DISCLAIMER = (
    "Semantic network on embedding cosine similarity — a language-based "
    "heuristic dimensionality signal, not respondent data."
)
SYNTHETIC_EGA_DISCLAIMER = (
    "EGA (EBIC graphical lasso + seeded Louvain) on simulated LLM "
    "respondents — item triage only, not evidence of human dimensionality."
)


def build_ega_result(graph: nx.Graph, method: str):
    """Assemble a serializable EGAResult from a built network."""
    from backend.schemas import EGAEdge, EGANode, EGAResult, RedundantPair

    communities, redundant, positions = analyze_network(graph)
    community_of: dict[int, int] = {}
    for community_index, community in enumerate(communities):
        for node in community:
            community_of[node] = community_index
    nodes = [
        EGANode(
            item_index=int(node),
            x=positions[node][0],
            y=positions[node][1],
            community=community_of.get(node, 0),
        )
        for node in sorted(graph.nodes)
    ]
    edges = [
        EGAEdge(source=int(i), target=int(j), weight=float(data.get("weight", 0.0)))
        for i, j, data in graph.edges(data=True)
    ]
    pairs = [
        RedundantPair(item_i_index=i, item_j_index=j, wto=w)
        for i, j, w in redundant
    ]
    return EGAResult(
        method=method,
        n_dimensions=len(communities),
        communities=communities,
        redundant_pairs=pairs,
        nodes=nodes,
        edges=edges,
        disclaimer=(
            SEMANTIC_DISCLAIMER
            if method == "semantic_threshold"
            else SYNTHETIC_EGA_DISCLAIMER
        ),
    )
