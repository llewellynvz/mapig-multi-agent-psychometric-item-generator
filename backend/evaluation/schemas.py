"""Pydantic schemas for evaluation module.

Defines data models for benchmark scales and comparison results.
"""

from pydantic import BaseModel, Field, field_validator


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
        overall_score: Average of all 4 dimension scores
    """
    quality_parity: ComparisonDimension
    construct_fidelity: ComparisonDimension
    stylistic_similarity: ComparisonDimension
    psychometric_properties: ComparisonDimension
    overall_score: float = Field(..., ge=1.0, le=10.0, description="Overall score (average of dimensions)")

    @field_validator('overall_score')
    @classmethod
    def validate_overall_is_average(cls, v, info):
        """Ensure overall score is the average of all 4 dimensions."""
        data = info.data
        dimensions = [
            data.get('quality_parity'),
            data.get('construct_fidelity'),
            data.get('stylistic_similarity'),
            data.get('psychometric_properties')
        ]

        # Only validate if all dimensions are present
        if all(dim is not None for dim in dimensions):
            expected = sum(dim.score for dim in dimensions) / 4.0
            if abs(v - expected) > 0.01:  # Allow small floating point differences
                raise ValueError(f"Overall score {v} must be average of dimensions ({expected:.2f})")
        return v


class BenchmarkScale(BaseModel):
    """Published assessment scale used for benchmarking.

    Attributes:
        name: Scale name (e.g., "IPIP-NEO-60")
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
