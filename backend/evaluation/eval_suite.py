import logging
import asyncio
from backend.evaluation.benchmark_loader import load_benchmark_scales
from backend.evaluation.item_comparison import compare_to_published_item
from backend.evaluation.metrics_aggregator import aggregate_comparison_results, EvaluationMetrics
from backend.evaluation.schemas import ComparisonResult
from backend.schemas import UserRequest
from backend.graph import build_graph
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

def run_evaluation_suite(model_provider: str = "claude") -> EvaluationMetrics:
    """Run full evaluation suite: generate items, compare to benchmarks, aggregate metrics.

    Workflow:
    1. Load 5 benchmark scales (25 items total)
    2. For each scale, generate 5 items using MAPIG with benchmark construct
    3. Compare each generated item to corresponding benchmark item
    4. Aggregate comparison results into 4-dimensional metrics

    Args:
        model_provider: "claude" or "openai" (APP_MODE env var controls mock mode)

    Returns:
        EvaluationMetrics with dimension scores

    Raises:
        FileNotFoundError: If benchmark scales file missing
        RuntimeError: If evaluation produces no results
    """
    logger.info("Starting evaluation suite...")

    # Validate model_provider
    if model_provider not in ["claude", "openai"]:
        # Default to claude if invalid value
        logger.warning(f"Invalid model_provider '{model_provider}', defaulting to 'claude'")
        model_provider = "claude"

    # Initialize graph with in-memory checkpointer
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)

    # Step 1: Load benchmark scales
    scales = load_benchmark_scales()
    logger.info(f"Loaded {len(scales)} benchmark scales")

    all_comparisons = []

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
            # Run MAPIG generation
            # Pattern from backend/main.py: graph.invoke returns state dict with final_output
            result_state = graph.invoke(
                {"user_request": request},
                config={"configurable": {"thread_id": f"eval-{scale.domain}"}}
            )

            # Extract FinalOutput from result state
            final_output = result_state.get("final_output")
            if final_output is None:
                logger.error(f"No final_output in result_state for {scale.name}")
                continue

            # FinalOutput.final_items is list of DraftItem objects
            # DraftItem has .item_text attribute
            generated_items = [item.item_text for item in final_output.final_items]

            # Compare each generated item to benchmark item
            for i, (gen_item, bench_item) in enumerate(zip(generated_items, scale.items)):
                logger.info(f"Comparing item {i+1}/5 for {scale.name}")
                comparison = compare_to_published_item(
                    generated_item=gen_item,
                    published_item=bench_item,
                    construct_name=scale.name,
                    model_provider=model_provider
                )
                all_comparisons.append(comparison)

        except Exception as e:
            logger.error(f"Failed to evaluate scale {scale.name}: {e}")
            # Continue with other scales

    # Step 4: Aggregate metrics
    if not all_comparisons:
        raise RuntimeError("Evaluation suite produced no comparison results")

    metrics = aggregate_comparison_results(all_comparisons)
    logger.info(f"Evaluation complete: {metrics}")

    return metrics

async def run_evaluation_suite_async(model_provider: str = "claude") -> EvaluationMetrics:
    """Async version of evaluation suite for parallel processing.

    Future optimization: run comparisons in parallel using asyncio.gather.
    """
    return run_evaluation_suite(model_provider)
