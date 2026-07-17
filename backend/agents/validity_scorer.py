"""Dual-direction validity scoring for instrument comparison.

Phase 9 Plan 02: LLM-as-judge convergent and discriminant validity assessment
using GPT-5.2 with position bias mitigation through dual-direction averaging.

When actual published items are available, uses embedding-based cross-scale
cosine similarity (mathematically computed). Falls back to LLM-as-judge when
items are not available.
"""
from __future__ import annotations

import logging
import warnings
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.agents.llm_factory import get_gpt52_analytics_model
from backend.schemas import ConstructPairAnalysis

logger = logging.getLogger("lmaig.validity_scorer")


# Internal Pydantic schemas for structured LLM output
class ConvergentValidityScore(BaseModel):
    """LLM response schema for convergent validity assessment."""
    score: float = Field(..., ge=0.0, le=1.0, description="Convergent validity score (0.0-1.0)")
    reasoning: str = Field(..., description="Chain-of-thought explanation for the score")


class DiscriminantValidityScore(BaseModel):
    """LLM response schema for discriminant validity assessment."""
    estimated_correlation: float = Field(..., ge=-1.0, le=1.0, description="Expected correlation between constructs")
    reasoning: str = Field(..., description="Chain-of-thought explanation for the estimate")


def score_convergent_validity(
    generated_items: List[str],
    instrument_name: str,
    instrument_construct: str,
    target_construct: str,
    published_items: Optional[List[str]] = None,
    gpt52_enabled: bool = True,
) -> tuple[Optional[float], str]:
    """Score convergent validity using embeddings (preferred) or LLM-as-judge fallback.

    When published_items are provided, computes embedding-based cross-scale
    cosine similarity (centroid_r). Otherwise falls back to dual-direction
    LLM-as-judge averaging — unless gpt52_enabled is False, in which case no
    LLM is called and the score is reported as not estimable.

    Args:
        generated_items: List of generated item texts
        instrument_name: Name of comparison instrument
        instrument_construct: Construct measured by comparison instrument
        target_construct: Construct measured by generated items
        published_items: Optional actual item texts from the published instrument
        gpt52_enabled: Whether the user opted into GPT-5.2 analytics calls

    Returns:
        Tuple of (score 0.0-1.0 or None, method 'embedding' | 'llm-as-judge'
        | 'disabled' | 'failed'). None means not estimable — a fabricated
        neutral value is never substituted.
    """
    # Prefer embedding-based scoring when published items are available
    if published_items and len(published_items) >= 3:
        try:
            from backend.agents.correlation_estimator import compute_cross_scale_validity_sync
            result = compute_cross_scale_validity_sync(generated_items, published_items)
            score = result["centroid_r"]
            logger.info(
                "CONVERGENT_VALIDITY method=embedding score=%.3f centroid_r=%.3f mean_cross_r=%.3f instrument=%s",
                score, result["centroid_r"], result["mean_cross_r"], instrument_name,
            )
            return score, "embedding"
        except Exception as e:
            logger.warning(
                "CONVERGENT_VALIDITY embedding failed for %s: %s — falling back to LLM",
                instrument_name, e,
            )

    # Fallback: LLM-as-judge (only when the user opted into GPT-5.2 analytics)
    if not gpt52_enabled:
        logger.info(
            "CONVERGENT_VALIDITY method=disabled instrument=%s — GPT-5.2 analytics off and no usable published items",
            instrument_name,
        )
        return None, "disabled"

    try:
        forward = _score_single_direction_convergent(
            generated_items, instrument_name, instrument_construct, target_construct, "forward"
        )
        reverse = _score_single_direction_convergent(
            generated_items, instrument_name, instrument_construct, target_construct, "reverse"
        )

        averaged_score = (forward.score + reverse.score) / 2.0

        logger.info(
            "CONVERGENT_VALIDITY method=llm-as-judge score=%.2f instrument=%s forward=%.2f reverse=%.2f",
            averaged_score, instrument_name, forward.score, reverse.score
        )

        return averaged_score, "llm-as-judge"

    except Exception as e:
        logger.warning(
            "CONVERGENT_VALIDITY error scoring instrument=%s: %s - score not estimable",
            instrument_name, str(e)
        )
        return None, "failed"


def score_discriminant_validity(
    generated_items: List[str],
    instrument_name: str,
    instrument_construct: str,
    target_construct: str,
    published_items: Optional[List[str]] = None,
    gpt52_enabled: bool = True,
) -> tuple[ConstructPairAnalysis, str]:
    """Score discriminant validity using embeddings (preferred) or LLM fallback.

    When published_items are provided, computes embedding-based cross-scale
    cosine similarity. Low correlation = good discriminant validity. Falls
    back to LLM-as-judge when items are not available.

    Args:
        generated_items: List of generated item texts
        instrument_name: Name of comparison instrument
        instrument_construct: Construct measured by comparison instrument
        target_construct: Construct measured by generated items
        published_items: Optional actual item texts from the published instrument

    Returns:
        Tuple of (ConstructPairAnalysis, method 'embedding' or 'llm-as-judge')
    """
    # Prefer embedding-based scoring when published items are available
    if published_items and len(published_items) >= 3:
        try:
            from backend.agents.correlation_estimator import compute_cross_scale_validity_sync
            result = compute_cross_scale_validity_sync(generated_items, published_items)
            corr = result["centroid_r"]
            flag = "concern" if abs(corr) > 0.85 else "adequate"

            logger.info(
                "DISCRIMINANT_VALIDITY method=embedding correlation=%.3f flag=%s constructs=%s vs %s",
                corr, flag, target_construct, instrument_construct,
            )

            return ConstructPairAnalysis(
                construct_a=target_construct,
                construct_b=instrument_construct,
                estimated_correlation=corr,
                discriminant_validity_flag=flag,
                reasoning=f"Embedding-based: centroid_r={result['centroid_r']:.3f}, mean_item_r={result['mean_cross_r']:.3f}",
            ), "embedding"
        except Exception as e:
            logger.warning(
                "DISCRIMINANT_VALIDITY embedding failed for %s vs %s: %s — falling back to LLM",
                target_construct, instrument_construct, e,
            )

    # Fallback: LLM-as-judge (only when the user opted into GPT-5.2 analytics)
    if not gpt52_enabled:
        logger.info(
            "DISCRIMINANT_VALIDITY method=disabled constructs=%s vs %s — GPT-5.2 analytics off and no usable published items",
            target_construct, instrument_construct,
        )
        return ConstructPairAnalysis(
            construct_a=target_construct,
            construct_b=instrument_construct,
            estimated_correlation=None,
            discriminant_validity_flag="not_estimable",
            reasoning="LLM validity scoring disabled (GPT-5.2 analytics off) and no published items available for embedding-based scoring.",
        ), "disabled"

    try:
        forward = _score_single_direction_discriminant(
            target_construct, instrument_construct, "forward"
        )
        reverse = _score_single_direction_discriminant(
            instrument_construct, target_construct, "reverse"
        )

        averaged_correlation = (forward.estimated_correlation + reverse.estimated_correlation) / 2.0

        if abs(averaged_correlation) > 0.85:
            flag = "concern"
        else:
            flag = "adequate"

        logger.info(
            "DISCRIMINANT_VALIDITY method=llm-as-judge correlation=%.2f flag=%s constructs=%s vs %s",
            averaged_correlation, flag, target_construct, instrument_construct
        )

        return ConstructPairAnalysis(
            construct_a=target_construct,
            construct_b=instrument_construct,
            estimated_correlation=averaged_correlation,
            discriminant_validity_flag=flag,
            reasoning=f"Forward: {forward.reasoning[:100]}... | Reverse: {reverse.reasoning[:100]}..."
        ), "llm-as-judge"

    except Exception as e:
        logger.warning(
            "DISCRIMINANT_VALIDITY error scoring constructs=%s vs %s: %s - not estimable",
            target_construct, instrument_construct, str(e)
        )
        return ConstructPairAnalysis(
            construct_a=target_construct,
            construct_b=instrument_construct,
            estimated_correlation=None,
            discriminant_validity_flag="not_estimable",
            reasoning=f"Scoring failed: {str(e)[:200]}",
        ), "failed"


def _score_single_direction_convergent(
    generated_items: List[str],
    instrument_name: str,
    instrument_construct: str,
    target_construct: str,
    direction: str
) -> ConvergentValidityScore:
    """Score convergent validity in a single direction (forward or reverse).

    Args:
        generated_items: List of generated item texts
        instrument_name: Name of comparison instrument
        instrument_construct: Construct measured by comparison instrument
        target_construct: Construct measured by generated items
        direction: "forward" or "reverse" for logging

    Returns:
        ConvergentValidityScore from LLM

    Raises:
        Exception: If LLM call fails (caught by caller)
    """
    # Build prompt based on direction
    if direction == "forward":
        prompt = f"""You are a psychometric expert assessing convergent validity.

**Task:** Evaluate how well these generated items align with the established instrument '{instrument_name}' which measures {instrument_construct}.

**Generated items measuring {target_construct}:**
{_format_items(generated_items)}

**Comparison instrument:** {instrument_name} (measures {instrument_construct})

**Question:** How well do these generated items align with {instrument_name} measuring {instrument_construct}?

Provide a convergent validity score from 0.0 to 1.0:
- 1.0 = Perfect alignment (items measure exactly the same construct in the same way)
- 0.5 = Moderate alignment (overlap but distinct operationalizations)
- 0.0 = No alignment (completely different constructs)

Consider: Construct overlap, item phrasing similarity, measurement approach, and facet coverage."""
    else:  # reverse
        prompt = f"""You are a psychometric expert assessing convergent validity.

**Task:** Evaluate how well the established instrument '{instrument_name}' (which measures {instrument_construct}) aligns with these generated items.

**Generated items measuring {target_construct}:**
{_format_items(generated_items)}

**Comparison instrument:** {instrument_name} (measures {instrument_construct})

**Question:** How well does {instrument_name} measuring {instrument_construct} align with these generated items?

Provide a convergent validity score from 0.0 to 1.0:
- 1.0 = Perfect alignment (instrument measures exactly the same construct in the same way)
- 0.5 = Moderate alignment (overlap but distinct operationalizations)
- 0.0 = No alignment (completely different constructs)

Consider: Construct overlap, item phrasing similarity, measurement approach, and facet coverage."""

    # Call GPT-5.2 with structured output
    model = get_gpt52_analytics_model()
    messages = [
        SystemMessage(content="You are a psychometric expert specializing in construct validity assessment."),
        HumanMessage(content=prompt)
    ]

    # include_raw=True kept for consistent response handling across codebase.
    # PydanticSerializationUnexpectedValue warnings suppressed globally in
    # backend/__init__.py (see openai/openai-python#2872)
    runnable = model.with_structured_output(ConvergentValidityScore, strict=False, include_raw=True)
    response = runnable.invoke(messages)

    # Handle response (same pattern as item_comparison.py)
    if isinstance(response, dict) and "parsed" in response:
        result = response["parsed"]
        if result is None:
            logger.error("Convergent validity structured output parsing failed (%s direction)", direction)
            raise RuntimeError(f"Convergent validity scoring failed - LLM returned invalid format")
        return result
    else:
        # Fallback for older LangChain behavior
        if response is None:
            raise RuntimeError(f"Convergent validity scoring returned None - no response from LLM")
        return response


def _score_single_direction_discriminant(
    construct_a: str,
    construct_b: str,
    direction: str
) -> DiscriminantValidityScore:
    """Estimate correlation between two constructs in a single direction.

    Args:
        construct_a: First construct
        construct_b: Second construct
        direction: "forward" or "reverse" for logging

    Returns:
        DiscriminantValidityScore from LLM

    Raises:
        Exception: If LLM call fails (caught by caller)
    """
    prompt = f"""You are a psychometric expert specializing in discriminant validity assessment.

**Task:** Estimate the expected correlation between measures of two psychological constructs based on theoretical relationships and empirical literature.

**Construct A:** {construct_a}
**Construct B:** {construct_b}

**Question:** What correlation would you expect between measures of '{construct_a}' and '{construct_b}' based on psychological theory and published research?

Provide an estimated correlation from -1.0 to 1.0:
- 1.0 = Perfect positive correlation (constructs are essentially the same)
- 0.7-0.9 = Strong positive correlation (high overlap, poor discriminant validity)
- 0.3-0.6 = Moderate correlation (related but distinct constructs)
- 0.0-0.2 = Weak correlation (well-discriminated constructs)
- Negative values = Inverse relationship

Consider: Theoretical definitions, empirical meta-analyses, common measurement approaches, and conceptual boundaries between the constructs."""

    # Call GPT-5.2 with structured output
    model = get_gpt52_analytics_model()
    messages = [
        SystemMessage(content="You are a psychometric expert specializing in construct validity and discriminant validity assessment."),
        HumanMessage(content=prompt)
    ]

    # include_raw=True kept for consistent response handling across codebase.
    # PydanticSerializationUnexpectedValue warnings suppressed globally in
    # backend/__init__.py (see openai/openai-python#2872)
    runnable = model.with_structured_output(DiscriminantValidityScore, strict=False, include_raw=True)
    response = runnable.invoke(messages)

    # Handle response
    if isinstance(response, dict) and "parsed" in response:
        result = response["parsed"]
        if result is None:
            logger.error("Discriminant validity structured output parsing failed (%s direction)", direction)
            raise RuntimeError(f"Discriminant validity scoring failed - LLM returned invalid format")
        return result
    else:
        if response is None:
            raise RuntimeError(f"Discriminant validity scoring returned None - no response from LLM")
        return response


def _format_items(items: List[str]) -> str:
    """Format item list for LLM prompt."""
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
