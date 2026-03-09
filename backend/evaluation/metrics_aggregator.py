import logging
from backend.evaluation.schemas import ComparisonResult

logger = logging.getLogger(__name__)

class EvaluationMetrics:
    """Aggregated evaluation metrics across 4 dimensions."""

    def __init__(
        self,
        item_quality_score: float,
        agent_performance_score: float,
        workflow_efficiency_score: float,
        construct_validity_score: float,
        total_comparisons: int
    ):
        self.item_quality_score = item_quality_score
        self.agent_performance_score = agent_performance_score
        self.workflow_efficiency_score = workflow_efficiency_score
        self.construct_validity_score = construct_validity_score
        self.total_comparisons = total_comparisons
        self.overall_score = (
            item_quality_score +
            agent_performance_score +
            workflow_efficiency_score +
            construct_validity_score
        ) / 4.0

    def __repr__(self):
        return (
            f"EvaluationMetrics("
            f"item_quality={self.item_quality_score:.2f}, "
            f"agent_performance={self.agent_performance_score:.2f}, "
            f"workflow_efficiency={self.workflow_efficiency_score:.2f}, "
            f"construct_validity={self.construct_validity_score:.2f}, "
            f"overall={self.overall_score:.2f}, "
            f"n={self.total_comparisons})"
        )

def aggregate_comparison_results(comparisons: list[ComparisonResult]) -> EvaluationMetrics:
    """Aggregate comparison results into 4-dimensional evaluation metrics.

    Dimension mapping:
    - Item Quality: quality_parity (clarity, precision, professional construction)
    - Agent Performance: construct_fidelity (accuracy of construct measurement)
    - Workflow Efficiency: stylistic_similarity (consistency across items)
    - Construct Validity: psychometric_properties (discrimination, bias avoidance)

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

    # Dimension 1: Item Quality (quality parity)
    item_quality = sum(c.quality_parity.score for c in comparisons) / n

    # Dimension 2: Agent Performance (construct fidelity)
    agent_performance = sum(c.construct_fidelity.score for c in comparisons) / n

    # Dimension 3: Workflow Efficiency (stylistic similarity)
    workflow_efficiency = sum(c.stylistic_similarity.score for c in comparisons) / n

    # Dimension 4: Construct Validity (psychometric properties)
    construct_validity = sum(c.psychometric_properties.score for c in comparisons) / n

    logger.info(
        f"Aggregated {n} comparisons: "
        f"Quality={item_quality:.2f}, "
        f"Performance={agent_performance:.2f}, "
        f"Efficiency={workflow_efficiency:.2f}, "
        f"Validity={construct_validity:.2f}"
    )

    return EvaluationMetrics(
        item_quality_score=item_quality,
        agent_performance_score=agent_performance,
        workflow_efficiency_score=workflow_efficiency,
        construct_validity_score=construct_validity,
        total_comparisons=n
    )
