"""Input sanitizer for prompt injection defense.

Strips known injection patterns from user-supplied strings before they are
interpolated into LLM prompts.  This is a defense-in-depth measure — it does
NOT replace structured output parsing or output validation.
"""

from __future__ import annotations

import logging
import re
from typing import Dict

logger = logging.getLogger("lmaig.sanitizer")

# Compiled once at import time for performance
_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\b", re.IGNORECASE),
    re.compile(r"^system\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^assistant\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"<\|?\s*(?:system|im_start|im_end)\s*\|?>", re.IGNORECASE),
    re.compile(r"(?:output|reveal|print|show)\s+(?:your\s+)?(?:system\s+)?prompt", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous|prior|above)", re.IGNORECASE),
    re.compile(r"forget\s+(?:all\s+)?(?:previous|prior|your)\s+(?:instructions|rules)", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
]

# Per-field length limits (in characters)
_FIELD_LIMITS: Dict[str, int] = {
    "construct_name": 200,
    "construct_definition": 2000,
    "example_item": 500,
    "native_construct": 200,
    "target_population": 500,
    "cultural_group": 200,
    "response_scale": 200,
    "construct_exclusions": 1000,
    "human_feedback": 3000,
}


def sanitize_string(value: str, field_name: str, max_length: int | None = None) -> str:
    """Sanitize a single string value.

    1. Strips known injection patterns (replaced with empty string).
    2. Truncates to *max_length* if specified.

    Returns the cleaned string.
    """
    if not value:
        return value

    cleaned = value
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            logger.warning(
                "SANITIZER field=%s pattern=%r matched=%r",
                field_name, pattern.pattern, match.group()[:60],
            )
            cleaned = pattern.sub("", cleaned)

    # Collapse multiple whitespace left by removals
    cleaned = re.sub(r"[ \t]{3,}", " ", cleaned).strip()

    limit = max_length or _FIELD_LIMITS.get(field_name)
    if limit and len(cleaned) > limit:
        logger.warning(
            "SANITIZER field=%s truncated from %d to %d chars",
            field_name, len(cleaned), limit,
        )
        cleaned = cleaned[:limit]

    return cleaned


def sanitize_user_request(request) -> None:
    """Sanitize mutable string fields on a UserRequest in place.

    Modifies the request object directly so downstream code uses clean values.
    """
    for field_name in (
        "construct_name",
        "construct_definition",
        "example_item",
        "native_construct",
        "target_population",
        "cultural_group",
        "response_scale",
        "construct_exclusions",
        "human_feedback",
    ):
        raw = getattr(request, field_name, None)
        if raw is not None:
            cleaned = sanitize_string(raw, field_name)
            if cleaned != raw:
                object.__setattr__(request, field_name, cleaned)

    # Sanitize list-of-string fields
    if request.constraints:
        cleaned_constraints = [
            sanitize_string(c, "constraints", max_length=500)
            for c in request.constraints
        ]
        if cleaned_constraints != request.constraints:
            object.__setattr__(request, "constraints", cleaned_constraints)

    if request.previous_items:
        cleaned_previous = [
            sanitize_string(p, "previous_items", max_length=500)
            for p in request.previous_items
        ]
        if cleaned_previous != request.previous_items:
            object.__setattr__(request, "previous_items", cleaned_previous)


def check_construct_definition_coherence(
    request,
    threshold: float = 0.40,
) -> str | None:
    """Compute embedding similarity between construct_name and construct_definition.

    Returns a human-readable warning string when cosine similarity falls below
    `threshold` — meaning the definition probably describes a different
    construct from what the name suggests (e.g., name='Cognitive Flexibility'
    with definition='drive to seek new knowledge'). Returns None when coherent
    or when the check cannot be run (no OpenAI key, etc.).

    The warning surfaces in AuditMetadata.warnings and the UI so the user can
    correct mismatches that drive low correspondence scores.
    """
    from backend.settings import settings

    name = (getattr(request, "construct_name", None) or "").strip()
    definition = (getattr(request, "construct_definition", None) or "").strip()

    if not name or not definition or len(definition.split()) < 3:
        return None

    if settings.APP_MODE == "mock" or not settings.OPENAI_API_KEY:
        # Can't embed without OpenAI; skip silently.
        return None

    try:
        import numpy as np
        from backend.agents.correlation_estimator import embed_items_sync

        emb = embed_items_sync([name, definition], model="text-embedding-3-small")
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normed = emb / norms
        cosine = float(np.clip(normed[0] @ normed[1], -1.0, 1.0))

        if cosine < threshold:
            logger.warning(
                "CONSTRUCT_NAME_DEFINITION_MISMATCH name=%r cos=%.3f threshold=%.2f",
                name, cosine, threshold,
            )
            return (
                f"Construct name '{name}' and the supplied definition appear to describe "
                f"different constructs (semantic similarity {cosine:.2f} < {threshold:.2f}). "
                f"Items will be written for the DEFINITION; if that is not what you meant, "
                f"edit the construct definition before running again."
            )
        else:
            logger.info(
                "CONSTRUCT_COHERENCE_OK name=%r cos=%.3f", name, cosine,
            )
            return None
    except Exception as e:
        logger.debug("Construct coherence check skipped: %s", e)
        return None
