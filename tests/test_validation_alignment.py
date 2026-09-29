"""Tests that each final item keeps its own validation result.

The bug: finalize_node matched ``validation_results`` to items by position, but
PFA pruning, the fallback trim and dedup all drop items first, so later items
were reported with another item's scores. The quality-gate top-3 fallback also
re-indexed validations in score order while keeping items in draft order.
"""

from collections import OrderedDict

import pytest
from fastapi import HTTPException

from backend import main
from backend.agents.meta_editor import _with_original_structure
from backend.graph import _attach_validations, _fallback_trim_to_target
from backend.schemas import DimensionScore, DraftItem, ItemValidation, UserRequest


def _item(text: str) -> DraftItem:
    return DraftItem(item_text=text, construct_name="Test Construct", rationale="Targets the construct.")


def _validation(idx: int, text: str, score: float) -> ItemValidation:
    return ItemValidation(
        item_index=idx,
        item_text=text,
        dimension_scores=[
            DimensionScore(dimension=d, reasoning="", score=int(score))
            for d in ("correspondence", "distinctiveness", "clarity", "specificity")
        ],
        weighted_score=score,
        accept=score >= 7.0,
        attempt=1,
    )


def test_attach_validations_pins_by_item_index():
    items = [_item(f"item {i}") for i in range(3)]
    validations = [_validation(2, "item 2", 9.0), _validation(0, "item 0", 6.0)]

    attached = _attach_validations(items, validations)

    assert attached[0].validation_result.item_text == "item 0"
    assert attached[1].validation_result is None
    assert attached[2].validation_result.item_text == "item 2"


def test_fallback_trim_uses_pinned_scores_after_pruning():
    # Four validated items; PFA already dropped item 0, so positions shifted.
    texts = ["item a", "item b", "item c", "item d"]
    validations = [
        _validation(0, texts[0], 9.0),
        _validation(1, texts[1], 5.0),
        _validation(2, texts[2], 8.0),
        _validation(3, texts[3], 7.0),
    ]
    pinned = _attach_validations([_item(t) for t in texts], validations)
    after_pfa = pinned[1:]  # b, c, d

    kept, _ = _fallback_trim_to_target(
        after_pfa, target=2, validation_results=validations, is_unidimensional=True
    )

    # "b" (5.0) is the weakest item. Position-based lookup reads positions
    # 0/1/2 as validation 0/1/2 (9.0/5.0/8.0) and drops "c" instead.
    assert [it.item_text for it in kept] == ["item c", "item d"]


def test_meta_editor_carries_validation_through_revision():
    original = _attach_validations([_item("old wording")], [_validation(0, "old wording", 8.0)])
    revised = [_item("new wording")]

    out = _with_original_structure(original, revised)

    assert out[0].item_text == "new wording"
    assert out[0].validation_result.item_text == "old wording"


def _request(provider: str) -> UserRequest:
    return UserRequest(
        construct_name="Belonging",
        construct_definition="Feeling accepted and valued at work.",
        target_population="employees",
        response_scale="5-point Likert",
        model_provider=provider,
    )


def test_mock_mode_skips_provider_credential_check(monkeypatch):
    monkeypatch.setattr(main.settings, "APP_MODE", "mock")
    monkeypatch.setattr(main.settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(main.settings, "CLAUDE_API_KEY", None)

    main._require_provider_credentials(_request("openai"))
    main._require_provider_credentials(_request("claude"))


def test_live_mode_requires_provider_key(monkeypatch):
    monkeypatch.setattr(main.settings, "APP_MODE", "claude")
    monkeypatch.setattr(main.settings, "CLAUDE_API_KEY", None)

    with pytest.raises(HTTPException) as exc:
        main._require_provider_credentials(_request("claude"))
    assert exc.value.status_code == 400


def test_run_status_registry_is_bounded(monkeypatch):
    monkeypatch.setattr(main, "RUN_STATUS_REGISTRY", OrderedDict())
    monkeypatch.setattr(main, "_RUN_STATUS_MAX_ENTRIES", 3)

    for i in range(5):
        main._set_run_status(f"thread-{i}", f"run-{i}", status="complete")

    assert list(main.RUN_STATUS_REGISTRY) == ["thread-2", "thread-3", "thread-4"]


def test_run_status_registry_evicts_least_recently_updated(monkeypatch):
    monkeypatch.setattr(main, "RUN_STATUS_REGISTRY", OrderedDict())
    monkeypatch.setattr(main, "_RUN_STATUS_MAX_ENTRIES", 2)

    main._set_run_status("old", "run-old", status="complete")
    main._set_run_status("other", "run-other", status="complete")
    main._set_run_status("old", "run-old", status="complete")  # touched again
    main._set_run_status("new", "run-new", status="complete")

    assert list(main.RUN_STATUS_REGISTRY) == ["old", "new"]


def test_run_status_registry_never_evicts_running(monkeypatch):
    monkeypatch.setattr(main, "RUN_STATUS_REGISTRY", OrderedDict())
    monkeypatch.setattr(main, "_RUN_STATUS_MAX_ENTRIES", 1)

    main._set_run_status("live", "run-live", status="running")
    main._set_run_status("done", "run-done", status="complete")
    main._set_run_status("newer", "run-newer", status="complete")

    assert "live" in main.RUN_STATUS_REGISTRY


def test_run_status_registry_evicts_stale_running_entries(monkeypatch):
    monkeypatch.setattr(main, "RUN_STATUS_REGISTRY", OrderedDict())
    monkeypatch.setattr(main, "_RUN_STATUS_MAX_ENTRIES", 1)

    main._set_run_status("abandoned", "run-a", status="running")
    main.RUN_STATUS_REGISTRY["abandoned"]["updated_at"] = "2020-01-01T00:00:00+00:00"
    main._set_run_status("current", "run-c", status="complete")

    assert list(main.RUN_STATUS_REGISTRY) == ["current"]
