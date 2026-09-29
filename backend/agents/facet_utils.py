from __future__ import annotations

from typing import Optional


def facet_key(name: Optional[str]) -> str:
    """Comparison key for facet names: case- and whitespace-insensitive.

    Regenerated or revised items can come back as "belonging " or "Belonging";
    every facet count and facet match must treat those as the same facet.
    """
    return " ".join((name or "").split()).casefold()
