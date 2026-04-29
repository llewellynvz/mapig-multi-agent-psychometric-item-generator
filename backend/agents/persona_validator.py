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
    interpretation: str = Field(..., min_length=3, max_length=1000)


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
    """Generate `n_personas` deterministic, richer persona descriptors.

    Mock-mode fallback only. In production, `_generate_personas_via_llm` writes
    far more detailed personas via gpt-5.4-mini.
    """
    cg = cultural_group or "general"
    base = [
        (
            f"22-year-old early-career {target_population} member (junior level), "
            f"some tertiary education, English as a second language, {cg} background, "
            f"living with extended family in an urban township; uses English at work "
            f"but mixes with home language socially."
        ),
        (
            f"58-year-old experienced {target_population} member (senior level), "
            f"completed secondary school, fluent reader, {cg} background, "
            f"raised in a rural area before relocating, navigates work life with traditional values."
        ),
        (
            f"34-year-old mid-career {target_population} member from a {cg} sub-group, "
            f"university degree, second-generation urban professional, juggles "
            f"family obligations and work pressure, comfortable with both global and local norms."
        ),
    ]
    while len(base) < n_personas:
        base.append(
            f"Additional respondent variant {len(base) + 1} from {target_population} ({cg}) "
            f"with mid-level literacy and a focus on work-family balance."
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
        "You generate detailed respondent personas for cognitive-interview-style "
        "survey item validation. Each persona is a 2-3 sentence biographical sketch "
        "covering: age + life stage, occupation/role with seniority, education + "
        "literacy level, primary language(s) and English fluency, cultural "
        "reference frame, current life context (family, work pressure, health, "
        "geography). The personas must be DISTINCT — they should produce DIFFERENT "
        "interpretations of the same item. Avoid generic descriptions."
    )
    human = (
        f"Generate exactly {n} richly detailed respondent personas for a survey "
        f"targeted at: target_population={request.target_population!r} "
        f"cultural_group={request.cultural_group!r}.\n\n"
        f"Each persona should be 2–3 sentences with concrete biographical detail. "
        f"Cover at least:\n"
        f"  - The YOUNGER end of the population (early 20s, less life experience).\n"
        f"  - The OLDER end (50s/60s, different cultural reference frame).\n"
        f"  - A culturally or linguistically DISTINCT sub-group whose comprehension "
        f"may differ (e.g., second-language English, rural vs urban, different "
        f"socioeconomic position).\n"
        f"Personas should expose how SAME ITEMS may be READ DIFFERENTLY.\n\n"
        f"Return JSON with a 'personas' field containing exactly {n} multi-sentence strings."
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
        # Deterministic mock: rating cycles over 1..5 to produce disagreement.
        # Use a short label snippet in the interpretation to stay well under
        # the 1000-char schema limit regardless of how long the persona is.
        label_snippet = persona_label[:60].rsplit(" ", 1)[0]
        offset = abs(hash(persona_label)) % 5
        ratings = [
            _PersonaItemRating(
                item_index=i,
                rating=((i + offset) % 5) + 1,
                interpretation=(
                    f"Mock interpretation for {label_snippet}: "
                    f"item {i} reads as a self-report query in this persona's voice."
                ),
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
        f"You are this persona, embodying their biography fully:\n\n"
        f"PERSONA: {persona_label}\n\n"
        f"For EACH of the {len(items)} items below, produce a rating (1-5) AND a "
        f"2-4 sentence cognitive-interview-style interpretation that:\n"
        f"  1. States what you (as the persona) thought the item was asking.\n"
        f"  2. Mentions any alternative reading you considered.\n"
        f"  3. Gives a concrete personal reason for the rating you chose.\n"
        f"  4. Flags any wording that was unclear or culturally jarring for you.\n\n"
        f"Different items should produce DIFFERENT ratings — vary based on your "
        f"persona's specific life context. Identical ratings across all items "
        f"will be flagged as a failure.\n\n"
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
