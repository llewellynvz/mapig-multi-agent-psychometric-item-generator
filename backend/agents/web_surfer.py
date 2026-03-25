from __future__ import annotations

import hashlib
import json
import logging
import time
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
                _valid_evidence_types = {"theoretical_definition", "dimensions", "measurement_precedent", "boundary_conditions", "cultural_context"}
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


def _synthesize_cultural_query(request: UserRequest) -> str:
    """Build a Perplexity query for cultural norms and sensitivities."""
    parts = [
        f'Describe cultural norms, values, and measurement sensitivities for "{request.cultural_group}".',
        f'Context: We are developing a psychometric scale measuring "{request.construct_name}" '
        f'for {request.target_population}.',
        "",
        "Focus on:",
        "(1) Cultural values and communication styles relevant to self-report surveys",
        "(2) Topics or concepts that may be sensitive or taboo",
        "(3) Language considerations (directness, formality, idioms to avoid)",
        "(4) Work culture norms if applicable",
        "(5) Religious or social customs that affect how people respond to survey items",
        "",
        "Keep response factual and evidence-based. Cite academic sources where possible.",
    ]
    return "\n".join(parts)


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

    _t0 = time.perf_counter()
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    _elapsed = time.perf_counter() - _t0
    log.info("PERPLEXITY_CALL elapsed=%.1fs status=%d", _elapsed, resp.status_code)

    # Task #4: Process LLM response for structured evidence
    evidence = _process_perplexity_response(data)

    # 3A: Supplement from search_results if structured parsing yielded < 20 chunks
    if len(evidence) < 20:
        search_results = data.get("search_results") or []
        seen_urls = {e.url_or_docref for e in evidence}
        for sr in search_results:
            if len(evidence) >= 20:
                break
            u = (sr.get("url") or "").strip()
            if not u or u in seen_urls:
                continue
            title = (sr.get("title") or "Web result").strip()
            snippet = (sr.get("snippet") or "").strip()
            if not snippet:
                continue
            evidence.append(
                EvidenceChunk(
                    source_id=_source_id(u),
                    title=title,
                    snippet=snippet[:240] + ("…" if len(snippet) > 240 else ""),
                    url_or_docref=u,
                    quote=snippet[:500],
                )
            )
            seen_urls.add(u)
        if len(evidence) < 20:
            log.warning("EVIDENCE_DEPTH_WARNING evidence=%d after supplementing (minimum recommended: 20)", len(evidence))

    # Retry loop: broaden search if below minimum evidence threshold
    retry_count = 0
    while len(evidence) < settings.EVIDENCE_MIN_CHUNKS and retry_count < settings.EVIDENCE_MAX_RETRIES:
        retry_count += 1
        log.info("EVIDENCE_RETRY attempt=%d current=%d target=%d", retry_count, len(evidence), settings.EVIDENCE_MIN_CHUNKS)

        # Broadened query: drop specific theoretical terms, use generic measurement language
        broad_query_parts = [
            f'Find academic research on measuring "{request.construct_name}".',
            f"Definition: {request.construct_definition}",
            f"Target population: {request.target_population}",
            "",
            "Search broadly for:",
            "(1) Scale development and validation studies",
            "(2) Psychometric properties and factor analysis",
            "(3) Cross-cultural adaptation and translation",
            "(4) Systematic reviews or meta-analyses",
            "(5) Related measurement frameworks",
        ]
        if retry_count >= 2:
            broad_query_parts.append("(6) Handbook chapters, test reviews, and measurement compendia")

        broad_query = "\n".join(broad_query_parts)

        retry_payload = {
            "model": settings.PERPLEXITY_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": broad_query},
            ],
            "temperature": 0,
            "web_search_options": {
                "search_mode": settings.PERPLEXITY_SEARCH_MODE,
                "num_search_results": settings.PERPLEXITY_MAX_RESULTS,
                "search_domain_filter": domains,
            },
        }

        try:
            _t0_retry = time.perf_counter()
            with httpx.Client(timeout=30) as client:
                retry_resp = client.post(url, headers=headers, json=retry_payload)
                retry_resp.raise_for_status()
                retry_data = retry_resp.json()
            _elapsed_retry = time.perf_counter() - _t0_retry
            log.info("PERPLEXITY_CALL elapsed=%.1fs status=%d (retry %d)", _elapsed_retry, retry_resp.status_code, retry_count)

            retry_evidence = _process_perplexity_response(retry_data)

            # Deduplicate by URL
            seen_urls = {e.url_or_docref for e in evidence}
            for chunk in retry_evidence:
                if chunk.url_or_docref not in seen_urls:
                    evidence.append(chunk)
                    seen_urls.add(chunk.url_or_docref)

            # Also supplement from search_results
            for sr in retry_data.get("search_results") or []:
                u = (sr.get("url") or "").strip()
                if not u or u in seen_urls:
                    continue
                title = (sr.get("title") or "Web result").strip()
                snippet = (sr.get("snippet") or "").strip()
                if not snippet:
                    continue
                evidence.append(
                    EvidenceChunk(
                        source_id=_source_id(u),
                        title=title,
                        snippet=snippet[:240] + ("…" if len(snippet) > 240 else ""),
                        url_or_docref=u,
                        quote=snippet[:500],
                    )
                )
                seen_urls.add(u)

            log.info("EVIDENCE_RETRY done attempt=%d evidence=%d", retry_count, len(evidence))
        except Exception as e:
            log.warning("EVIDENCE_RETRY failed attempt=%d: %s", retry_count, e)
            break

    if len(evidence) < settings.EVIDENCE_MIN_CHUNKS:
        log.warning("EVIDENCE_DEPTH_BELOW_MINIMUM evidence=%d minimum=%d", len(evidence), settings.EVIDENCE_MIN_CHUNKS)

    log.info("PERPLEXITY_SEARCH done evidence=%d", len(evidence))

    # Cultural context search (if cultural_group is set)
    if request.cultural_group:
        try:
            cultural_query = _synthesize_cultural_query(request)
            cultural_payload = {
                "model": settings.PERPLEXITY_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a cultural psychology expert. Provide evidence-based cultural context for psychometric item development."},
                    {"role": "user", "content": cultural_query},
                ],
                "temperature": 0,
                "web_search_options": {
                    "search_mode": settings.PERPLEXITY_SEARCH_MODE,
                    "num_search_results": 5,
                    "search_domain_filter": domains,
                },
            }
            _t0_cultural = time.perf_counter()
            with httpx.Client(timeout=30) as client:
                cultural_resp = client.post(url, headers=headers, json=cultural_payload)
                cultural_resp.raise_for_status()
                cultural_data = cultural_resp.json()
            _elapsed_cultural = time.perf_counter() - _t0_cultural
            log.info("PERPLEXITY_CALL elapsed=%.1fs status=%d (cultural)", _elapsed_cultural, cultural_resp.status_code)

            # Extract cultural context as evidence chunks
            cultural_content = cultural_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if cultural_content:
                evidence.append(
                    EvidenceChunk(
                        source_id=f"cultural:{_source_id(request.cultural_group)}",
                        title=f"Cultural context: {request.cultural_group}",
                        snippet=cultural_content[:240] + ("…" if len(cultural_content) > 240 else ""),
                        url_or_docref="perplexity:cultural_search",
                        quote=cultural_content[:500],
                        evidence_type="cultural_context",
                    )
                )
                log.info("PERPLEXITY_CULTURAL_SEARCH done cultural_group=%s", request.cultural_group)
        except Exception as e:
            log.warning("PERPLEXITY_CULTURAL_SEARCH failed: %s", e)

    return RetrievalResponse(evidence=evidence)
