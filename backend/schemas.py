from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, conint, field_validator


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

    language: Optional[str] = Field(
        default=None,
        description="Target language for generated items (e.g. 'Spanish', 'French'). If not set, items are generated in English.",
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

    # Construct dimensionality
    is_unidimensional: bool = Field(
        default=True,
        description="User's intended construct structure. If true, items target a single construct and sub-constructs are flagged for separate runs."
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

    construct_exclusions: Optional[str] = Field(
        default=None,
        description="Optional note describing what nearby constructs this is NOT and where overlap should be avoided.",
    )

    cultural_context_notes: Optional[str] = Field(
        default=None,
        description="Searched cultural context notes for the specified cultural_group. Passed to reviewers for culturally informed feedback.",
    )

    evidence_summary: Optional[str] = Field(
        default=None,
        description="Compact summary of theoretical models, dimensions, and boundary conditions from evidence. Gives reviewers theoretical grounding without full evidence payload.",
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

    @field_validator("title", "snippet", "quote", mode="before")
    @classmethod
    def _sanitize_external_text(cls, v):
        # Evidence text comes from external sources (web search, local files)
        # and is interpolated into agent prompts — strip injection patterns
        # at ingestion so every creation site is covered.
        if isinstance(v, str):
            from backend.agents.sanitizer import sanitize_string
            return sanitize_string(v, "evidence_text")
        return v


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
        max_length=500,  # ~70 words at 7 chars/word average — allows facet + evidence citation
        description="Why this item reflects the construct. Maximum 50 words.",
    )
    evidence_citations: List[str] = Field(
        default_factory=list,
        description="List of EvidenceChunk.source_id values that support this item.",
    )
    facet_name: Optional[str] = Field(
        default=None,
        description="Facet this item targets (from Facet Mapper agent).",
    )
    polarity: Literal["+", "-"] = Field(
        default="+",
        description="Item polarity for sign-aware embeddings during PFA. '+' positively keyed, '-' reverse-keyed.",
    )
    validation_result: Optional["ItemValidation"] = Field(
        default=None,
        description="Optional validation result if item has been validated.",
    )


class FacetDefinition(BaseModel):
    """A single construct facet identified by the Facet Mapper agent."""

    model_config = ConfigDict(extra="forbid")

    facet_name: str = Field(..., min_length=2, description="Short name for this facet (e.g., 'Attentional Shifting')")
    facet_description: str = Field(..., min_length=10, description="What this facet IS — operational definition")
    exclusions: str = Field(..., min_length=5, description="What this facet is NOT — negative space fence to prevent overlap")
    target_item_count: int = Field(..., ge=1, description="Number of items to allocate to this facet")


class FacetMapperResponse(BaseModel):
    """Structured output from the Facet Mapper agent.

    Defines the theoretical structure of a construct — either as multiple
    mutually exclusive facets (multi-dimensional) or a single facet with
    strict boundary exclusions (unidimensional).
    """

    model_config = ConfigDict(extra="forbid")

    is_unidimensional: bool = Field(..., description="True if construct has only 1 facet")
    facets: List[FacetDefinition] = Field(..., min_length=1, description="Identified facets with item allocation")
    theoretical_basis: str = Field(..., min_length=10, description="Source model/theory for this facet structure (e.g., 'CFI model per Dennis & Vander Wal, 2010')")
    flagged_sub_constructs: Optional[List[str]] = Field(
        default=None,
        description="Sub-constructs found in literature that user may want to generate items for separately (only populated in unidimensional mode)"
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
    suggested_edit: Optional[str] = Field(
        default=None,
        max_length=300,  # room for a full replacement item (~40 words)
        description="Proposed replacement text, max 40 words. None for global/facet-level comments.",
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

    summary: str = Field(
        default="",
        description="What was fixed and what remains risky, including facet balance.",
    )
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
    correlation: float = Field(..., ge=-1.0, le=1.0, description="Embedding cosine similarity treated as a pseudo inter-item correlation (pre-data estimate)")
    ci_low: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Lower bound of 95% confidence interval")
    ci_high: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Upper bound of 95% confidence interval")


class CorrelationMatrix(BaseModel):
    """Semantic similarity matrix with pre-data aggregates.

    Contains pairwise embedding cosine similarities (upper-triangular only,
    treated as pseudo inter-item correlations) plus scale-level pre-data
    estimates such as pseudo-alpha and mean semantic similarity.
    """

    model_config = ConfigDict(extra="forbid")

    cells: List[CorrelationCell] = Field(..., min_length=1, description="Flat list of N*(N-1)/2 cells (upper-triangular)")
    pseudo_alpha: Optional[float] = Field(
        default=None,
        le=1.0,
        description=(
            "Standardized Cronbach's alpha formula applied to the semantic-similarity matrix "
            "('pseudo-alpha', a pre-data estimate; Hommel & Arslan 2024 framing). NOT McDonald's "
            "omega and NOT respondent-based reliability. None = not estimable; negative values are "
            "reported as-is (degenerate item set)."
        ),
    )
    mean_inter_item_correlation: float = Field(..., description="Mean pairwise embedding cosine similarity (pseudo inter-item r)")
    internal_consistency_flag: str = Field(..., description="optimal_range/too_low/too_high/calculation_failed based on mean semantic similarity")
    guidance: Optional[str] = Field(default=None, description="Actionable guidance based on internal_consistency_flag")
    redundancy_flags: Optional[List[str]] = Field(default=None, description="Warnings for item pairs with cosine similarity > 0.75, suggesting redundancy")
    disclaimer: str = Field(default="Similarities computed via sentence-embedding cosine similarity, treated as pseudo-correlations (Hommel & Arslan, 2024). Pre-data estimates; not a substitute for empirical validation.", description="Standard disclaimer for embedding-based estimates")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model that produced the similarity matrix (auditability)")


class ComparisonInstrument(BaseModel):
    """Validated instrument from literature for comparison.

    Represents an established instrument that measures a similar or related construct,
    used for convergent/divergent validity assessment.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, description="Instrument name (e.g., 'Rosenberg Self-Esteem Scale')")
    measured_construct: str = Field(..., min_length=2, description="Construct measured by this instrument")
    source_citation: str = Field(..., min_length=5, description="APA-format citation for the instrument")
    publication_year: Optional[int] = Field(default=None, description="Year the instrument was published")
    sample_items_count: Optional[int] = Field(default=None, ge=0, description="Number of items in the instrument")
    psychometric_properties: Optional[str] = Field(default=None, description="Reported reliability/validity summary")
    similarity_rationale: Optional[str] = Field(default=None, description="Why this instrument is relevant for comparison")
    items: Optional[List[str]] = Field(default=None, description="Actual item texts from the published instrument (for embedding-based validity)")
    validity_method: Optional[str] = Field(default=None, description="Method used for validity scoring: 'embedding', 'llm-as-judge', 'disabled', or 'failed'")

    @field_validator("items", mode="before")
    @classmethod
    def _sanitize_fetched_items(cls, v):
        # Published item texts are fetched from the web and later embedded in
        # prompts — strip injection patterns at ingestion.
        if isinstance(v, list):
            from backend.agents.sanitizer import sanitize_string
            return [
                sanitize_string(item, "instrument_item") if isinstance(item, str) else item
                for item in v
            ]
        return v


class ConstructPairAnalysis(BaseModel):
    """Discriminant validity analysis for a pair of constructs.

    Represents LLM reasoning about expected correlation and discriminant validity
    between the target construct and one comparison construct.
    """

    model_config = ConfigDict(extra="forbid")

    construct_a: str = Field(..., description="First construct in the pair")
    construct_b: str = Field(..., description="Second construct in the pair")
    estimated_correlation: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Expected correlation between constructs")
    discriminant_validity_flag: Optional[str] = Field(default=None, description="adequate/concern/poor based on estimated correlation; 'not_estimable' when scoring failed or was disabled (no fabricated value is ever substituted)")
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

    # Prompt caching metrics
    cache_read_tokens: Optional[int] = Field(default=None, description="Total cached input tokens (Anthropic + OpenAI)")
    cache_savings_usd: Optional[float] = Field(default=None, description="Estimated savings from prompt caching in USD")

    # Phase 14-16 follow-up: surface quality-gate fallback + non-fatal warnings to UI
    force_accepted_below_threshold: bool = Field(
        default=False,
        description="True when the validator force-accepted items below the 7.0 weighted_score threshold (top-N fallback fired). Surfaces in UI as a banner.",
    )
    forced_scores: List[float] = Field(
        default_factory=list,
        description="Weighted scores of items shipped via the quality-gate fallback (only populated when force_accepted_below_threshold is True).",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings (e.g., construct name vs. definition mismatch) to surface to the user.",
    )


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

    # Phase 14: Pseudo-Factor Analysis (Varrasi et al., 2026)
    pfa_result: Optional["PFAResult"] = Field(
        default=None,
        description="Pseudo-Factor Analysis on cosine-similarity of item embeddings: factor recovery, Tucker's congruence, DAAL labels, fit indices."
    )

    # Phase 15: Expert Panel face/content validity
    expert_consensus: Optional["ExpertConsensus"] = Field(
        default=None,
        description="Multi-expert face/content validity panel: psychometric, domain, and localization expert evaluations with IRR and consensus revisions."
    )

    # Phase 16: Persona-based ambiguity detection
    persona_validation: Optional["PersonaValidationResponse"] = Field(
        default=None,
        description="Persona-based conceptual alignment check: respondent persona ratings and inter-persona divergence flags."
    )


# --- Phase 14-16 Schemas: PFA, Expert Panel, Persona Validation ---


class PersonaRating(BaseModel):
    """A single rating from a respondent persona on one item."""

    model_config = ConfigDict(extra="forbid")

    persona_label: str = Field(
        ...,
        min_length=2,
        max_length=1500,
        description=(
            "Persona descriptor (e.g., '32-year-old township nurse in Cape Town'). "
            "Cap raised from 600→1500 to accommodate richer 2–3 sentence biographies "
            "without crashing on edge-case LLM responses. Defensive truncation is "
            "applied at construction time to enforce settings.PERSONA_LABEL_MAX_CHARS."
        ),
    )
    item_index: int = Field(..., ge=0, description="0-based item index")
    rating: conint(ge=1, le=5) = Field(..., description="1-5 Likert rating from this persona")
    interpretation: str = Field(..., min_length=3, max_length=1000, description="2-4 sentence cognitive-interview-style interpretation in the persona's voice")


class PersonaValidationResponse(BaseModel):
    """Output of the lightweight persona validator (Keane & McNaughton 2026, Step 13)."""

    model_config = ConfigDict(extra="forbid")

    personas: List[str] = Field(default_factory=list, description="Generated persona descriptors used for rating")
    ratings: List[PersonaRating] = Field(default_factory=list, description="All persona × item ratings")
    flagged_items: List[int] = Field(
        default_factory=list,
        description="Indices of items where inter-persona disagreement is ≥ PERSONA_VALIDATOR_DISAGREEMENT_THRESHOLD Likert points",
    )
    interpretive_variance: float = Field(
        default=0.0,
        description="Mean across-persona standard deviation of ratings (higher = more interpretive ambiguity)",
    )
    summary: str = Field(default="", description="One-line human-readable summary")


ExpertRole = Literal["psychometric", "domain", "localization", "custom"]


class ExpertEvaluation(BaseModel):
    """Single expert agent's per-item ratings + verdict."""

    model_config = ConfigDict(extra="forbid")

    expert_role: ExpertRole = Field(..., description="Role of this expert agent")
    expert_label: str = Field(..., min_length=2, description="Display label (e.g., 'Psychometric Expert')")
    item_scores: Dict[int, conint(ge=1, le=5)] = Field(
        default_factory=dict,
        description="Map of item_index → 1-5 quality score on this expert's rubric",
    )
    item_comments: Dict[int, str] = Field(
        default_factory=dict,
        description="Map of item_index → short comment (≤30 words) explaining a low score or specific concern",
    )
    overall_verdict: Literal["accept", "revise", "reject_set"] = Field(
        ..., description="Aggregate verdict on the full item set"
    )
    overall_summary: str = Field(default="", max_length=500, description="One-paragraph rationale for the verdict")


class ExpertConsensus(BaseModel):
    """Aggregated expert panel output: round 1 + optional debate + IRR + consensus revisions.

    NOTE on IRR: experts use DIFFERENT rubrics (psychometric / domain / localization),
    so per-item score-level α is conceptually wrong (it assumes parallel ratings of
    the same construct). We compute three IRR signals:

    - `irr_verdict_alpha`: Krippendorff's α on `overall_verdict` (3 raters × 1 nominal
      decision per rater). This is the meaningful aggregate-agreement metric — "do the
      experts agree on the bottom-line outcome?"
    - `irr_pairwise_spearman`: Spearman rank correlation between expert pairs on
      per-item scores. Robust to differing rubric scales — measures "do experts agree
      on which items are best/worst?"
    - `irr_alpha` (legacy / informational): per-item ordinal α. Often low here BY
      DESIGN because rubrics differ; retained for backward-compat but not used as
      a quality flag.
    - `irr_pairwise`: pairwise Cohen's κ on per-item scores (legacy, same caveat).
    """

    model_config = ConfigDict(extra="forbid")

    evaluations: List[ExpertEvaluation] = Field(default_factory=list, description="Round 1 expert evaluations")
    debate_revisions: List[ExpertEvaluation] = Field(
        default_factory=list,
        description="Round 2 (debate) revised evaluations. Empty if debate disabled or no revisions.",
    )
    irr_alpha: Optional[float] = Field(
        default=None,
        description=(
            "[Legacy] Per-item ordinal Krippendorff's α across experts. Often low "
            "because experts use different rubrics — see irr_verdict_alpha for the "
            "meaningful agreement metric."
        ),
    )
    irr_verdict_alpha: Optional[float] = Field(
        default=None,
        description=(
            "Krippendorff's α (nominal) on the experts' overall_verdict decisions. "
            "This is the right inter-rater metric for differing-rubric experts — "
            "asks 'do they agree on the bottom-line outcome?'"
        ),
    )
    irr_pairwise: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description=(
            "[Legacy] Map 'role_a|role_b' → Cohen's κ (linear-weighted on the fixed 1-5 scale) "
            "for per-item scores. None = not estimable (e.g., zero variance)."
        ),
    )
    irr_pairwise_spearman: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description=(
            "Pairwise Spearman rank correlation between experts on per-item scores. "
            "Measures whether experts agree on RELATIVE ITEM ORDERING — robust to "
            "differing rubrics. None = not estimable (zero variance or too few ratings)."
        ),
    )
    consensus_revisions: RevisionPlan = Field(
        default_factory=RevisionPlan,
        description="RevisionPlan handed to meta-editor for one final pass",
    )
    dissent_flags: List[int] = Field(
        default_factory=list,
        description="Item indices where inter-expert SD ≥ 1.0",
    )
    irr_warning: Optional[str] = Field(
        default=None,
        description="Warning emitted when expert agreement is genuinely low (verdict α < threshold)",
    )


class FactorLoading(BaseModel):
    """Factor loadings for a single item from PFA."""

    model_config = ConfigDict(extra="forbid")

    item_index: int = Field(..., ge=0, description="0-based item index")
    item_text: str = Field(..., description="The item text (for display)")
    facet_name: Optional[str] = Field(default=None, description="Facet from facet_mapping (parent factor name)")
    loadings: List[float] = Field(..., description="Loading on each factor, length = n_factors")
    parent_factor: int = Field(..., ge=0, description="Expected factor index for this item (from facet_mapping)")
    primary_loading: float = Field(..., description="Maximum |loading| across factors")
    primary_factor: int = Field(..., ge=0, description="Index of factor with maximum |loading|")
    is_well_loaded: bool = Field(
        ...,
        description="True iff all 4 retention rules pass (loads on parent, > others, > avg of others, > avg items on factor)",
    )
    retention_rule_violations: List[str] = Field(
        default_factory=list,
        description="Names of any retention rules this item failed",
    )


class PFAResult(BaseModel):
    """Result of running Pseudo-Factor Analysis on item embeddings."""

    model_config = ConfigDict(extra="forbid")

    embedding_model: str = Field(..., description="Embedding model used (e.g., 'text-embedding-3-large')")
    n_items: int = Field(..., ge=1, description="Number of items analyzed")
    n_factors: int = Field(..., ge=1, description="Number of factors extracted")
    factor_labels: List[str] = Field(default_factory=list, description="Factor labels via DAAL (Dominant Average Absolute Loading)")
    loadings: List[FactorLoading] = Field(..., description="Per-item loadings + retention check")
    tuckers_congruence: List[float] = Field(
        default_factory=list,
        description=(
            "Per-factor Tucker congruence computed against a one-hot target built from the LLM facet "
            "assignments — measures how concentrated loadings are on the expected facet, not cross-solution "
            "factor similarity. The 0.85/0.95 bands are applied heuristically (they were calibrated for "
            "loading-vs-loading comparisons; Lorenzo-Seva & ten Berge, 2006)."
        ),
    )
    factor_recovery_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of expected factors recovered (loading > 0.4 majority)",
    )
    rmsr: float = Field(default=0.0, description="Root Mean Square Residual (lower is better; <0.05 good)")
    caf: float = Field(default=0.0, description="Common Part Accounted For (higher is better; >0.7 good)")
    eigenvalues: List[float] = Field(
        default_factory=list,
        description=(
            "Eigenvalues of the cosine-similarity matrix (original correlation-matrix eigenvalues on the "
            "factor-analyzer path; signed eigendecomposition values on the PCA fallback — negatives signal "
            "a non-positive-definite matrix)."
        ),
    )
    residual_correlation_matrix: List[List[float]] = Field(
        default_factory=list,
        description="Item × item residual correlation matrix (similarity − reproduced)",
    )
    items_dropped: List[int] = Field(
        default_factory=list,
        description="Original item indices dropped during pruning (empty for analytics-only PFA)",
    )
    fit_verdict: Literal["good", "acceptable", "poor"] = Field(
        default="acceptable", description="Overall fit verdict"
    )
    model_identifiability: Literal["saturated", "identified", "over_identified"] = Field(
        default="over_identified",
        description=(
            "Degrees-of-freedom check on the EFA model. 'saturated' = 0 dof (n_items too small for meaningful fit "
            "indices; RMSR=0 / CAF=1 trivially). 'identified' = exactly enough dof. 'over_identified' = positive dof "
            "(typical case; fit indices informative)."
        ),
    )
    disclaimer: str = Field(
        default=(
            "Pseudo-Factor Analysis on sentence-embedding cosine similarity (Varrasi et al., 2026). "
            "Pre-calibration heuristic; not a substitute for empirical EFA on respondent data."
        ),
        description="Standard disclaimer for embedding-based factor analysis",
    )
    solver: str = Field(
        default="factor_analyzer:oblimin",
        description=(
            "Extraction path used. 'factor_analyzer:oblimin' = oblique EFA with factor correlations; "
            "'oblimin_phi_missing' = oblique solution but Φ unavailable (fit indices computed with Φ=I); "
            "'pca_eigh_fallback' = unrotated PCA fallback, eigenvalues reported signed."
        ),
    )
    pseudo_omega: Optional[float] = Field(
        default=None,
        le=1.0,
        description=(
            "Omega-total computed from the PFA loading solution: (Λ′1)′Φ(Λ′1) / "
            "[(Λ′1)′Φ(Λ′1) + Σ(1−diag(ΛΦΛ′))]. Pre-data semantic estimate on embedding-derived "
            "loadings — NOT respondent-based reliability. None = not estimable (e.g., Heywood case)."
        ),
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
