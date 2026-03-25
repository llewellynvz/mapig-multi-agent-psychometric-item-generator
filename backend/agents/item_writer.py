from __future__ import annotations

import logging
import uuid
from typing import List, Tuple

from backend.agents.llm_utils import invoke_structured_with_usage, TokenUsage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import DraftItem, EvidenceChunk, FacetMapperResponse, ItemWriterResponse, UserRequest
from backend.settings import settings

logger = logging.getLogger("lmaig.item_writer")


def write_items(
    request: UserRequest,
    evidence: List[EvidenceChunk],
    facet_mapping: FacetMapperResponse | None = None,
) -> Tuple[ItemWriterResponse, TokenUsage]:
    """Generate initial draft items, optionally guided by facet mapping.

    Args:
        request: User construct specification
        evidence: Retrieved evidence chunks
        facet_mapping: Optional facet structure from Facet Mapper agent

    Returns:
        Tuple of (ItemWriterResponse, TokenUsage)
    """
    item_count = request.item_count
    typed_count = sum(1 for e in evidence if e.evidence_type)
    dim_count = sum(1 for e in evidence if e.evidence_type == "dimensions")
    logger.info(
        "ITEM_WRITER start items=%d evidence=%d typed=%d dimensions=%d model=%s",
        item_count, len(evidence), typed_count, dim_count, request.model_provider,
    )
    if typed_count < 3:
        logger.warning("EVIDENCE_QUALITY_WARNING typed_evidence=%d (< 3 minimum)", typed_count)
    if dim_count == 0 and evidence:
        logger.warning("EVIDENCE_QUALITY_WARNING no dimensions evidence found")

    if settings.APP_MODE == "mock":
        # Deterministic stub: generate simple items with citations to the first evidence chunk(s).
        citations = [e.source_id for e in evidence[:2]] or ["local:unknown#1"]
        items: List[DraftItem] = []
        previous = request.previous_items or []
        has_feedback = bool((request.human_feedback or "").strip())
        for i in range(item_count):
            baseline = previous[i] if i < len(previous) else None
            item_text = (
                f"{baseline} (Refined {i + 1})"
                if baseline and has_feedback
                else f"I feel a sense of belonging at my workplace. (Item {i + 1})"
            )
            rationale = (
                "Refined from prior human feedback while preserving construct alignment."
                if baseline and has_feedback
                else "Stubbed item for orchestration testing. Replace with Azure mode for real generation."
            )
            items.append(
                DraftItem(
                    item_text=item_text,
                    construct_name=request.construct_name,
                    rationale=rationale,
                    evidence_citations=citations,
                )
            )
        return ItemWriterResponse(items=items), TokenUsage()

    system_prompt = load_prompt("item_writer.md")

    # Load item style reference bank for quality calibration
    style_reference = None
    try:
        import pathlib
        ref_path = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "item_style_reference.md"
        if ref_path.exists():
            style_reference = ref_path.read_text(encoding="utf-8")
    except Exception:
        pass  # Non-critical; prompt has inline examples as fallback
    logger.info("STYLE_REFERENCE loaded=%s chars=%d", style_reference is not None, len(style_reference or ""))

    user_payload = {
        "user_request": request.model_dump(),
        "evidence": [e.model_dump() for e in evidence],
        "item_count": item_count,
        "facet_mapping": facet_mapping.model_dump(mode="json") if facet_mapping else None,
        "style_reference": style_reference,
    }

    messages = [
        ("system", system_prompt),
        ("human", f"Draft {item_count} items using ONLY the evidence provided.\n\nINPUT:\n{user_payload}"),
    ]

    return invoke_structured_with_usage(
        ItemWriterResponse,
        messages,
        agent_name="item_writer",
        model_provider=request.model_provider,
        use_chatgpt_critics=request.use_chatgpt_critics,
    )
