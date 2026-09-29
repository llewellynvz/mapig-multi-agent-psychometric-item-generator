"""Pydantic schemas for evaluation module.

Defines data models for benchmark scales and comparison results.
"""

import logging

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class ComparisonDimension(BaseModel):
    """Single comparison dimension with score and reasoning.

    Attributes:
        dimension: Dimension name (quality_parity, construct_fidelity, stylistic_similarity, psychometric_properties)
        score: Score from 1-10 (float)
        reasoning: Explanation for the score (minimum 10 characters)
    """
    dimension: str = Field(..., description="Dimension name")
    score: float = Field(..., ge=1.0, le=10.0, description="Score 1-10")
    reasoning: str = Field(..., min_length=10, description="Explanation for score")


class ComparisonResult(BaseModel):
    """Result of comparing generated item to published item.

    Contains scores across 4 dimensions plus overall score.

    Attributes:
        quality_parity: Quality comparison (clarity, precision, professionalism)
        construct_fidelity: Construct measurement alignment
        stylistic_similarity: Tone and format similarity
        psychometric_properties: Item characteristics (difficulty, discrimination)
        overall_score: Mean of the 4 dimension scores. Always recomputed from
            the dimensions on validation: an LLM judge that reports an overall
            score inconsistent with its own dimensions is corrected rather than
            rejected, so one arithmetic slip cannot discard a whole comparison.
    """
    quality_parity: ComparisonDimension
    construct_fidelity: ComparisonDimension
    stylistic_similarity: ComparisonDimension
    psychometric_properties: ComparisonDimension
    overall_score: float = Field(
        default=0.0,
        description="Overall score (mean of the 4 dimension scores; recomputed from them)",
    )

    @model_validator(mode="after")
    def recompute_overall_from_dimensions(self) -> "ComparisonResult":
        """Set overall_score to the mean of the 4 dimension scores."""
        expected = (
            self.quality_parity.score
            + self.construct_fidelity.score
            + self.stylistic_similarity.score
            + self.psychometric_properties.score
        ) / 4.0
        if abs(self.overall_score - expected) > 0.01:
            logger.debug(
                "Recomputing overall_score %.3f -> %.3f (mean of dimensions)",
                self.overall_score, expected,
            )
        self.overall_score = expected
        return self


class BenchmarkScale(BaseModel):
    """Published assessment scale used for benchmarking.

    Attributes:
        name: Scale name (e.g., "IPIP Big-Five Factor Markers")
        author: Original author(s)
        year: Publication year
        domain: Psychological domain (personality|clinical|social|organizational|attitudes)
        citation: Full citation for reference
        items: Sample items from the scale (minimum 1)
        license: License or usage terms
    """
    name: str = Field(..., min_length=3, description="Scale name")
    author: str = Field(..., min_length=2, description="Author(s)")
    year: int = Field(..., ge=1900, le=2030, description="Publication year")
    domain: str = Field(..., description="Domain: personality|clinical|social|organizational|attitudes")
    citation: str = Field(default="", description="Full citation")
    items: list[str] = Field(..., min_length=1, description="Sample items (minimum 1)")
    license: str = Field(default="", description="License or usage terms")
