from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, conint


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

    response_scale: str = Field(..., min_length=2, description="Response scale, e.g., 5-point Likert.")

    item_count: conint(ge=10, le=50) = Field(
        default=10,
        description="Number of items to generate. Minimum 10.",
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Hard constraints for item writing (reading level, no idioms, etc.).",
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


class EvidenceChunk(BaseModel):
    """A small evidence unit from an approved source."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="Stable ID used for citations.")
    title: str = Field(..., description="Human-readable title of the source.")
    snippet: str = Field(..., description="Short snippet relevant to the construct.")
    url_or_docref: str = Field(..., description="URL or internal doc reference/path.")
    quote: str = Field(..., description="Exact quote or near-quote used as evidence.")


class DraftItem(BaseModel):
    """A single candidate item."""

    model_config = ConfigDict(extra="forbid")

    item_text: str = Field(..., min_length=5, description="The item stem text.")
    construct_name: str = Field(
        ...,
        min_length=2,
        description="Construct name for this item (should match UserRequest.construct_name).",
    )
    rationale: str = Field(..., min_length=5, description="Why this item reflects the construct.")
    evidence_citations: List[str] = Field(
        default_factory=list,
        description="List of EvidenceChunk.source_id values that support this item.",
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
    issue: str = Field(..., min_length=3, description="What is wrong and why it matters.")
    severity: conint(ge=1, le=5) = Field(
        ..., description="1=nitpick, 3=needs revision, 5=blocking"
    )
    suggested_edit: str = Field(..., min_length=0, description="Proposed fix in plain text.")


class RevisionEdit(BaseModel):
    """An atomic change the meta-editor wants applied."""

    model_config = ConfigDict(extra="forbid")

    item_index: int = Field(..., ge=0, description="Which item in the list to edit.")
    reason: str = Field(..., min_length=3, description="Why this edit is required.")
    before: str = Field(..., description="Previous item text (or excerpt).")
    after: str = Field(..., description="Revised item text.")


class RevisionPlan(BaseModel):
    """Ordered edits with reasons."""

    model_config = ConfigDict(extra="forbid")

    edits: List[RevisionEdit] = Field(default_factory=list)


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


class FinalOutput(BaseModel):
    """Final items plus audit metadata."""

    model_config = ConfigDict(extra="forbid")

    final_items: List[DraftItem]
    audit: AuditMetadata


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
