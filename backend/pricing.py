"""Static blended token rates used for the cost estimates in the audit trail.

Rates are USD per million tokens, blended across input and output at an
assumed ~1:1 ratio. They are estimates for run-level cost visibility, not
billing-grade accounting.
"""

from __future__ import annotations

BLENDED_RATES_PER_MTOK: dict[str, float] = {
    "claude_opus": 45.0,
    "claude_sonnet": 9.0,
    "gpt_4o": 6.25,
    "gpt_4o_mini": 0.375,
    "gpt_52": 14.0,
}

CACHE_INPUT_RATE_PER_MTOK = 3.0
CACHE_DISCOUNT = 0.9


def blended_cost(tokens: int, rate_key: str) -> float:
    """Estimated USD cost for a token count at a blended model rate."""
    return (tokens / 1_000_000) * BLENDED_RATES_PER_MTOK[rate_key]


def cache_savings(cache_read_tokens: int) -> float:
    """Estimated USD saved by prompt-cache reads (cached tokens are billed
    at 10% of the input rate; Sonnet input rate used as the blend)."""
    if cache_read_tokens <= 0:
        return 0.0
    return (cache_read_tokens / 1_000_000) * CACHE_INPUT_RATE_PER_MTOK * CACHE_DISCOUNT
