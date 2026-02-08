from __future__ import annotations

import uuid
from typing import List

from app.agents.llm_utils import invoke_structured
from app.agents.prompt_loader import load_prompt
from app.schemas import DraftItem, EvidenceChunk, ItemWriterResponse, UserRequest
from app.settings import settings


def write_items(request: UserRequest, evidence: List[EvidenceChunk]) -> ItemWriterResponse:
    """Generate initial draft items."""
    item_count = request.item_count

    if settings.APP_MODE == "mock":
        # Deterministic stub: generate simple items with citations to the first evidence chunk(s).
        citations = [e.source_id for e in evidence[:2]] or ["local:unknown#1"]
        items: List[DraftItem] = []
        for i in range(item_count):
            items.append(
                DraftItem(
                    item_text=f"I feel a sense of belonging at my workplace. (Item {i + 1})",
                    construct_name=request.construct_name,
                    rationale="Stubbed item for orchestration testing. Replace with Azure mode for real generation.",
                    evidence_citations=citations,
                )
            )
        return ItemWriterResponse(items=items)

    system_prompt = load_prompt("item_writer.md")

    user_payload = {
        "user_request": request.model_dump(),
        "evidence": [e.model_dump() for e in evidence],
        "item_count": item_count,
    }

    messages = [
        ("system", system_prompt),
        ("human", f"Draft {item_count} items using ONLY the evidence provided.\n\nINPUT:\n{user_payload}"),
    ]

    return invoke_structured(ItemWriterResponse, messages)
