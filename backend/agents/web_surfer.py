from __future__ import annotations

import hashlib
import logging
from typing import List

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

    user_query = (
        f"Target construct: {request.construct_name}.\n"
        f"Definition: {request.construct_definition}.\n"
        f"{boundary}"
        f"Population: {request.target_population}.\n"
        f"Optional native label: {request.native_construct or ''}.\n"
        f"Optional example item: {request.example_item or ''}.\n"
        f"Constraints: {', '.join(request.constraints) if request.constraints else ''}.\n"
        f"{exclude}"
    )

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

    results = data.get("search_results") or []
    log.info("PERPLEXITY_SEARCH done results=%d", len(results))
    evidence: List[EvidenceChunk] = []
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
            )
        )

    return RetrievalResponse(evidence=evidence)
