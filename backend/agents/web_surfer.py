from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List

import httpx

from backend.agents.prompt_loader import load_prompt
from backend.schemas import EvidenceChunk, RetrievalResponse, UserRequest
from backend.settings import settings

log = logging.getLogger("lmaig.web_surfer")


def _domain_filter(request: UserRequest) -> List[str]:
    """Return the domain allowlist.

    We *require* an allowlist to honor the "approved sources only" constraint.
    """
    if request.approved_domains:
        return request.approved_domains

    domains = settings.perplexity_domains()
    if domains:
        return domains

    raise RuntimeError(
        "Perplexity retrieval requires an approved domain allowlist. "
        "Set PERPLEXITY_DOMAIN_FILTER in .env (comma-separated domains) "
        "or pass approved_domains in the request body."
    )


def _source_id(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return f"web:{h}"


def _synthesize_theoretical_query(request: UserRequest, boundary: str, exclude: str) -> str:
    """Synthesize an enhanced query for theoretical model discovery.

    Task #4: Multi-stage search strategy to find theoretical definitions,
    conceptual frameworks, and measurement precedents.
    """
    query_parts = []

    # Core construct information
    query_parts.append(f'Find the theoretical definition and conceptual model for "{request.construct_name}".')
    query_parts.append(f'The construct is defined as: {request.construct_definition}')

    # Multi-stage search guidance
    query_parts.append('\nFocus your search on:')
    query_parts.append('(1) Authoritative academic definitions from seminal theoretical papers')
    query_parts.append('(2) Theoretical frameworks and models that structure this construct')
    query_parts.append('(3) Subcomponents, dimensions, or facets identified in the theoretical literature')
    query_parts.append('(4) How this construct differs from similar or neighboring constructs')
    query_parts.append('(5) Validated measurement instruments (names only, do not quote items)')

    # Additional context
    if boundary:
        query_parts.append(f'\n{boundary}')

    query_parts.append(f'\nTarget population: {request.target_population}')

    if request.native_construct:
        query_parts.append(f'Native language label: {request.native_construct}')

    if request.example_item:
        query_parts.append(f'Example item style: {request.example_item}')

    if request.constraints:
        query_parts.append(f'Constraints: {", ".join(request.constraints)}')

    if exclude:
        query_parts.append(f'\n{exclude}')

    # Prioritization guidance
    query_parts.append('\nPrioritize theory and conceptual papers over measurement-only papers.')

    return '\n'.join(query_parts)


def _process_perplexity_response(data: Dict[str, Any]) -> List[EvidenceChunk]:
    """Process Perplexity API response to extract structured evidence.

    Task #4: Extract evidence chunks with theoretical metadata from LLM response.
    Falls back to search results if LLM doesn't return structured JSON.
    """
    evidence: List[EvidenceChunk] = []

    # Try to parse LLM response for structured evidence
    try:
        message_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if message_content:
            # Look for JSON in the response
            json_start = message_content.find("{")
            json_end = message_content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = message_content[json_start:json_end]
                parsed = json.loads(json_str)

                # Process evidence chunks with enhanced metadata
                _valid_evidence_types = {"theoretical_definition", "dimensions", "measurement_precedent", "boundary_conditions"}
                for chunk_data in parsed.get("evidence", []):
                    raw_type = chunk_data.get("evidence_type")
                    evidence.append(
                        EvidenceChunk(
                            source_id=chunk_data.get("source_id", ""),
                            title=chunk_data.get("title", ""),
                            snippet=chunk_data.get("quote", "")[:240] + ("…" if len(chunk_data.get("quote", "")) > 240 else ""),
                            url_or_docref=chunk_data.get("url_or_docref", ""),
                            quote=chunk_data.get("quote", ""),
                            evidence_type=raw_type if raw_type in _valid_evidence_types else None,
                            authors=chunk_data.get("authors"),
                            theoretical_model=chunk_data.get("theoretical_model"),
                            dimensions=chunk_data.get("dimensions"),
                        )
                    )

                log.info("PERPLEXITY parsed structured evidence chunks=%d", len(evidence))
                return evidence

    except Exception as e:
        log.warning("PERPLEXITY failed to parse structured response: %s", e)

    # Fallback: use search_results if LLM didn't return structured JSON
    results = data.get("search_results") or []
    log.info("PERPLEXITY fallback to search_results count=%d", len(results))

    for sr in results:
        u = (sr.get("url") or "").strip()
        if not u:
            continue
        title = (sr.get("title") or "Web result").strip()
        snippet = (sr.get("snippet") or "").strip()
        quote = snippet[:500] if snippet else ""

        evidence.append(
            EvidenceChunk(
                source_id=_source_id(u),
                title=title,
                snippet=snippet[:240] + ("…" if len(snippet) > 240 else ""),
                url_or_docref=u,
                quote=quote,
                # No theoretical metadata in fallback mode
                evidence_type=None,
                authors=None,
                theoretical_model=None,
                dimensions=None,
            )
        )

    return evidence


def surf(request: UserRequest) -> RetrievalResponse:
    """Use Perplexity academic search to retrieve evidence chunks."""
    if not settings.PERPLEXITY_API_KEY:
        raise RuntimeError(
            "PERPLEXITY_API_KEY is not set but SEARCH_PROVIDER requires Perplexity."
        )

    system_prompt = load_prompt("web_surfer.md")

    exclude = ""
    if request.exclude_sources:
        exclude = " Avoid or exclude: " + ", ".join(request.exclude_sources) + "."
    boundary = ""
    if request.construct_exclusions:
        boundary = f"Boundary exclusions: {request.construct_exclusions}.\n"

    # Task #4: Enhanced query synthesis for theoretical model discovery
    user_query = _synthesize_theoretical_query(request, boundary, exclude)

    domains = _domain_filter(request)
    log.info("PERPLEXITY_SEARCH start mode=%s model=%s domains=%s", settings.PERPLEXITY_SEARCH_MODE, settings.PERPLEXITY_MODEL, domains)

    payload = {
        "model": settings.PERPLEXITY_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        "temperature": 0,
        "web_search_options": {
            "search_mode": settings.PERPLEXITY_SEARCH_MODE,
            "num_search_results": settings.PERPLEXITY_MAX_RESULTS,
            "search_domain_filter": domains,
        },
    }

    url = settings.PERPLEXITY_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Task #4: Process LLM response for structured evidence
    evidence = _process_perplexity_response(data)
    log.info("PERPLEXITY_SEARCH done evidence=%d", len(evidence))

    return RetrievalResponse(evidence=evidence)
