import logging
from typing import Literal, Optional

from backend.evaluation.eval_suite import run_evaluation_suite
from backend.evaluation.metrics_aggregator import DIMENSIONS, EvaluationMetrics

logger = logging.getLogger(__name__)

BaselineSource = Literal["synthetic", "measured"]

IMPROVEMENT_THRESHOLD_PCT = 15.0
DIMENSION_PASS_SCORE = 7.0


class BaselineComparison:
    """Result of comparing current system to baseline.

    Semantics of the success fields:

    - ``improvement_basis`` is ``"synthetic_reference"`` when the baseline is
      the fixed reference from ``_get_baseline_metrics`` (not a measured run),
      else ``"measured_baseline"``. All ``*_improvement`` percentages and
      ``meets_improvement_threshold`` are relative to that basis.
    - ``all_dimensions_passing`` uses only the current (measured) scores.
    - ``success`` is ``True``/``False`` only when it can actually be decided:
      it is ``False`` whenever any benchmark scale failed (the run is
      incomplete), and otherwise ``None`` when the baseline is synthetic,
      because an improvement over a made-up reference cannot establish
      success. ``success_reason`` explains a ``False``/``None`` outcome.
    """

    def __init__(
        self,
        current_metrics: EvaluationMetrics,
        baseline_metrics: EvaluationMetrics,
        baseline_source: BaselineSource = "measured",
    ):
        self.current = current_metrics
        self.baseline = baseline_metrics
        self.baseline_source = baseline_source
        self.improvement_basis = (
            "synthetic_reference" if baseline_source == "synthetic" else "measured_baseline"
        )

        # Improvement percentages per dimension (relative to improvement_basis)
        self.dimension_improvements = {
            f"{d}_improvement": self._calc_improvement(
                getattr(current_metrics, f"{d}_score"),
                getattr(baseline_metrics, f"{d}_score"),
            )
            for d in DIMENSIONS
        }
        self.overall_improvement = self._calc_improvement(
            current_metrics.overall_score,
            baseline_metrics.overall_score
        )

        # Success criteria evaluation
        self.meets_improvement_threshold = self.overall_improvement >= IMPROVEMENT_THRESHOLD_PCT
        self.all_dimensions_passing = all(
            score >= DIMENSION_PASS_SCORE for score in current_metrics.dimension_scores().values()
        )

        self.success: Optional[bool]
        self.success_reason: Optional[str]
        failed = current_metrics.failed_scales
        if failed:
            self.success = False
            self.success_reason = (
                f"{len(failed)} benchmark scale(s) failed and were excluded: "
                + ", ".join(f["name"] for f in failed)
            )
        elif baseline_source == "synthetic":
            self.success = None
            self.success_reason = (
                "Baseline is a synthetic reference, not a measured run; "
                "success requires a measured baseline."
            )
        else:
            self.success = self.meets_improvement_threshold and self.all_dimensions_passing
            self.success_reason = None if self.success else (
                "Improvement threshold or dimension threshold not met."
            )

    def _calc_improvement(self, current: float, baseline: float) -> float:
        """Calculate percentage improvement."""
        if baseline == 0:
            return 0.0
        return ((current - baseline) / baseline) * 100.0

    def __repr__(self):
        return (
            f"BaselineComparison("
            f"overall_improvement={self.overall_improvement:.1f}% vs {self.improvement_basis}, "
            f"threshold_met={self.meets_improvement_threshold}, "
            f"dimensions_passing={self.all_dimensions_passing}, "
            f"success={self.success})"
        )

async def run_baseline_comparison(model_provider: str = "claude") -> BaselineComparison:
    """Run the evaluation suite and compare it to the baseline reference.

    No pre-v1.0 run is measured yet: the baseline is the synthetic reference
    from ``_get_baseline_metrics`` and the comparison is flagged as such
    (``baseline_source="synthetic"``, ``improvement_basis="synthetic_reference"``,
    ``success=None``). See BaselineComparison for the success semantics.

    Criteria (decidable only against a measured baseline):
    - Overall improvement ≥15%
    - All 4 dimensions ≥7.0/10
    - No benchmark scale failed

    Args:
        model_provider: "claude" or "openai" (APP_MODE env var controls mock mode)

    Returns:
        BaselineComparison with improvement percentages and success evaluation
    """
    logger.info("Running baseline comparison (current vs synthetic reference)...")

    current_metrics = await run_evaluation_suite(model_provider)

    # No measured pre-v1.0 run exists; compare against a fixed reference and
    # mark it synthetic so no success claim is made from it.
    baseline_metrics = _get_baseline_metrics()

    comparison = BaselineComparison(current_metrics, baseline_metrics, baseline_source="synthetic")

    logger.info(f"Baseline comparison: {comparison}")
    if comparison.success is None:
        logger.info(f"SUCCESS CRITERIA: undetermined ({comparison.success_reason})")
    else:
        logger.info(f"SUCCESS CRITERIA: {'MET' if comparison.success else 'NOT MET'}")

    return comparison

def _get_baseline_metrics() -> EvaluationMetrics:
    """Return the synthetic baseline reference (NOT measured data).

    These are fixed, hand-picked values assumed to be ~20% below a good run.
    They are not derived from any evaluation, so ``total_comparisons`` is 0.
    Replace with a measured run (evaluation with the validation gate
    disabled) and pass ``baseline_source="measured"`` to make success decidable.
    """
    return EvaluationMetrics(
        quality_parity_score=6.5,
        construct_fidelity_score=6.2,
        stylistic_similarity_score=6.8,
        psychometric_properties_score=6.0,
        total_comparisons=0
    )
