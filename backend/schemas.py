from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, conint


class LogEvent(BaseModel):
    """Real-time log event for SSE streaming."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["log"]
    timestamp: str = Field(..., description="ISO timestamp")
    level: Literal["info", "warning", "error"] = Field(..., description="Log level")
    source: str = Field(..., description="Agent or step name")
    message: str = Field(..., description="Log message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context (tokens, duration, etc.)")


class UserRequest(BaseModel):
    """The user's measurement intent.

    Keep this contract stable. It is the single source of truth for downstream agents.
    """

    model_config = ConfigDict(extra="forbid")

    construct_name: str = Field(..., min_length=2, description="Name of construct to measure.")

    construct_definition: str = Field(
        ...,
        min_length=10,
        description="Operational definition of the construct (in-scope and out-of-scope boundaries).",
    )

    # Optional: native-language label (does not change item language unless you request it)
    native_construct: Optional[str] = Field(
        default=None,
        description="Optional native-language label for the construct (if relevant).",
    )

    # Optional: example item to emulate the style/format (do not copy)
    example_item: Optional[str] = Field(
        default=None,
        description="Optional example item to emulate style/format. Do not copy verbatim.",
    )

    target_population: str = Field(..., min_length=2, description="Who will answer these items.")

    cultural_group: Optional[str] = Field(
        default=None,
        description="Cultural, regional, or linguistic group for context-appropriate items.",
    )

    response_scale: str = Field(..., min_length=2, description="Response scale, e.g., 5-point Likert.")

    item_count: conint(ge=2, le=50) = Field(
        default=10,
        description="Number of items to generate. Minimum 2, maximum 50.",
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Hard constraints for item writing (reading level, no idioms, etc.).",
    )
    construct_exclusions: Optional[str] = Field(
        default=None,
        description="Optional note describing what nearby constructs this is NOT and where overlap should be avoided.",
    )

    human_feedback: Optional[str] = Field(
        default=None,
        description="Optional human feedback to guide a refinement rerun.",
    )
    previous_items: List[str] = Field(
        default_factory=list,
        description="Optional prior generated item texts used as refinement context.",
    )

    # Optional retrieval constraints (web surf)
    approved_domains: List[str] = Field(
        default_factory=list,
        description="Optional domain allowlist to constrain web surfing retrieval.",
    )
    exclude_sources: List[str] = Field(
        default_factory=list,
        description="Optional list of sources/terms to avoid in web search.",
    )

    # Phase 03: Claude API Migration - Model provider selection
    model_provider: Literal["claude", "openai"] = Field(
        default="claude",
        description="LLM provider selection (claude or openai)."
    )

    # ChatGPT critics toggle for cost comparison
    use_chatgpt_critics: bool = Field(
        default=False,
        description="Use ChatGPT (o1-5.2-flex) for critic agents (validator, reviewers, critic). Item writer always uses Sonnet."
    )

    # Phase 10: GPT-5.2 analytics toggle
    use_gpt52_analytics: bool = Field(
        default=False,
        description="Enable GPT-5.2 reasoning models for analytics tasks (correlation, comparison, cross-construct). Higher accuracy but 4-6x cost multiplier."
    )


class AbbreviatedRequest(BaseModel):
    """Minimal request for agents that don't need full context.

    Used by reviewers to reduce payload size (~60% smaller than UserRequest).
    Reviewers only need: construct definition, constraints, target population, and response scale.
    Evidence, examples, and retrieval settings are not needed for review.

    Cost optimization: Reduces input tokens by ~500-800 per reviewer call.
    """

    model_config = ConfigDict(extra="forbid")

    construct_name: str = Field(..., min_length=2, description="Name of construct to measure.")
    construct_definition: str = Field(
        ...,
        min_length=10,
        description="Operational definition of the construct (in-scope and out-of-scope boundaries).",
    )
    target_population: str = Field(..., min_length=2, description="Who will answer these items.")
    cultural_group: Optional[str] = Field(
        default=None,
        description="Cultural, regional, or linguistic group for context-appropriate items.",
    )
    response_scale: str = Field(..., min_length=2, description="Response scale, e.g., 5-point Likert.")
    constraints: List[str] = Field(
        default_factory=list,
        description="Hard constraints for item writing (reading level, no idioms, etc.).",
    )
    model_provider: Literal["claude", "openai"] = Field(
        default="claude",
        description="LLM provider selection (claude or openai)."
    )

    # ChatGPT critics toggle for cost comparison
    use_chatgpt_critics: bool = Field(
        default=False,
        description="Use ChatGPT for critic agents."
    )

    cultural_context_notes: Optional[str] = Field(
        default=None,
        description="Searched cultural context notes for the specified cultural_group. Passed to reviewers for culturally informed feedback.",
    )


class EvidenceChunk(BaseModel):
    """A small evidence unit from an approved source.

    Enhanced in Task #4 to support theoretical model discovery with structured metadata.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="Stable ID used for citations.")
    title: str = Field(..., description="Human-readable title of the source.")
    snippet: str = Field(..., description="Short snippet relevant to the construct.")
    url_or_docref: str = Field(..., description="URL or internal doc reference/path.")
    quote: str = Field(..., description="Exact quote or near-quote used as evidence.")

    # Task #4: Theoretical model discovery fields
    evidence_type: Optional[Literal["theoretical_definition", "dimensions", "measurement_precedent", "boundary_conditions", "cultural_context"]] = Field(
        default=None,
        description="Type of evidence: theoretical_definition, dimensions, measurement_precedent, or boundary_conditions"
    )
    authors: Optional[str] = Field(
        default=None,
        description="Author names for theoretical sources (e.g., 'Keyes, 2002' or 'Deci & Ryan')"
    )
    theoretical_model: Optional[str] = Field(
        default=None,
        description="Name of theoretical model or framework (e.g., 'Two-Continua Model of Mental Health')"
    )
    dimensions: Optional[List[str]] = Field(
        default=None,
        description="Subcomponents or dimensions from theoretical framework (e.g., ['emotional', 'psychological', 'social'])"
    )


class DraftItem(BaseModel):
    """A single candidate item."""

    model_config = ConfigDict(extra="forbid")

    item_text: str = Field(..., min_length=5, description="The item stem text.")
    construct_name: str = Field(
        ...,
        min_length=2,
        description="Construct name for this item (should match UserRequest.construct_name).",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        max_length=350,  # ~50 words at 7 chars/word average
        description="Why this item reflects the construct. Maximum 50 words.",
    )
    evidence_citations: List[str] = Field(
        default_factory=list,
        description="List of EvidenceChunk.source_id values that support this item.",
    )
    validation_result: Optional["ItemValidation"] = Field(
        default=None,
        description="Optional validation result if item has been validated.",
    )


ReviewType = Literal["linguistic", "bias", "content"]


class ReviewComment(BaseModel):
    """A single review comment produced by a specialist reviewer."""

    model_config = ConfigDict(extra="forbid")

    type: ReviewType = Field(..., description="linguistic, bias, or content")
    item_index: Optional[int] = Field(
        default=None,
        description="0-based index of the item this comment refers to (when applicable).",
    )
    issue: str = Field(
        ...,
        min_length=3,
        max_length=210,  # ~30 words at 7 chars/word average
        description="What is wrong and why it matters. Maximum 30 words.",
    )
    severity: conint(ge=1, le=5) = Field(
        ..., description="1=nitpick, 3=needs revision, 5=blocking"
    )
    suggested_edit: str = Field(
        ...,
        min_length=0,
        max_length=175,  # ~25 words for concise suggestions
        description="Proposed fix in plain text. Maximum 25 words.",
    )


class RevisionEdit(BaseModel):
    """An atomic change the meta-editor wants applied."""

    model_config = ConfigDict(extra="forbid")

    item_index: int = Field(..., ge=0, description="Which item in the list to edit.")
    reason: str = Field(
        ...,
        min_length=3,
        max_length=280,  # ~40 words at 7 chars/word average
        description="Why this edit is required. Maximum 40 words.",
    )
    before: str = Field(..., description="Previous item text (or excerpt).")
    after: str = Field(..., description="Revised item text.")


class RevisionPlan(BaseModel):
    """Ordered edits with reasons."""

    model_config = ConfigDict(extra="forbid")

    edits: List[RevisionEdit] = Field(default_factory=list)


class DimensionScore(BaseModel):
    """A single dimension score with chain-of-thought reasoning.

    Represents one of four validation dimensions: correspondence, distinctiveness,
    clarity, or specificity. Reasoning is only required for failing dimensions
    (score < 7) to reduce token usage while maintaining quality feedback.
    """

    model_config = ConfigDict(extra="forbid")

    dimension: str = Field(..., description="One of: correspondence, distinctiveness, clarity, specificity")
    reasoning: str = Field(
        default="",
        min_length=0,
        max_length=280,  # ~40 words at 7 chars/word average
        description="Chain-of-thought explanation. Empty string for passing dimensions (score ≥ 7), detailed reasoning for failing dimensions (score < 7). Maximum 40 words when provided.",
    )
    score: int = Field(..., ge=1, le=10, description="Score from 1-10 for this dimension")


class ItemValidation(BaseModel):
    """Validation result for a single item.

    Contains four dimension scores (correspondence, distinctiveness, clarity, specificity),
    a weighted score, and accept/reject decision.
    """

    model_config = ConfigDict(extra="forbid")

    item_index: int = Field(..., ge=0, description="Index of the item in the batch")
    item_text: str = Field(..., min_length=5, description="The validated item text")
    dimension_scores: List[DimensionScore] = Field(..., description="Exactly 4 dimension scores")
    weighted_score: float = Field(..., description="Weighted average: correspondence*0.5 + distinctiveness*0.25 + clarity*0.15 + specificity*0.1")
    accept: bool = Field(..., description="True if weighted_score >= 7.0")
    attempt: int = Field(..., ge=1, le=3, description="Which regeneration attempt (1-3)")


class ValidationResponse(BaseModel):
    """Validator agent output containing all item validations."""

    model_config = ConfigDict(extra="forbid")

    validations: List[ItemValidation] = Field(default_factory=list, description="Validation results for all items")


# Phase 7: v2.0 Analytics Models


class CorrelationCell(BaseModel):
    """Single correlation between two items.

    Represents a pairwise correlation estimate from embedding cosine similarity.
    """

    model_config = ConfigDict(extra="forbid")

    item_i_index: int = Field(..., ge=0, description="Index of first item (0-based)")
    item_j_index: int = Field(..., ge=0, description="Index of second item (0-based)")
    correlation: float = Field(..., ge=-1.0, le=1.0, description="Estimated correlation coefficient")
    ci_low: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Lower bound of 95% confidence interval")
    ci_high: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Upper bound of 95% confidence interval")


class CorrelationMatrix(BaseModel):
    """Synthetic inter-item correlation matrix with aggregates.

    Contains pairwise correlations (upper-triangular only) plus scale-level statistics
    like McDonald's omega and mean inter-item correlation.
    """

    model_config = ConfigDict(extra="forbid")

    cells: List[CorrelationCell] = Field(..., min_length=1, description="Flat list of N*(N-1)/2 cells (upper-triangular)")
    mcdonalds_omega: float = Field(..., ge=0.0, le=1.0, description="McDonald's omega total for internal consistency reliability")
    mean_inter_item_correlation: float = Field(..., description="Mean of all pairwise correlations")
    internal_consistency_flag: str = Field(..., description="optimal_range/too_low/too_high based on mean inter-item correlation")
    guidance: Optional[str] = Field(default=None, description="Actionable guidance based on internal_consistency_flag")
    disclaimer: str = Field(default="Correlations estimated via sentence-embedding cosine similarity (Hommel & Arslan, 2024). Not a substitute for empirical validation.", description="Standard disclaimer for embedding-based estimates")


class ComparisonInstrument(BaseModel):
    """Validated instrument from literature for comparison.

    Represents an established instrument that measures a similar or related construct,
    used for convergent/divergent validity assessment.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, description="Instrument name (e.g., 'Rosenberg Self-Esteem Scale')")
    construct: str = Field(..., min_length=2, description="Construct measured by this instrument")
    source_citation: str = Field(..., min_length=5, description="APA-format citation for the instrument")
    publication_year: Optional[int] = Field(default=None, description="Year the instrument was published")
    sample_items_count: Optional[int] = Field(default=None, ge=0, description="Number of items in the instrument")
    psychometric_properties: Optional[str] = Field(default=None, description="Reported reliability/validity summary")
    similarity_rationale: Optional[str] = Field(default=None, description="Why this instrument is relevant for comparison")


class ConstructPairAnalysis(BaseModel):
    """Discriminant validity analysis for a pair of constructs.

    Represents LLM reasoning about expected correlation and discriminant validity
    between the target construct and one comparison construct.
    """

    model_config = ConfigDict(extra="forbid")

    construct_a: str = Field(..., description="First construct in the pair")
    construct_b: str = Field(..., description="Second construct in the pair")
    estimated_correlation: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Expected correlation between constructs")
    discriminant_validity_flag: Optional[str] = Field(default=None, description="adequate/concern/poor based on estimated correlation")
    reasoning: Optional[str] = Field(default=None, max_length=500, description="Chain-of-thought explanation for the discriminant validity assessment")


class CrossConstructComparison(BaseModel):
    """Discriminant validity assessment across multiple constructs.

    Analyzes whether the generated items discriminate the target construct
    from related-but-distinct constructs (e.g., self-esteem vs self-efficacy).
    """

    model_config = ConfigDict(extra="forbid")

    target_construct: str = Field(..., min_length=2, description="The construct being measured by generated items")
    comparison_constructs: List[str] = Field(..., description="List of related-but-distinct constructs for comparison")
    analysis_summary: str = Field(..., min_length=10, description="Overall discriminant validity assessment across all comparisons")
    construct_pairs: List[ConstructPairAnalysis] = Field(default_factory=list, description="Per-pair discriminant validity analysis")
    disclaimer: str = Field(default="LLM-estimated, not empirically validated", description="Standard disclaimer for LLM estimates")


class IterationSnapshot(BaseModel):
    """Snapshot of reviewer comments from a single iteration.

    Preserves the full comment history so finalization can aggregate
    feedback across all iterations instead of only the last one.
    """

    model_config = ConfigDict(extra="forbid")

    iteration: int = Field(..., ge=0, description="0-based iteration number")
    linguistic_comments: List[ReviewComment] = Field(default_factory=list)
    bias_comments: List[ReviewComment] = Field(default_factory=list)
    content_comments: List[ReviewComment] = Field(default_factory=list)


class AuditMetadata(BaseModel):
    """Minimal audit trail."""

    model_config = ConfigDict(extra="forbid")

    thread_id: str
    run_id: str
    timestamp_utc: str
    iteration_count: int
    stop_reason: str
    model_info: Dict[str, Any] = Field(default_factory=dict)
    approved_sources: List[str] = Field(default_factory=list)
    validation_attempts: int = Field(default=0, description="Total validation attempts across all items")
    validation_failures: int = Field(default=0, description="Number of items that failed validation")

    # Cost tracking (optional, calculated at finalization)
    opus_cost: Optional[float] = Field(default=None, description="Claude Opus API cost in USD")
    sonnet_cost: Optional[float] = Field(default=None, description="Claude Sonnet API cost in USD")
    openai_cost: Optional[float] = Field(default=None, description="OpenAI API cost in USD (GPT-4o-mini)")
    chatgpt_cost: Optional[float] = Field(default=None, description="ChatGPT API cost in USD (GPT-4o for critics toggle)")
    total_cost: Optional[float] = Field(default=None, description="Total API cost in USD")

    # Smart validation tracking (Strategy C)
    smart_validation_used: Optional[bool] = Field(default=None, description="Whether smart validation (Sonnet→Opus) was used")
    validation_model_used: Optional[str] = Field(default=None, description="Model used for validation (sonnet/opus)")

    # Phase 10: GPT-5.2 cost tracking
    gpt52_reasoning_cost: Optional[float] = Field(default=None, description="GPT-5.2 reasoning token cost in USD")
    gpt52_output_cost: Optional[float] = Field(default=None, description="GPT-5.2 output token cost in USD")
    analytics_budget_exceeded: Optional[bool] = Field(default=None, description="Whether analytics budget cap was exceeded")


class FinalOutput(BaseModel):
    """Final items plus audit metadata.

    Phase 03.1 enhancement: Added user_request and review feedback fields
    to enable complete metadata export without breaking existing consumers.

    Phase 7: v2.0 enhancement: Added optional analytics fields (correlation_matrix,
    comparison_instruments, cross_construct_analysis) for scale-level validation.
    """

    model_config = ConfigDict(extra="forbid")

    final_items: List[DraftItem]
    audit: AuditMetadata

    # Phase 03.1: Optional metadata for complete context export
    user_request: Optional[UserRequest] = Field(
        default=None,
        description="Original user request with construct definition, target population, and constraints. Enables export of context without separate API call."
    )

    linguistic_feedback: List[ReviewComment] = Field(
        default_factory=list,
        description="All linguistic reviewer comments across iterations. Includes item_index, issue, severity, and suggested_edit."
    )

    bias_feedback: List[ReviewComment] = Field(
        default_factory=list,
        description="All bias reviewer comments across iterations. Includes item_index, issue, severity, and suggested_edit."
    )

    content_feedback: List[ReviewComment] = Field(
        default_factory=list,
        description="All content reviewer comments across iterations. Includes item_index, issue, severity, and suggested_edit."
    )

    iteration_history: List[IterationSnapshot] = Field(
        default_factory=list,
        description="Full reviewer comment history from each iteration, preserving per-iteration snapshots."
    )

    # Phase 7: v2.0 analytics fields
    correlation_matrix: Optional[CorrelationMatrix] = Field(
        default=None,
        description="Synthetic inter-item correlation matrix with Cronbach's alpha and internal consistency assessment (CORR-01 through CORR-06)"
    )

    comparison_instruments: List[ComparisonInstrument] = Field(
        default_factory=list,
        description="Validated instruments from literature for convergent/divergent validity comparison (INST-01 through INST-06)"
    )

    cross_construct_analysis: Optional[CrossConstructComparison] = Field(
        default=None,
        description="Discriminant validity assessment comparing target construct against related constructs (XCON-01 through XCON-04)"
    )

    plagiarism_flags: Optional[dict[int, str]] = Field(
        default=None,
        description="Per-item plagiarism warnings keyed by item index (INST-06). Format: {0: 'Potential similarity to X (r = 0.87)'}"
    )

    convergent_validity_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Convergent validity score (0-1) from dual-direction LLM-as-judge comparison with convergent instrument (INST-04)"
    )


# --- Agent I/O wrappers (contracts) ---


class RetrievalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence: List[EvidenceChunk]


class ItemWriterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[DraftItem]


class LinguisticReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comments: List[ReviewComment]


class BiasReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comments: List[ReviewComment]


class ContentReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comments: List[ReviewComment]


class MetaEditorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision_plan: RevisionPlan
    revised_items: List[DraftItem]
