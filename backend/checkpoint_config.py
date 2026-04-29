"""Shared checkpoint configuration for LangGraph MemorySaver.

Registers all custom Pydantic types used in GraphState so that
LangGraph's JsonPlusSerializer can serialize/deserialize them
without warnings. Future LangGraph versions will block unregistered types.
"""
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# Every custom type that appears in GraphState or is nested inside one.
# Format: (module_path, class_name) — must match the actual import path.
ALLOWED_CHECKPOINT_TYPES: list[tuple[str, str]] = [
    # Core request / response
    ("backend.schemas", "UserRequest"),
    ("backend.schemas", "AbbreviatedRequest"),
    # Evidence
    ("backend.schemas", "EvidenceChunk"),
    # Items
    ("backend.schemas", "DraftItem"),
    ("backend.schemas", "DimensionScore"),
    # Facet mapping
    ("backend.schemas", "FacetDefinition"),
    ("backend.schemas", "FacetMapperResponse"),
    # Validation
    ("backend.schemas", "ItemValidation"),
    ("backend.schemas", "ValidationResponse"),
    # Review
    ("backend.schemas", "ReviewComment"),
    # Revision
    ("backend.schemas", "RevisionPlan"),
    ("backend.schemas", "RevisionEdit"),
    ("backend.schemas", "MetaEditorResponse"),
    # Iteration history
    ("backend.schemas", "IterationSnapshot"),
    # Analytics — correlation
    ("backend.schemas", "CorrelationCell"),
    ("backend.schemas", "CorrelationMatrix"),
    # Analytics — comparison
    ("backend.schemas", "ComparisonInstrument"),
    ("backend.schemas", "ConstructPairAnalysis"),
    ("backend.schemas", "CrossConstructComparison"),
    # Final output
    ("backend.schemas", "FinalOutput"),
    ("backend.schemas", "AuditMetadata"),
    # Token tracking
    ("backend.agents.llm_utils", "TokenUsage"),
    # Phase 14-16: PFA, Expert Panel, Persona Validator
    ("backend.schemas", "FactorLoading"),
    ("backend.schemas", "PFAResult"),
    ("backend.schemas", "ExpertEvaluation"),
    ("backend.schemas", "ExpertConsensus"),
    ("backend.schemas", "PersonaRating"),
    ("backend.schemas", "PersonaValidationResponse"),
]


def create_checkpointer() -> MemorySaver:
    """Create a MemorySaver with all custom types pre-registered.

    This eliminates the 'Deserializing unregistered type' warnings
    and ensures forward compatibility with future LangGraph versions
    that will block unregistered types entirely.
    """
    serde = JsonPlusSerializer(allowed_json_modules=ALLOWED_CHECKPOINT_TYPES)
    return MemorySaver(serde=serde)
