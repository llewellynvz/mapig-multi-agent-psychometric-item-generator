"""Known published instrument items for plagiarism detection.

These items are from freely-published, public-domain instruments used in
academic research. They are included here solely for automated plagiarism
detection (semantic similarity comparison) to ensure generated items are
sufficiently original.

Sources:
- SWLS: Diener, E., Emmons, R.A., Larsen, R.J., & Griffin, S. (1985). The Satisfaction With Life Scale. Journal of Personality Assessment, 49(1), 71-75.
- PWI: International Wellbeing Group (2013). Personal Wellbeing Index, 5th Edition.
- RSES: Rosenberg, M. (1965). Society and the Adolescent Self-Image. Princeton University Press.
- PHQ-9: Kroenke, K., Spitzer, R.L., & Williams, J.B. (2001). The PHQ-9. Journal of General Internal Medicine, 16(9), 606-613. (Public domain, developed with public funding.)
"""

from __future__ import annotations

# Dict keyed by canonical instrument name (lowercase for lookup).
# Each value is a list of item text strings.

KNOWN_INSTRUMENT_ITEMS: dict[str, list[str]] = {
    # ── Satisfaction With Life Scale (Diener et al., 1985) ──
    "satisfaction with life scale": [
        "In most ways my life is close to my ideal",
        "The conditions of my life are excellent",
        "I am satisfied with my life",
        "So far I have gotten the important things I want in life",
        "If I could live my life over I would change almost nothing",
    ],
    "swls": [  # alias
        "In most ways my life is close to my ideal",
        "The conditions of my life are excellent",
        "I am satisfied with my life",
        "So far I have gotten the important things I want in life",
        "If I could live my life over I would change almost nothing",
    ],
    # ── Personal Wellbeing Index (International Wellbeing Group, 2013) ──
    "personal wellbeing index": [
        "How satisfied are you with your standard of living",
        "How satisfied are you with your health",
        "How satisfied are you with what you are achieving in life",
        "How satisfied are you with your personal relationships",
        "How satisfied are you with how safe you feel",
        "How satisfied are you with feeling part of your community",
        "How satisfied are you with your future security",
        "How satisfied are you with your spirituality or religion",
    ],
    "pwi": [  # alias
        "How satisfied are you with your standard of living",
        "How satisfied are you with your health",
        "How satisfied are you with what you are achieving in life",
        "How satisfied are you with your personal relationships",
        "How satisfied are you with how safe you feel",
        "How satisfied are you with feeling part of your community",
        "How satisfied are you with your future security",
        "How satisfied are you with your spirituality or religion",
    ],
    # ── Rosenberg Self-Esteem Scale (Rosenberg, 1965) ──
    "rosenberg self-esteem scale": [
        "On the whole I am satisfied with myself",
        "At times I think I am no good at all",
        "I feel that I have a number of good qualities",
        "I am able to do things as well as most other people",
        "I feel I do not have much to be proud of",
        "I certainly feel useless at times",
        "I feel that I am a person of worth at least on an equal plane with others",
        "I wish I could have more respect for myself",
        "All in all I am inclined to feel that I am a failure",
        "I take a positive attitude toward myself",
    ],
    "rses": [  # alias
        "On the whole I am satisfied with myself",
        "I feel that I have a number of good qualities",
        "I am able to do things as well as most other people",
        "I take a positive attitude toward myself",
    ],
    # ── PHQ-9 (Kroenke et al., 2001) — public domain ──
    "phq-9": [
        "Little interest or pleasure in doing things",
        "Feeling down depressed or hopeless",
        "Trouble falling or staying asleep or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself or that you are a failure",
        "Trouble concentrating on things such as reading",
        "Moving or speaking so slowly that other people could have noticed",
        "Thoughts that you would be better off dead or of hurting yourself",
    ],
    "patient health questionnaire": [
        "Little interest or pleasure in doing things",
        "Feeling down depressed or hopeless",
        "Feeling tired or having little energy",
    ],
}


def lookup_instrument_items(instrument_name: str) -> list[str]:
    """Look up known items for an instrument by name.

    Args:
        instrument_name: Instrument name (case-insensitive, partial match).

    Returns:
        List of item text strings, or empty list if not found.
    """
    name_lower = instrument_name.lower().strip()

    # Exact match first
    if name_lower in KNOWN_INSTRUMENT_ITEMS:
        return KNOWN_INSTRUMENT_ITEMS[name_lower]

    # Partial match (instrument name contains key or key contains instrument name)
    for key, items in KNOWN_INSTRUMENT_ITEMS.items():
        if key in name_lower or name_lower in key:
            return items

    return []
