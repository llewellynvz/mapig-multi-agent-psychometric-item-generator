"""Persona-based conceptual alignment validator.

Adapted from Step 13 of Keane & McNaughton (2026): respondent personas re-rate
items to surface ambiguity. Detects items where different personas interpret
the same wording very differently — a different failure mode than bias or
linguistic clarity reviews.

Pipeline position: inside `validation_node`, parallel to LLM-as-judge validator.
Lightweight — uses gpt-5.4-mini (settings.OPENAI_CHEAP_MODEL).
"""

from __future__ import annotations

import concurrent.futures
import logging
import statistics
from typing import List, Tuple

from pydantic import BaseModel, ConfigDict, Field, conint

from backend.agents.llm_utils import TokenUsage, invoke_structured_with_usage
from backend.agents.prompt_loader import load_prompt
from backend.schemas import (
    DraftItem,
    PersonaRating,
    PersonaValidationResponse,
    UserRequest,
)
from backend.settings import settings

logger = logging.getLogger("lmaig.persona_validator")


# --- Inner agent schemas (one persona's output) ---


class _PersonaItemRating(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_index: int = Field(..., ge=0)
    rating: conint(ge=1, le=5)  # type: ignore[valid-type]
    interpretation: str = Field(..., min_length=3, max_length=350)


class _PersonaValidatorAgentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona_label: str = Field(..., min_length=2)
    ratings: List[_PersonaItemRating] = Field(default_factory=list)


# --- Persona generation schema ---


class _PersonaList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    personas: List[str] = Field(..., min_length=1, max_length=10)


def _build_persona_prompts(
    n_personas: int,
    target_population: str,
    cultural_group: str | None,
) -> List[str]:
    """Generate `n_personas` deterministic persona descriptors.

    Falls back to a heuristic mix of age + cultural-group personas if no LLM
    call is desired. The plan calls for one cheap LLM call to produce these,
    but in mock mode we synthesize templates directly.
    """
    cg = cultural_group or "general"
    # Deterministic stub personas covering young / older / cultural sub-group
    base = [
        f"Younger respondent (early 20s) from {target_population} ({cg})",
        f"Older respondent (50s-60s) from {target_population} ({cg})",
        f"Mid-career respondent (30s-40s) from {target_population}, {cg} sub-group",
    ]
    # If user wants more, append generic descriptors
    while len(base) < n_personas:
        base.append(
            f"Additional respondent from {target_population} ({cg}) variant {len(base) + 1}"
        )
    return base[:n_personas]


def _generate_personas_via_llm(
    request: UserRequest, n: int
) -> Tuple[List[str], TokenUsage]:
    """Call the cheap model to generate N distinct persona descriptors."""
    if settings.APP_MODE == "mock":
        return (
            _build_persona_prompts(n, request.target_population, request.cultural_group),
            TokenUsage(),
        )

    system = (
        "You generate concise respondent personas for survey item validation. "
        "Each persona is one sentence describing age band, occupation/role, and "
        "one culturally relevant detail. Personas must be DISTINCT (cover age "
        "range and any cultural sub-groups)."
    )
    human = (
        f"Generate exactly {n} distinct one-sentence respondent persona descriptors "
        f"for a survey targeted at: target_population={request.target_population!r} "
        f"cultural_group={request.cultural_group!r}.\n\n"
        f"Cover the youngest end, oldest end, and a culturally distinct sub-group. "
        f"Return JSON with a 'personas' field containing exactly {n} strings."
    )
    try:
        result, usage = invoke_structured_with_usage(
            _PersonaList,
            [("system", system), ("human", human)],
            agent_name="persona_validator",
            model_provider=request.model_provider,
        )
        return list(result.personas)[:n], usage
    except Exception as e:
        logger.warning("Persona generation LLM failed (%s); using template fallback", e)
        return (
            _build_persona_prompts(n, request.target_population, request.cultural_group),
            TokenUsage(),
        )


def _rate_items_for_persona(
    request: UserRequest,
    persona_label: str,
    items: List[DraftItem],
) -> Tuple[_PersonaValidatorAgentOutput, TokenUsage]:
    """Single-persona LLM call: rate every item + interpretation."""
    if settings.APP_MODE == "mock":
        # Deterministic mock: rating cycles over 1..5 to produce disagreement
        offset = abs(hash(persona_label)) % 5
        ratings = [
            _PersonaItemRating(
                item_index=i,
                rating=((i + offset) % 5) + 1,
                interpretation=f"As {persona_label}, I read item {i} as a self-report query.",
            )
            for i in range(len(items))
        ]
        return (
            _PersonaValidatorAgentOutput(persona_label=persona_label, ratings=ratings),
            TokenUsage(),
        )

    system = load_prompt("persona_validator.md")
    payload = {
        "persona": persona_label,
        "construct_name": request.construct_name,
        "construct_definition": request.construct_definition,
        "response_scale": request.response_scale,
        "target_population": request.target_population,
        "cultural_group": request.cultural_group,
        "items": [
            {"item_index": i, "item_text": it.item_text}
            for i, it in enumerate(items)
        ],
    }
    human = (
        f"Rate every item as the persona would. Return all {len(items)} ratings.\n\n"
        f"INPUT:\n{payload}"
    )

    return invoke_structured_with_usage(
        _PersonaValidatorAgentOutput,
        [("system", system), ("human", human)],
        agent_name="persona_validator",
        model_provider=request.model_provider,
    )


def validate_with_personas(
    request: UserRequest,
    items: List[DraftItem],
    n_personas: int | None = None,
) -> Tuple[PersonaValidationResponse, TokenUsage]:
    """Run persona-based validation on a set of items.

    Args:
        request: User request (provides target_population, cultural_group, model).
        items: Items to validate.
        n_personas: Override settings.PERSONA_VALIDATOR_PERSONAS for testing.

    Returns:
        (PersonaValidationResponse, accumulated TokenUsage)
    """
    if n_personas is None:
        n_personas = settings.PERSONA_VALIDATOR_PERSONAS
    if n_personas <= 0 or len(items) == 0:
        return (
            PersonaValidationResponse(
                summary="Persona validator disabled or no items to rate.",
            ),
            TokenUsage(),
        )

    logger.info(
        "PERSONA_VALIDATOR start n_personas=%d n_items=%d",
        n_personas, len(items),
    )

    total_usage = TokenUsage(model_name="persona_validator")

    # 1. Generate personas
    personas, gen_usage = _generate_personas_via_llm(request, n_personas)
    total_usage.input_tokens += gen_usage.input_tokens
    total_usage.output_tokens += gen_usage.output_tokens
    total_usage.total_tokens += gen_usage.total_tokens

    # 2. Rate items per persona, in parallel
    all_ratings: List[PersonaRating] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(personas), 4)) as ex:
        futures = [
            ex.submit(_rate_items_for_persona, request, p, items) for p in personas
        ]
        for fut in concurrent.futures.as_completed(futures):
            try:
                resp, usage = fut.result()
                total_usage.input_tokens += usage.input_tokens
                total_usage.output_tokens += usage.output_tokens
                total_usage.total_tokens += usage.total_tokens
                for r in resp.ratings:
                    if 0 <= r.item_index < len(items):
                        all_ratings.append(
                            PersonaRating(
                                persona_label=resp.persona_label,
                                item_index=r.item_index,
                                rating=int(r.rating),
                                interpretation=r.interpretation,
                            )
                        )
            except Exception as e:
                logger.warning("Persona rating call failed: %s", e)

    # 3. Per-item SD across personas → flag items with SD ≥ threshold
    threshold = settings.PERSONA_VALIDATOR_DISAGREEMENT_THRESHOLD
    by_item: dict[int, List[int]] = {}
    for r in all_ratings:
        by_item.setdefault(r.item_index, []).append(r.rating)

    flagged: List[int] = []
    sds: List[float] = []
    for idx, ratings in by_item.items():
        if len(ratings) >= 2:
            sd = statistics.pstdev(ratings)
            sds.append(sd)
            if sd >= threshold:
                flagged.append(idx)
    flagged.sort()

    interpretive_var = float(statistics.fmean(sds)) if sds else 0.0

    if flagged:
        summary = (
            f"{len(flagged)} of {len(items)} items flagged for ambiguity (SD ≥ "
            f"{threshold} across {len(personas)} personas)."
        )
    else:
        summary = (
            f"All {len(items)} items interpreted consistently across {len(personas)} personas."
        )

    logger.info(
        "PERSONA_VALIDATOR done flagged=%d/%d interpretive_variance=%.2f",
        len(flagged), len(items), interpretive_var,
    )

    return (
        PersonaValidationResponse(
            personas=personas,
            ratings=all_ratings,
            flagged_items=flagged,
            interpretive_variance=interpretive_var,
            summary=summary,
        ),
        total_usage,
    )
