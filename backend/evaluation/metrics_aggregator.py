import logging
from backend.evaluation.schemas import ComparisonResult

logger = logging.getLogger(__name__)

# The four LLM-as-judge comparison dimensions, in reporting order. Metric
# attributes and API keys are named after these so each score says what it
# measures (earlier versions relabelled them as "agent performance",
# "workflow efficiency", etc., which they never measured).
DIMENSIONS = (
    "quality_parity",
    "construct_fidelity",
    "stylistic_similarity",
    "psychometric_properties",
)


class EvaluationMetrics:
    """Mean LLM-as-judge scores (1-10) across the 4 comparison dimensions.

    Attributes:
        quality_parity_score: Clarity/precision relative to the published item
        construct_fidelity_score: Alignment with the target construct
        stylistic_similarity_score: Tone/format similarity to the published item
        psychometric_properties_score: Judged difficulty/discrimination/bias
        overall_score: Mean of the 4 dimension scores
        total_comparisons: Number of item comparisons aggregated
        evaluated_scales: Benchmark scales whose comparisons are included
        failed_scales: Scales that could not be evaluated, as
            ``{"name", "domain", "error"}`` dicts (excluded from the scores)
        pairing_method: How generated items were paired with published items
    """

    def __init__(
        self,
        quality_parity_score: float,
        construct_fidelity_score: float,
        stylistic_similarity_score: float,
        psychometric_properties_score: float,
        total_comparisons: int,
        evaluated_scales: list[str] | None = None,
        failed_scales: list[dict] | None = None,
        pairing_method: str | None = None,
    ):
        self.quality_parity_score = quality_parity_score
        self.construct_fidelity_score = construct_fidelity_score
        self.stylistic_similarity_score = stylistic_similarity_score
        self.psychometric_properties_score = psychometric_properties_score
        self.total_comparisons = total_comparisons
        self.evaluated_scales = list(evaluated_scales or [])
        self.failed_scales = list(failed_scales or [])
        self.pairing_method = pairing_method
        self.overall_score = (
            quality_parity_score +
            construct_fidelity_score +
            stylistic_similarity_score +
            psychometric_properties_score
        ) / 4.0

    def dimension_scores(self) -> dict[str, float]:
        """Return ``{"<dimension>_score": value}`` for the 4 dimensions."""
        return {f"{d}_score": getattr(self, f"{d}_score") for d in DIMENSIONS}

    def __repr__(self):
        return (
            f"EvaluationMetrics("
            f"quality_parity={self.quality_parity_score:.2f}, "
            f"construct_fidelity={self.construct_fidelity_score:.2f}, "
            f"stylistic_similarity={self.stylistic_similarity_score:.2f}, "
            f"psychometric_properties={self.psychometric_properties_score:.2f}, "
            f"overall={self.overall_score:.2f}, "
            f"n={self.total_comparisons}, "
            f"failed_scales={len(self.failed_scales)})"
        )

def aggregate_comparison_results(comparisons: list[ComparisonResult]) -> EvaluationMetrics:
    """Aggregate comparison results into per-dimension mean scores.

    Each metric is the mean of the judge dimension of the same name
    (quality_parity, construct_fidelity, stylistic_similarity,
    psychometric_properties); no dimension is relabelled.

    Args:
        comparisons: List of ComparisonResult from benchmark item comparisons

    Returns:
        EvaluationMetrics with 4 dimension scores (1-10 scale)

    Raises:
        ValueError: If comparisons list is empty
    """
    if not comparisons:
        raise ValueError("Cannot aggregate empty comparison list")

    n = len(comparisons)
    means = {
        d: sum(getattr(c, d).score for c in comparisons) / n
        for d in DIMENSIONS
    }

    logger.info(
        f"Aggregated {n} comparisons: "
        + ", ".join(f"{d}={v:.2f}" for d, v in means.items())
    )

    return EvaluationMetrics(
        quality_parity_score=means["quality_parity"],
        construct_fidelity_score=means["construct_fidelity"],
        stylistic_similarity_score=means["stylistic_similarity"],
        psychometric_properties_score=means["psychometric_properties"],
        total_comparisons=n
    )
