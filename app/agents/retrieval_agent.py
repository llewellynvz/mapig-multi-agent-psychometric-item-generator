from __future__ import annotations
from app.logging_utils import step

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from app.schemas import EvidenceChunk, RetrievalResponse, UserRequest
from app.settings import settings


def _tokenize(text: str) -> List[str]:
    return [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if t]


def _score(query_tokens: set[str], doc_tokens: set[str]) -> int:
    return len(query_tokens.intersection(doc_tokens))


def retrieve_evidence(request: UserRequest, top_k: int = 5) -> RetrievalResponse:
    """Retrieve evidence chunks from local allowlisted sources only."""
    # Use os.getcwd() for project root (Vercel sets cwd to project base)
    sources_dir = Path(os.getcwd()) / "data" / "approved_sources"

    if not sources_dir.exists():
        # Fallback: relative to this file
        sources_dir = Path(__file__).parent.parent.parent / "data" / "approved_sources"

    if not sources_dir.exists():
        raise FileNotFoundError(f"Approved sources directory not found. Tried: {sources_dir}")

    base_dir = sources_dir

    query_parts = [
        request.construct_name,
        request.construct_definition,
        request.native_construct or "",
        request.target_population,
        request.example_item or "",
        " ".join(request.constraints),
    ]
    query = " ".join([p for p in query_parts if p.strip()])

    q_tokens = set(_tokenize(query))

    candidates: List[Tuple[int, EvidenceChunk]] = []

    md_files = sorted(base_dir.rglob("*.md"))
    for fp in md_files:
        text = fp.read_text(encoding="utf-8", errors="ignore")
        d_tokens = set(_tokenize(text))
        s = _score(q_tokens, d_tokens)
        if s <= 0:
            continue

        # Chunk very simply by paragraphs to keep things deterministic.
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for i, para in enumerate(paragraphs[:10]):  # cap per doc
            para_tokens = set(_tokenize(para))
            ps = _score(q_tokens, para_tokens)
            if ps <= 0:
                continue

            source_id = f"local:{fp.stem}#{i+1}"
            snippet = (para[:240] + "…") if len(para) > 240 else para
            chunk = EvidenceChunk(
                source_id=source_id,
                title=fp.stem.replace("_", " ").title(),
                snippet=snippet,
                url_or_docref=str(fp),
                quote=para[:500],
            )
            candidates.append((ps, chunk))

    # If no candidate matched, still return a deterministic fallback from any docs.
    if not candidates:
        fallback_chunks: List[EvidenceChunk] = []
        for fp in md_files[:2]:
            text = fp.read_text(encoding="utf-8", errors="ignore")
            para = next((p.strip() for p in text.split("\n\n") if p.strip()), "")
            fallback_chunks.append(
                EvidenceChunk(
                    source_id=f"local:{fp.stem}#1",
                    title=fp.stem.replace("_", " ").title(),
                    snippet=para[:240],
                    url_or_docref=str(fp),
                    quote=para[:500],
                )
            )
        return RetrievalResponse(evidence=fallback_chunks)

    candidates.sort(key=lambda x: x[0], reverse=True)
    top = [c for _, c in candidates[:top_k]]
    return RetrievalResponse(evidence=top)
