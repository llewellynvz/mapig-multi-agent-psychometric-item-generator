"""Unit tests for persona validator (Phase 16)."""

from __future__ import annotations

import statistics

import pytest

from backend.agents.persona_validator import (
    _build_persona_prompts,
    validate_with_personas,
)
from backend.schemas import DraftItem, PersonaRating, PersonaValidationResponse, UserRequest


def _make_request() -> UserRequest:
    return UserRequest(
        construct_name="Test",
        construct_definition="An operational definition for testing.",
        target_population="South African working adults",
        cultural_group="urban professionals",
        response_scale="5-point Likert",
        item_count=3,
        model_provider="openai",
    )


def _make_items(n: int) -> list[DraftItem]:
    return [
        DraftItem(
            item_text=f"Item text number {i}.",
            construct_name="Test",
            rationale="synthetic rationale",
            facet_name="A",
        )
        for i in range(n)
    ]


def test_build_persona_prompts_returns_n_distinct():
    prompts = _build_persona_prompts(3, "nurses", "Cape Town")
    assert len(prompts) == 3
    assert len(set(prompts)) == 3
    assert all("nurses" in p for p in prompts)


def test_build_persona_prompts_pads_when_n_large():
    prompts = _build_persona_prompts(6, "students", "Joburg")
    assert len(prompts) == 6


def test_validate_with_personas_zero_personas_disabled():
    req = _make_request()
    items = _make_items(3)
    resp, _usage = validate_with_personas(req, items, n_personas=0)
    assert resp.flagged_items == []
    assert "disabled" in resp.summary.lower()


def test_validate_with_personas_no_items():
    req = _make_request()
    resp, _usage = validate_with_personas(req, [], n_personas=3)
    assert resp.flagged_items == []


def test_validate_with_personas_in_mock_mode(monkeypatch):
    monkeypatch.setattr("backend.settings.settings.APP_MODE", "mock")
    req = _make_request()
    items = _make_items(4)

    resp, _usage = validate_with_personas(req, items, n_personas=3)

    # In mock mode, ratings should be generated for all 3 personas × 4 items = 12
    assert len(resp.ratings) == 12
    # Personas should be distinct
    persona_labels = {r.persona_label for r in resp.ratings}
    assert len(persona_labels) == 3
    # Interpretive variance should be computed
    assert resp.interpretive_variance >= 0.0


def test_persona_validation_flagging_logic_with_synthetic_ratings():
    """Direct test of flagging logic with hand-crafted ratings.

    With 4 raters on a 1-5 Likert scale:
    - item 0: all agree (rating 3) → SD = 0 → no flag
    - item 1: split (1, 1, 5, 5) → SD = 2.0 → flag (= threshold)
    - item 2: minor disagreement (3, 4, 3, 4) → SD = 0.5 → no flag
    """
    ratings = [
        # Item 0 — perfect agreement
        PersonaRating(persona_label=f"Persona {p}", item_index=0, rating=3, interpretation="reads same way")
        for p in ["A", "B", "C", "D"]
    ] + [
        # Item 1 — split
        PersonaRating(persona_label="Persona A", item_index=1, rating=1, interpretation="reading one way"),
        PersonaRating(persona_label="Persona B", item_index=1, rating=1, interpretation="reading one way"),
        PersonaRating(persona_label="Persona C", item_index=1, rating=5, interpretation="reading other way"),
        PersonaRating(persona_label="Persona D", item_index=1, rating=5, interpretation="reading other way"),
    ] + [
        # Item 2 — minor noise
        PersonaRating(persona_label="Persona A", item_index=2, rating=3, interpretation="reads neutrally"),
        PersonaRating(persona_label="Persona B", item_index=2, rating=4, interpretation="reads positively"),
        PersonaRating(persona_label="Persona C", item_index=2, rating=3, interpretation="reads neutrally"),
        PersonaRating(persona_label="Persona D", item_index=2, rating=4, interpretation="reads positively"),
    ]

    by_item: dict[int, list[int]] = {}
    for r in ratings:
        by_item.setdefault(r.item_index, []).append(r.rating)

    threshold = 2
    flagged = [
        idx
        for idx, vals in by_item.items()
        if len(vals) >= 2 and statistics.pstdev(vals) >= threshold
    ]
    assert 1 in flagged
    assert 0 not in flagged
    assert 2 not in flagged


def test_persona_label_max_chars_setting_respected():
    """Schema cap was raised from 600 to 1500. Verify both bounds."""
    from backend.schemas import PersonaRating
    # Should accept a 1500-char label
    long_ok = "A " + "x" * 1497  # 1499 chars
    pr = PersonaRating(persona_label=long_ok, item_index=0, rating=3, interpretation="ok ok")
    assert len(pr.persona_label) == 1499
    # Should reject a 1501-char label (Pydantic max_length=1500)
    too_long = "A " + "x" * 1500  # 1502 chars
    import pytest
    with pytest.raises(Exception):
        PersonaRating(persona_label=too_long, item_index=0, rating=3, interpretation="ok ok")


def test_persona_truncation_in_validate_with_personas(monkeypatch):
    """When the LLM returns a persona_label > settings.PERSONA_LABEL_MAX_CHARS,
    validate_with_personas truncates it BEFORE constructing PersonaRating —
    no crash, ratings still produced, PERSONA_TRUNCATED log fires."""
    monkeypatch.setattr("backend.settings.settings.APP_MODE", "mock")
    monkeypatch.setattr("backend.settings.settings.PERSONA_LABEL_MAX_CHARS", 100)

    # Build a persona that's intentionally longer than 100 chars
    long_persona = "A 41-year-old senior retail store manager " + ("with extensive responsibilities " * 10)
    assert len(long_persona) > 100

    # Stub the persona-rating worker to return our long persona
    from backend.agents import persona_validator as pv
    from backend.agents.persona_validator import _PersonaItemRating, _PersonaValidatorAgentOutput
    from backend.agents.llm_utils import TokenUsage

    def _stub_rating(request, persona_label, items):
        return (
            _PersonaValidatorAgentOutput(
                persona_label=long_persona,
                ratings=[
                    _PersonaItemRating(
                        item_index=i, rating=3, interpretation=f"persona reads item {i} the same way"
                    )
                    for i in range(len(items))
                ],
            ),
            TokenUsage(),
        )

    monkeypatch.setattr(pv, "_rate_items_for_persona", _stub_rating)
    # Skip persona generation by stubbing it too
    monkeypatch.setattr(pv, "_generate_personas_via_llm", lambda req, n: ([long_persona] * n, TokenUsage()))

    req = _make_request()
    items = _make_items(3)
    resp, _usage = pv.validate_with_personas(req, items, n_personas=2)

    # No crash — ratings present, persona_labels truncated to ≤100 chars
    assert len(resp.ratings) == 6  # 2 personas × 3 items
    for r in resp.ratings:
        assert len(r.persona_label) <= 100, (
            f"Expected truncation to ≤100 chars; got {len(r.persona_label)}"
        )
        assert r.persona_label.endswith("…")  # truncation marker


def test_persona_validation_response_schema_roundtrip():
    """Schema dump/load works."""
    resp = PersonaValidationResponse(
        personas=["Persona One", "Persona Two"],
        ratings=[
            PersonaRating(persona_label="Persona One", item_index=0, rating=4, interpretation="reads it as expected")
        ],
        flagged_items=[0],
        interpretive_variance=1.0,
        summary="Test",
    )
    dumped = resp.model_dump()
    rebuilt = PersonaValidationResponse.model_validate(dumped)
    assert rebuilt.flagged_items == [0]
    assert rebuilt.interpretive_variance == 1.0
