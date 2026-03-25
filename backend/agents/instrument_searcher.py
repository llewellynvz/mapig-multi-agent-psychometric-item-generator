"""Instrument search engine for dynamic comparison instrument discovery.

Phase 9 Plan 01: Hybrid search strategy combining Perplexity Academic search
with hardcoded fallback defaults across 5 psychological domains.
"""
from __future__ import annotations

import json
import logging
from typing import Literal, Optional

import httpx
from pydantic import ValidationError

from backend.schemas import ComparisonInstrument
from backend.settings import settings

log = logging.getLogger("lmaig.instrument_searcher")


def _safe_int(val) -> Optional[int]:
    """Safely convert LLM output to int, returning None for non-numeric values."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def search_instruments(
    construct_name: str,
    construct_definition: str
) -> tuple[ComparisonInstrument, ComparisonInstrument]:
    """Search for convergent and discriminant comparison instruments.

    Returns exactly 2 instruments:
    - Convergent: Instrument measuring the same construct
    - Discriminant: Instrument measuring a related-but-distinct construct

    Args:
        construct_name: Name of the target construct
        construct_definition: Operational definition of the construct

    Returns:
        (convergent_instrument, discriminant_instrument)
    """
    log.info("INSTRUMENT_SEARCH start construct=%s", construct_name)

    # Try Perplexity search first
    convergent = _search_perplexity_instrument(construct_name, "convergent")
    discriminant = _search_perplexity_instrument(construct_name, "discriminant")

    # Fall back to defaults if either search failed
    if convergent is None or discriminant is None:
        log.info("INSTRUMENT_SEARCH fallback to defaults (perplexity_failed)")
        convergent_default, discriminant_default = _get_hardcoded_defaults(construct_name)
        if convergent is None:
            convergent = convergent_default
        if discriminant is None:
            discriminant = discriminant_default

    # Phase 2: Try to extract actual items for each instrument
    convergent = _fetch_instrument_items(convergent)
    discriminant = _fetch_instrument_items(discriminant)

    log.info(
        "INSTRUMENT_SEARCH done convergent=%s (items=%s) discriminant=%s (items=%s)",
        convergent.name, len(convergent.items) if convergent.items else 0,
        discriminant.name, len(discriminant.items) if discriminant.items else 0,
    )
    return convergent, discriminant


def _search_perplexity_instrument(
    construct_name: str,
    search_type: Literal["convergent", "discriminant"]
) -> Optional[ComparisonInstrument]:
    """Search Perplexity Academic for a specific instrument type.

    Args:
        construct_name: Target construct name
        search_type: "convergent" for same construct, "discriminant" for related-but-distinct

    Returns:
        ComparisonInstrument if found and not blocked, None otherwise
    """
    if not settings.PERPLEXITY_API_KEY:
        log.warning("PERPLEXITY_INSTRUMENT_SEARCH skipped (no API key)")
        return None

    # Build query based on search type
    if search_type == "convergent":
        query = (
            f"Find a validated psychometric instrument that directly measures {construct_name}. "
            f"Return structured metadata including: instrument name, author(s), publication year, "
            f"construct measured, number of items, and key psychometric properties (reliability, validity). "
            f"Prioritize widely-used, well-validated instruments from peer-reviewed sources."
        )
    else:  # discriminant
        query = (
            f"Find a validated psychometric instrument that measures a construct related to but distinct from {construct_name}. "
            f"The instrument should measure something conceptually adjacent (e.g., if {construct_name} is self-esteem, "
            f"find instruments measuring depression, anxiety, or life satisfaction - not self-esteem itself). "
            f"Return structured metadata including: instrument name, author(s), publication year, "
            f"construct measured, number of items, and why this construct is related but distinct."
        )

    # Use academic domain filter if configured
    domains = settings.perplexity_domains()

    payload = {
        "model": settings.PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a psychometric instrument search assistant. Return instrument metadata "
                    "in JSON format with these fields: name, authors, year, construct, item_count, "
                    "psychometric_properties, similarity_rationale. Do not include instruments from "
                    "commercial publishers that require purchase (e.g., Pearson, PAR, MHS, WPS, Hogrefe)."
                )
            },
            {"role": "user", "content": query}
        ],
        "temperature": 0,
    }

    # Add domain filter if configured
    if domains:
        payload["web_search_options"] = {
            "search_mode": settings.PERPLEXITY_SEARCH_MODE,
            "num_search_results": settings.PERPLEXITY_MAX_RESULTS,
            "search_domain_filter": domains,
        }

    url = settings.PERPLEXITY_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Parse LLM response
        message_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not message_content:
            log.warning("PERPLEXITY_INSTRUMENT_SEARCH no content returned")
            return None

        # Extract JSON from response
        json_start = message_content.find("{")
        json_end = message_content.rfind("}") + 1
        if json_start < 0 or json_end <= json_start:
            log.warning("PERPLEXITY_INSTRUMENT_SEARCH no JSON found in response")
            return None

        json_str = message_content[json_start:json_end]
        parsed = json.loads(json_str)

        # Check for blocked publishers
        citation = f"{parsed.get('authors', '')} ({parsed.get('year', '')})"
        if _is_blocked_publisher(citation, message_content):
            log.info("PERPLEXITY_INSTRUMENT_SEARCH blocked publisher detected, skipping")
            return None

        # Build ComparisonInstrument
        instrument = ComparisonInstrument(
            name=parsed.get("name", "Unknown Instrument"),
            measured_construct=parsed.get("construct", construct_name),
            source_citation=citation,
            publication_year=_safe_int(parsed.get("year")),
            sample_items_count=_safe_int(parsed.get("item_count")),
            psychometric_properties=parsed.get("psychometric_properties"),
            similarity_rationale=parsed.get("similarity_rationale")
        )

        log.info("PERPLEXITY_INSTRUMENT_SEARCH success type=%s instrument=%s", search_type, instrument.name)
        return instrument

    except (httpx.TimeoutException, httpx.HTTPStatusError, json.JSONDecodeError, KeyError, ValidationError) as e:
        log.warning("PERPLEXITY_INSTRUMENT_SEARCH failed: %s", e)
        return None


def _fetch_instrument_items(instrument: ComparisonInstrument) -> ComparisonInstrument:
    """Search Perplexity for the actual items/questions of a published instrument.

    Queries Perplexity Academic for the item text of the instrument. If found,
    returns a copy of the instrument with the `items` field populated.

    Args:
        instrument: The instrument to fetch items for

    Returns:
        Updated ComparisonInstrument (with items if found, unchanged otherwise)
    """
    if not settings.PERPLEXITY_API_KEY:
        return instrument

    query = (
        f"List ALL the exact item texts (questions/statements) from the "
        f"'{instrument.name}' psychometric instrument that measures {instrument.measured_construct}. "
        f"Return ONLY the item texts as a JSON array of strings, e.g. "
        f'["I feel satisfied with my life", "In most ways my life is close to my ideal"]. '
        f"Include every item. Do not paraphrase — use the exact published wording. "
        f"If items are behind a paywall or not publicly available, return an empty array []."
    )

    payload = {
        "model": settings.PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a psychometric instrument specialist. Return instrument items "
                    "as a JSON array of strings. Only include items whose exact wording is "
                    "publicly available in peer-reviewed publications or supplementary materials. "
                    "Do not fabricate or paraphrase items."
                ),
            },
            {"role": "user", "content": query},
        ],
        "temperature": 0,
    }

    # Do NOT apply academic domain filter for item fetching — items may be on
    # general web (ResearchGate PDFs, course pages, open-access supplements)
    payload["web_search_options"] = {
        "search_mode": "web",  # General web, not academic-only
        "num_search_results": 10,
    }

    url = settings.PERPLEXITY_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    def _try_fetch(p: dict) -> list | None:
        """Attempt item fetch and return parsed items or None."""
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, headers=headers, json=p)
                resp.raise_for_status()
                data = resp.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                return None

            arr_start = content.find("[")
            arr_end = content.rfind("]") + 1
            if arr_start < 0 or arr_end <= arr_start:
                return None

            items = json.loads(content[arr_start:arr_end])
            if (
                isinstance(items, list)
                and len(items) >= 3
                and all(isinstance(it, str) and len(it.strip()) > 5 for it in items)
            ):
                return [it.strip() for it in items]
            return None
        except (httpx.TimeoutException, httpx.HTTPStatusError, json.JSONDecodeError) as e:
            log.warning("FETCH_ITEMS attempt failed for %s: %s", instrument.name, e)
            return None

    # Attempt 1: standard query
    items = _try_fetch(payload)
    if items:
        log.info("FETCH_ITEMS success instrument=%s items=%d", instrument.name, len(items))
        return instrument.model_copy(update={"items": items})

    # Attempt 2: broader query targeting PDFs and full texts
    log.info("FETCH_ITEMS retry with broader query for %s", instrument.name)
    retry_query = (
        f'"{instrument.name}" questionnaire items full text. '
        f"List ALL exact item texts (questions/statements) from this instrument. "
        f"Return ONLY a JSON array of strings. If not available, return []."
    )
    retry_payload = {
        "model": settings.PERPLEXITY_MODEL,
        "messages": [
            {"role": "system", "content": payload["messages"][0]["content"]},
            {"role": "user", "content": retry_query},
        ],
        "temperature": 0,
        "web_search_options": {"search_mode": "web", "num_search_results": 15},
    }
    items = _try_fetch(retry_payload)
    if items:
        log.info("FETCH_ITEMS retry success instrument=%s items=%d", instrument.name, len(items))
        return instrument.model_copy(update={"items": items})

    log.info("FETCH_ITEMS published items unavailable for %s (likely copyrighted or paywalled)", instrument.name)
    return instrument


def _get_hardcoded_defaults(construct_name: str) -> tuple[ComparisonInstrument, ComparisonInstrument]:
    """Get fallback instruments based on domain heuristics.

    Covers 5 psychological domains: personality, clinical, organizational, social, cognitive.

    Args:
        construct_name: Target construct name for domain matching

    Returns:
        (convergent_instrument, discriminant_instrument)
    """
    construct_lower = construct_name.lower()

    # Personality domain
    if any(kw in construct_lower for kw in ["personality", "extraversion", "openness", "conscientiousness", "agreeableness", "neuroticism", "big five"]):
        return (
            ComparisonInstrument(
                name="IPIP-NEO",
                measured_construct="Big Five personality traits",
                source_citation="Goldberg, L. R. (1999). A broad-bandwidth, public domain, personality inventory measuring the lower-level facets of several five-factor models. Personality Psychology in Europe, 7(1), 7-28.",
                publication_year=1999,
                sample_items_count=50,
                psychometric_properties="α = 0.77-0.89 across dimensions, well-established construct validity",
                similarity_rationale="Measures personality traits similar to target construct"
            ),
            ComparisonInstrument(
                name="PHQ-9",
                measured_construct="depression severity",
                source_citation="Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001). The PHQ-9: validity of a brief depression severity measure. Journal of General Internal Medicine, 16(9), 606-613.",
                publication_year=2001,
                sample_items_count=9,
                psychometric_properties="α = 0.89, sensitivity 88%, specificity 88% for major depression",
                similarity_rationale="Related to personality but measures distinct clinical construct (depression)"
            )
        )

    # Clinical domain
    if any(kw in construct_lower for kw in ["depression", "anxiety", "mood", "symptom", "mental health", "clinical", "disorder"]):
        return (
            ComparisonInstrument(
                name="PHQ-9",
                measured_construct="depression severity",
                source_citation="Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001). The PHQ-9: validity of a brief depression severity measure. Journal of General Internal Medicine, 16(9), 606-613.",
                publication_year=2001,
                sample_items_count=9,
                psychometric_properties="α = 0.89, sensitivity 88%, specificity 88% for major depression",
                similarity_rationale="Directly measures depression/clinical symptoms"
            ),
            ComparisonInstrument(
                name="Rosenberg Self-Esteem Scale",
                measured_construct="self-esteem",
                source_citation="Rosenberg, M. (1965). Society and the adolescent self-image. Princeton, NJ: Princeton University Press.",
                publication_year=1965,
                sample_items_count=10,
                psychometric_properties="α = 0.77-0.88, test-retest reliability = 0.82-0.88",
                similarity_rationale="Related to mood/clinical constructs but measures distinct positive self-evaluation"
            )
        )

    # Organizational domain
    if any(kw in construct_lower for kw in ["work", "job", "engagement", "burnout", "organizational", "employee", "occupation"]):
        return (
            ComparisonInstrument(
                name="Utrecht Work Engagement Scale (UWES-9)",
                measured_construct="work engagement",
                source_citation="Schaufeli, W. B., Bakker, A. B., & Salanova, M. (2006). The measurement of work engagement with a short questionnaire: A cross-national study. Educational and Psychological Measurement, 66(4), 701-716.",
                publication_year=2006,
                sample_items_count=9,
                psychometric_properties="α = 0.85-0.92 across dimensions (vigor, dedication, absorption)",
                similarity_rationale="Measures positive work-related well-being"
            ),
            ComparisonInstrument(
                name="Maslach Burnout Inventory (MBI-GS)",
                measured_construct="burnout",
                source_citation="Schaufeli, W. B., Leiter, M. P., Maslach, C., & Jackson, S. E. (1996). Maslach Burnout Inventory-General Survey. In C. Maslach, S. E. Jackson, & M. P. Leiter (Eds.), MBI Manual (3rd ed.). Consulting Psychologists Press.",
                publication_year=1996,
                sample_items_count=16,
                psychometric_properties="α = 0.87-0.89 across exhaustion, cynicism, professional efficacy",
                similarity_rationale="Related to work constructs but measures negative work-related state (opposite valence)"
            )
        )

    # Social domain
    if any(kw in construct_lower for kw in ["social", "loneliness", "relationship", "interpersonal", "isolation", "connection"]):
        return (
            ComparisonInstrument(
                name="UCLA Loneliness Scale (Version 3)",
                measured_construct="loneliness",
                source_citation="Russell, D. W. (1996). UCLA Loneliness Scale (Version 3): Reliability, validity, and factor structure. Journal of Personality Assessment, 66(1), 20-40.",
                publication_year=1996,
                sample_items_count=20,
                psychometric_properties="α = 0.89-0.94, test-retest reliability = 0.73",
                similarity_rationale="Measures subjective social isolation"
            ),
            ComparisonInstrument(
                name="Rosenberg Self-Esteem Scale",
                measured_construct="self-esteem",
                source_citation="Rosenberg, M. (1965). Society and the adolescent self-image. Princeton, NJ: Princeton University Press.",
                publication_year=1965,
                sample_items_count=10,
                psychometric_properties="α = 0.77-0.88, test-retest reliability = 0.82-0.88",
                similarity_rationale="Related to social constructs but measures distinct self-evaluation"
            )
        )

    # Cognitive domain
    if any(kw in construct_lower for kw in ["cognition", "cognitive", "thinking", "intelligence", "reasoning", "memory", "attention"]):
        return (
            ComparisonInstrument(
                name="Need for Cognition Scale",
                measured_construct="need for cognition",
                source_citation="Cacioppo, J. T., Petty, R. E., & Kao, C. F. (1984). The efficient assessment of need for cognition. Journal of Personality Assessment, 48(3), 306-307.",
                publication_year=1984,
                sample_items_count=18,
                psychometric_properties="α = 0.85-0.90, test-retest reliability = 0.88",
                similarity_rationale="Measures individual differences in cognitive engagement"
            ),
            ComparisonInstrument(
                name="Big Five Inventory - Openness Subscale",
                measured_construct="openness to experience",
                source_citation="John, O. P., Donahue, E. M., & Kentle, R. L. (1991). The Big Five Inventory--Versions 4a and 54. Berkeley, CA: University of California, Berkeley, Institute of Personality and Social Research.",
                publication_year=1991,
                sample_items_count=10,
                psychometric_properties="α = 0.79-0.81 for openness dimension",
                similarity_rationale="Related to cognitive constructs but measures broader personality trait"
            )
        )

    # Fallback (unmatched constructs) - use widely applicable instruments
    return (
        ComparisonInstrument(
            name="Rosenberg Self-Esteem Scale",
            measured_construct="self-esteem",
            source_citation="Rosenberg, M. (1965). Society and the adolescent self-image. Princeton, NJ: Princeton University Press.",
            publication_year=1965,
            sample_items_count=10,
            psychometric_properties="α = 0.77-0.88, test-retest reliability = 0.82-0.88",
            similarity_rationale="General positive self-evaluation construct"
        ),
        ComparisonInstrument(
            name="PHQ-9",
            measured_construct="depression severity",
            source_citation="Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001). The PHQ-9: validity of a brief depression severity measure. Journal of General Internal Medicine, 16(9), 606-613.",
            publication_year=2001,
            sample_items_count=9,
            psychometric_properties="α = 0.89, sensitivity 88%, specificity 88% for major depression",
            similarity_rationale="General negative affect/clinical construct"
        )
    )


def _is_blocked_publisher(citation: str, content: str) -> bool:
    """Check if citation or content contains blocked publisher domains.

    Args:
        citation: Citation string to check
        content: Full response content to check

    Returns:
        True if any blocked domain is found, False otherwise
    """
    blocked = settings.publisher_blocklist_domains()
    combined_text = (citation + " " + content).lower()

    for domain in blocked:
        if domain.lower() in combined_text:
            return True

    return False
