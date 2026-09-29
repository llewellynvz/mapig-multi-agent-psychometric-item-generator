"""Tests for the post-dedup per-facet minimum item floor.

The fix: ``_enforce_facet_floor`` restores dropped near-duplicate items so no
facet falls below ``min_items_per_facet`` (default 3 — the just-identification
floor for a single factor). This closes the gap where ``deduplicate_items``
removed near-duplicates without facet bookkeeping and collapsed a facet into a
Heywood case (e.g. UWES Vigor/Absorption dropping to 1 item).
"""

from backend.graph import _enforce_facet_floor
from backend.schemas import DraftItem


def _item(text: str, facet: str) -> DraftItem:
    return DraftItem(
        item_text=f"{text} item",
        construct_name="Test Construct",
        rationale="Targets the assigned facet.",
        facet_name=facet,
    )


def _facet_counts(items) -> dict:
    counts = {}
    for it in items:
        counts[it.facet_name] = counts.get(it.facet_name, 0) + 1
    return counts


def test_restores_facet_dropped_below_floor():
    # Three facets (A, B, C) x 3 items. Dedup drops B2 and B3, leaving B with 1.
    original = [_item(f"{f}{n}", f) for f in ("A", "B", "C") for n in range(3)]
    dropped = [4, 5]  # B2 (index 4), B3 (index 5)
    kept = [it for i, it in enumerate(original) if i not in dropped]

    final, still_dropped, warnings = _enforce_facet_floor(
        kept, original, dropped, min_per_facet=3
    )

    counts = _facet_counts(final)
    assert counts["B"] == 3
    assert len(final) == 9
    assert still_dropped == []
    assert warnings == []


def test_noop_when_facets_already_at_floor():
    # Every facet keeps >= 3 items after dedup → nothing restored.
    original = [_item(f"{f}{n}", f) for f in ("A", "B", "C") for n in range(4)]
    dropped = [3, 7, 11]  # one item dropped from each facet (A3, B3, C3)
    kept = [it for i, it in enumerate(original) if i not in dropped]

    final, still_dropped, warnings = _enforce_facet_floor(
        kept, original, dropped, min_per_facet=3
    )

    assert _facet_counts(final) == {"A": 3, "B": 3, "C": 3}
    assert still_dropped == dropped  # nothing restored
    assert warnings == []


def test_noop_when_floor_is_one():
    # min_per_facet <= 1 disables the guard (legacy behaviour).
    original = [_item(f"{f}{n}", f) for f in ("A", "B") for n in range(2)]
    dropped = [1]
    kept = [it for i, it in enumerate(original) if i not in dropped]

    final, still_dropped, warnings = _enforce_facet_floor(
        kept, original, dropped, min_per_facet=1
    )

    assert final == kept
    assert still_dropped == dropped
    assert warnings == []


def test_warns_when_facet_cannot_reach_floor():
    # Facet B had only 2 items pre-dedup; dedup drops one, and the floor is 3.
    # The guard can restore only 1 → B remains at 2 and a warning fires.
    original = [
        _item("A0", "A"), _item("A1", "A"), _item("A2", "A"),
        _item("B0", "B"), _item("B1", "B"),
        _item("C0", "C"), _item("C1", "C"), _item("C2", "C"),
    ]
    dropped = [4]  # B1
    kept = [it for i, it in enumerate(original) if i not in dropped]

    final, still_dropped, warnings = _enforce_facet_floor(
        kept, original, dropped, min_per_facet=3
    )

    assert _facet_counts(final)["B"] == 2  # restored B1, but only 2 exist in total
    assert len(warnings) == 1
    assert "B" in warnings[0]
