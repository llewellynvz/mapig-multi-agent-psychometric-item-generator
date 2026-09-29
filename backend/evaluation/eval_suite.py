import logging
import re
from backend.evaluation.benchmark_loader import load_benchmark_scales
from backend.evaluation.item_comparison import compare_to_published_item
from backend.evaluation.metrics_aggregator import aggregate_comparison_results, EvaluationMetrics
from backend.evaluation.schemas import ComparisonResult
from backend.schemas import UserRequest
from backend.graph import build_graph
from backend.checkpoint_config import create_checkpointer
from backend.settings import settings

logger = logging.getLogger(__name__)

VALID_MODEL_PROVIDERS = ("claude", "openai")

# Pairing methods reported in EvaluationMetrics.pairing_method
PAIRING_EMBEDDING = "embedding_nearest_neighbor"
PAIRING_LEXICAL = "lexical_nearest_neighbor"


def _word_jaccard(a: str, b: str) -> float:
    """Word-level Jaccard similarity, punctuation ignored (deterministic, no network)."""
    words_a = set(re.findall(r"[a-z0-9']+", a.lower()))
    words_b = set(re.findall(r"[a-z0-9']+", b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _argmax_rows(similarities: list[list[float]]) -> list[int]:
    """Index of the highest value per row; ties go to the lowest index."""
    return [max(range(len(row)), key=lambda j: (row[j], -j)) for row in similarities]


async def pair_with_most_similar(
    generated_items: list[str], published_items: list[str]
) -> tuple[list[int], str]:
    """Pair each generated item with its most similar published item.

    Generated and published items are not written in any shared order, so
    positional pairing (item i with item i) compares arbitrary items. Instead,
    each generated item is compared with its nearest published neighbour.
    Several generated items may share the same published item; every generated
    item is judged exactly once.

    Similarity is embedding cosine similarity (the same embedding helpers the
    correlation estimator and plagiarism detector use). In mock mode, or if
    the embedding call fails, word-level Jaccard similarity is used instead so
    the pairing stays deterministic and offline.

    Returns:
        (indices into published_items, one per generated item; pairing method)
    """
    if not generated_items or not published_items:
        return [], PAIRING_LEXICAL

    if settings.APP_MODE != "mock":
        try:
            from backend.agents.correlation_estimator import (
                compute_cosine_similarity_matrix,
                embed_items,
            )

            embeddings = await embed_items(generated_items + published_items)
            sim = compute_cosine_similarity_matrix(embeddings)
            n_gen = len(generated_items)
            block = sim[:n_gen, n_gen:].tolist()
            return _argmax_rows(block), PAIRING_EMBEDDING
        except Exception as e:
            logger.warning(f"Embedding pairing failed ({e}); falling back to lexical pairing")

    block = [[_word_jaccard(g, p) for p in published_items] for g in generated_items]
    return _argmax_rows(block), PAIRING_LEXICAL


async def run_evaluation_suite(model_provider: str = "claude") -> EvaluationMetrics:
    """Run full evaluation suite: generate items, compare to benchmarks, aggregate metrics.

    Workflow:
    1. Load benchmark scales (5 scales, 5 published items each)
    2. For each scale, generate 5 items using MAPIG with benchmark construct
    3. Compare each generated item to its most similar published item of that
       scale (see pair_with_most_similar)
    4. Aggregate comparison results into 4-dimensional metrics

    A scale whose generation or any comparison fails is excluded from the
    scores and reported in ``EvaluationMetrics.failed_scales``; callers must
    not treat a run with failed scales as a complete evaluation.

    Args:
        model_provider: "claude" or "openai" (APP_MODE env var controls mock mode)

    Returns:
        EvaluationMetrics with dimension scores, evaluated/failed scales and
        the pairing method used

    Raises:
        ValueError: If model_provider is not "claude" or "openai"
        FileNotFoundError: If benchmark scales file missing
        RuntimeError: If evaluation produces no results
    """
    logger.info("Starting evaluation suite...")

    if model_provider not in VALID_MODEL_PROVIDERS:
        raise ValueError(
            f"Invalid model_provider '{model_provider}'; expected one of {VALID_MODEL_PROVIDERS}"
        )

    # Initialize graph with in-memory checkpointer (custom types pre-registered)
    checkpointer = create_checkpointer()
    graph = build_graph(checkpointer=checkpointer)

    # Step 1: Load benchmark scales
    scales = load_benchmark_scales()
    logger.info(f"Loaded {len(scales)} benchmark scales")

    all_comparisons: list[ComparisonResult] = []
    evaluated_scales: list[str] = []
    failed_scales: list[dict] = []
    pairing_methods: set[str] = set()

    # Step 2-3: Generate and compare for each scale
    for scale in scales:
        logger.info(f"Evaluating scale: {scale.name} ({scale.domain})")

        # Generate items for this construct
        request = UserRequest(
            construct_name=scale.name,
            construct_definition=f"{scale.domain} construct from {scale.author} ({scale.year})",
            target_population="General",
            response_scale="5-point Likert",
            item_count=5,
            model_provider=model_provider
        )

        try:
            # Run MAPIG generation (async — graph contains async nodes)
            result_state = await graph.ainvoke(
                {"user_request": request},
                config={"configurable": {"thread_id": f"eval-{scale.domain}"}}
            )

            # Extract FinalOutput from result state
            final_output = result_state.get("final_output")
            if final_output is None:
                raise RuntimeError("generation produced no final_output")

            # FinalOutput.final_items is list of DraftItem objects
            generated_items = [item.item_text for item in final_output.final_items]
            if not generated_items:
                raise RuntimeError("generation produced no items")

            pairs, method = await pair_with_most_similar(generated_items, scale.items)

            scale_comparisons = []
            for i, (gen_item, pub_idx) in enumerate(zip(generated_items, pairs)):
                logger.info(
                    f"Comparing item {i+1}/{len(generated_items)} for {scale.name} "
                    f"with published item {pub_idx+1}"
                )
                comparison = await compare_to_published_item(
                    generated_item=gen_item,
                    published_item=scale.items[pub_idx],
                    construct_name=scale.name,
                    model_provider=model_provider
                )
                scale_comparisons.append(comparison)

        except Exception as e:
            logger.error(f"Failed to evaluate scale {scale.name}: {e}")
            failed_scales.append({"name": scale.name, "domain": scale.domain, "error": str(e)})
            continue

        all_comparisons.extend(scale_comparisons)
        evaluated_scales.append(scale.name)
        pairing_methods.add(method)

    # Step 4: Aggregate metrics
    if not all_comparisons:
        failed = ", ".join(f"{f['name']}: {f['error']}" for f in failed_scales)
        raise RuntimeError(
            "Evaluation suite produced no comparison results"
            + (f" (failed scales — {failed})" if failed else "")
        )

    metrics = aggregate_comparison_results(all_comparisons)
    metrics.evaluated_scales = evaluated_scales
    metrics.failed_scales = failed_scales
    metrics.pairing_method = "+".join(sorted(pairing_methods))
    if failed_scales:
        logger.warning(
            f"{len(failed_scales)} of {len(scales)} scales failed and are excluded: "
            + ", ".join(f["name"] for f in failed_scales)
        )
    logger.info(f"Evaluation complete: {metrics}")

    return metrics
