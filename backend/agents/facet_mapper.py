"""Facet Mapper agent — identifies construct dimensions before item generation.

Analyzes retrieved evidence to establish the formal facet structure of a construct.
Multi-dimensional constructs get N mutually exclusive facets with item allocation.
Unidimensional constructs get 1 facet with strict negative space fence.

Runs between retrieve_node and item_writer_node in the pipeline.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from backend.agents.llm_utils import TokenUsage, invoke_structured_with_usage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import EvidenceChunk, FacetDefinition, FacetMapperResponse, UserRequest
from backend.settings import settings

logger = logging.getLogger("lmaig.facet_mapper")


def map_facets(
    request: UserRequest,
    evidence: List[EvidenceChunk],
) -> Tuple[FacetMapperResponse, TokenUsage]:
    """Identify construct facets from evidence and allocate items per facet.

    Args:
        request: User's construct specification (name, definition, item_count)
        evidence: Retrieved evidence chunks (may include dimension metadata)

    Returns:
        (FacetMapperResponse, TokenUsage) — facet mapping + token cost
    """
    logger.info(
        "FACET_MAPPER start construct=%s item_count=%d evidence_chunks=%d",
        request.construct_name,
        request.item_count,
        len(evidence),
    )

    if settings.APP_MODE == "mock":
        # Return a single-facet unidimensional mapping covering all requested items
        return FacetMapperResponse(
            is_unidimensional=True,
            facets=[
                FacetDefinition(
                    facet_name=request.construct_name,
                    facet_description=request.construct_definition or f"Core dimension of {request.construct_name}",
                    exclusions="Not related constructs or sub-constructs",
                    target_item_count=request.item_count,
                )
            ],
            theoretical_basis=f"Mock facet mapping for {request.construct_name}",
        ), TokenUsage()

    system_prompt = load_prompt("facet_mapper.md")

    # Build payload — include dimension-rich evidence for the LLM
    user_payload = {
        "construct_name": request.construct_name,
        "construct_definition": request.construct_definition,
        "item_count": request.item_count,
        "is_unidimensional": request.is_unidimensional,
        "evidence": [e.model_dump(mode="json") for e in evidence],
    }

    messages = [
        ("system", system_prompt),
        ("human", f"Analyze this construct and return the facet mapping.\n\nINPUT:\n{user_payload}"),
    ]

    resp, usage = invoke_structured_with_usage(
        FacetMapperResponse,
        messages,
        agent_name="facet_mapper",
        model_provider=request.model_provider,
    )

    # Post-validation: ensure item counts sum to requested total
    total_allocated = sum(f.target_item_count for f in resp.facets)
    if total_allocated != request.item_count:
        logger.warning(
            "FACET_MAPPER item_count_mismatch allocated=%d requested=%d — adjusting",
            total_allocated, request.item_count,
        )
        # Adjust: distribute difference across facets
        diff = request.item_count - total_allocated
        if diff > 0:
            # Under-allocated: add to first facets
            for i in range(diff):
                resp.facets[i % len(resp.facets)].target_item_count += 1
        elif diff < 0:
            # Over-allocated: subtract from last facets
            for i in range(abs(diff)):
                idx = len(resp.facets) - 1 - (i % len(resp.facets))
                if resp.facets[idx].target_item_count > 1:
                    resp.facets[idx].target_item_count -= 1

    logger.info(
        "FACET_MAPPER done construct=%s facets=%d unidimensional=%s basis=%s",
        request.construct_name,
        len(resp.facets),
        resp.is_unidimensional,
        resp.theoretical_basis[:60],
    )

    return resp, usage
