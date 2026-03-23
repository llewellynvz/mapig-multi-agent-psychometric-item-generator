"""LLM-as-judge item comparison logic with position bias mitigation.

This module implements comparison of generated items against published scale items
using Claude Opus as an expert psychometrician judge.
"""

import logging
import warnings
from langchain_core.messages import HumanMessage, SystemMessage
from backend.agents.llm_factory import get_chat_model_for_agent
from backend.agents.prompt_loader import load_prompt
from backend.evaluation.schemas import ComparisonResult, ComparisonDimension
from backend.settings import settings

logger = logging.getLogger(__name__)


def compare_to_published_item(
    generated_item: str,
    published_item: str,
    construct_name: str,
    model_provider: str = "claude"
) -> ComparisonResult:
    """Compare generated item to published scale item using LLM-as-judge.

    Mitigates position bias by evaluating both orderings and averaging scores.

    Args:
        generated_item: The generated assessment item
        published_item: Item from published scale (gold standard)
        construct_name: Name of construct being measured
        model_provider: "claude" or "openai"

    Returns:
        ComparisonResult with averaged scores from both orderings

    Raises:
        RuntimeError: If structured output parsing fails
    """
    # Mock mode: return deterministic results for testing
    if settings.APP_MODE == "mock":
        return _mock_comparison_result(generated_item, published_item, construct_name)

    # Score both orderings to mitigate position bias
    forward = _compare_single_direction(
        generated_item, published_item, construct_name, model_provider, "generated vs published"
    )
    reverse = _compare_single_direction(
        published_item, generated_item, construct_name, model_provider, "published vs generated"
    )

    # Average scores
    return _average_comparison_results(forward, reverse)


def _compare_single_direction(
    candidate: str,
    reference: str,
    construct_name: str,
    model_provider: str,
    direction_label: str
) -> ComparisonResult:
    """Compare candidate to reference (single direction)."""
    system_prompt = load_prompt("item_comparator.md")

    model = get_chat_model_for_agent(
        agent_name="validator",  # Use Opus allocation
        model_provider=model_provider,
        use_chatgpt_critics=False
    )

    messages = [
        SystemMessage(
            content=system_prompt,
            additional_kwargs={"cache_control": {"type": "ephemeral"}}
        ),
        HumanMessage(
            content=f"Construct: {construct_name}\n\nCANDIDATE item:\n{candidate}\n\nREFERENCE item:\n{reference}"
        ),
    ]

    # No include_raw=True — raw response is not needed here and triggers
    # PydanticSerializationUnexpectedValue warnings (openai/openai-python#2872)
    runnable = model.with_structured_output(ComparisonResult, strict=False)
    result = runnable.invoke(messages)

    if result is None:
        logger.error(f"Structured output parsing failed for comparison ({direction_label})")
        raise RuntimeError(f"Item comparison structured output parsing failed - LLM returned invalid format")
    return result


def _average_comparison_results(forward: ComparisonResult, reverse: ComparisonResult) -> ComparisonResult:
    """Average scores from both orderings to mitigate position bias."""
    return ComparisonResult(
        quality_parity=ComparisonDimension(
            dimension="quality_parity",
            score=(forward.quality_parity.score + reverse.quality_parity.score) / 2.0,
            reasoning=f"Forward: {forward.quality_parity.reasoning[:100]}... | Reverse: {reverse.quality_parity.reasoning[:100]}..."
        ),
        construct_fidelity=ComparisonDimension(
            dimension="construct_fidelity",
            score=(forward.construct_fidelity.score + reverse.construct_fidelity.score) / 2.0,
            reasoning=f"Forward: {forward.construct_fidelity.reasoning[:100]}... | Reverse: {reverse.construct_fidelity.reasoning[:100]}..."
        ),
        stylistic_similarity=ComparisonDimension(
            dimension="stylistic_similarity",
            score=(forward.stylistic_similarity.score + reverse.stylistic_similarity.score) / 2.0,
            reasoning=f"Forward: {forward.stylistic_similarity.reasoning[:100]}... | Reverse: {reverse.stylistic_similarity.reasoning[:100]}..."
        ),
        psychometric_properties=ComparisonDimension(
            dimension="psychometric_properties",
            score=(forward.psychometric_properties.score + reverse.psychometric_properties.score) / 2.0,
            reasoning=f"Forward: {forward.psychometric_properties.reasoning[:100]}... | Reverse: {reverse.psychometric_properties.reasoning[:100]}..."
        ),
        overall_score=(forward.overall_score + reverse.overall_score) / 2.0
    )


def _mock_comparison_result(generated_item: str, published_item: str, construct_name: str) -> ComparisonResult:
    """Return deterministic mock comparison result for testing."""
    return ComparisonResult(
        quality_parity=ComparisonDimension(
            dimension="quality_parity",
            score=8.0,
            reasoning="Mock: Both items demonstrate professional clarity and precision"
        ),
        construct_fidelity=ComparisonDimension(
            dimension="construct_fidelity",
            score=7.5,
            reasoning="Mock: Items align well with construct definition and facets"
        ),
        stylistic_similarity=ComparisonDimension(
            dimension="stylistic_similarity",
            score=7.0,
            reasoning="Mock: Similar tone and format, comparable sentence structure"
        ),
        psychometric_properties=ComparisonDimension(
            dimension="psychometric_properties",
            score=7.5,
            reasoning="Mock: Comparable difficulty level and discrimination potential"
        ),
        overall_score=7.5  # Average of 8.0, 7.5, 7.0, 7.5
    )
