"""Regression tests for dedup-before-pruning, checkpoint cleanup and stream capacity."""

import asyncio
import time

from fastapi.testclient import TestClient

from backend import graph, main
from backend.schemas import DraftItem, UserRequest


def _item(text: str) -> DraftItem:
    return DraftItem(item_text=text, construct_name="Trait", rationale="Targets the trait.")


def _request(item_count: int, min_items_per_facet: int = 1) -> UserRequest:
    return UserRequest(
        construct_name="Trait",
        construct_definition="A single test trait for the pipeline.",
        target_population="adults",
        response_scale="5-point Likert",
        item_count=item_count,
        min_items_per_facet=min_items_per_facet,
    )


def _state(items, item_count):
    return {
        "user_request": _request(item_count),
        "draft_items": items,
        "validation_results": [],
        "audit_warnings": [],
        "_start_time": time.time(),
    }


def test_pruning_dedups_pool_first_and_reports_original_indices(monkeypatch):
    items = [_item(f"distinct item {i}") for i in range(6)]
    # Items 1 and 3 are near-duplicates of earlier items.
    monkeypatch.setattr(
        "backend.agents.deduplicator.deduplicate_items",
        lambda its, threshold: ([it for i, it in enumerate(its) if i not in (1, 3)], [1, 3]),
    )
    seen = {}

    def fake_prune(pool, facet_mapping, target_count, deadline, min_per_facet):
        seen["pool"] = [it.item_text for it in pool]
        # Drop pool position 0 (original item 0) to reach the target of 3.
        return pool[1:], [0], None

    monkeypatch.setattr("backend.agents.pfa_pruning.prune_items", fake_prune)

    out = graph.pfa_pruning_node(_state(items, item_count=3))

    assert seen["pool"] == ["distinct item 0", "distinct item 2", "distinct item 4", "distinct item 5"]
    assert [it.item_text for it in out["draft_items"]] == [
        "distinct item 2", "distinct item 4", "distinct item 5",
    ]
    assert out["pfa_dropped_indices"] == [0, 1, 3]


def test_pruning_warns_when_dedup_leaves_fewer_than_requested(monkeypatch):
    items = [_item(f"distinct item {i}") for i in range(4)]
    monkeypatch.setattr(
        "backend.agents.deduplicator.deduplicate_items",
        lambda its, threshold: (its[:2], [2, 3]),
    )
    monkeypatch.setattr("backend.agents.pfa_estimator.run_pfa", lambda its, facet_mapping: None)

    out = graph.pfa_pruning_node(_state(items, item_count=3))

    assert len(out["draft_items"]) == 2
    assert any("2 distinct items remain of the 3 requested" in w for w in out["audit_warnings"])


def test_discard_checkpoints_deletes_thread(monkeypatch):
    deleted = []

    class _Saver:
        async def adelete_thread(self, thread_id):
            deleted.append(thread_id)

    monkeypatch.setattr(main.app.state, "checkpointer", _Saver(), raising=False)

    asyncio.run(main._discard_checkpoints("thread-x"))

    assert deleted == ["thread-x"]


def test_stream_reports_capacity_instead_of_queueing(monkeypatch):
    monkeypatch.setattr(main.settings, "APP_MODE", "mock")
    monkeypatch.setattr(main, "_reject_if_at_capacity", lambda: None)
    monkeypatch.setattr(main, "_GENERATION_SLOTS", asyncio.Semaphore(0))
    body = {
        "construct_name": "Trait",
        "construct_definition": "A single test trait for the pipeline.",
        "target_population": "adults",
        "response_scale": "5-point Likert",
    }

    with TestClient(main.app) as client:
        resp = client.post("/v1/generate-items-stream", json=body)

    assert resp.status_code == 200
    assert "Generation capacity reached" in resp.text


def test_embedding_cache_fetches_each_text_once(monkeypatch):
    from types import SimpleNamespace

    from backend.agents import correlation_estimator as ce

    calls = []

    class _Client:
        def __init__(self, **kwargs):
            self.embeddings = SimpleNamespace(create=self._create)

        def _create(self, model, input):
            calls.append(list(input))
            return SimpleNamespace(
                data=[SimpleNamespace(index=i, embedding=[float(len(t)), 1.0]) for i, t in enumerate(input)]
            )

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(ce.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(ce, "OpenAI", _Client)

    first = ce.embed_items_sync(["alpha", "beta"], model="m")
    second = ce.embed_items_sync(["beta", "gamma", "alpha"], model="m")

    assert calls == [["alpha", "beta"], ["gamma"]]
    assert second.tolist() == [[4.0, 1.0], [5.0, 1.0], [5.0, 1.0]]
    assert first.tolist() == [[5.0, 1.0], [4.0, 1.0]]


def test_clean_validations_drops_out_of_range_and_duplicate_indices():
    from backend.graph import _clean_validations
    from backend.schemas import DimensionScore, ItemValidation

    def v(idx):
        return ItemValidation(
            item_index=idx,
            item_text=f"Item text {idx}",
            dimension_scores=[DimensionScore(dimension="clarity", reasoning="", score=8)],
            weighted_score=8.0,
            accept=True,
            attempt=1,
        )

    cleaned = _clean_validations([v(0), v(2), v(2), v(5), v(1)], n_items=3)

    assert [c.item_index for c in cleaned] == [0, 2, 1]


def test_meta_editor_input_applies_construct_level_bias_downgrade(monkeypatch):
    from backend.schemas import ReviewComment

    captured = {}

    def fake_revise(**kwargs):
        captured["bias"] = kwargs["bias_comments"]
        raise RuntimeError("stop after capturing input")

    monkeypatch.setattr(graph, "revise_items", fake_revise)
    same_issue = "Construct wording assumes a Western individualist workplace culture."
    bias = [
        ReviewComment(type="bias", item_index=i, issue=same_issue, severity=3)
        for i in range(3)
    ]
    state = {**_state([_item(f"distinct item {i}") for i in range(3)], 3), "bias_comments": bias}

    graph.meta_editor_node(state)

    assert captured["bias"] == []
    assert [c.severity for c in state["bias_comments"]] == [3, 3, 3]


def test_unmatched_facet_item_is_judged_on_its_strongest_loading():
    import numpy as np

    from backend.agents.pfa_estimator import compute_retention_flags

    loadings = np.array([[0.7, 0.1], [0.1, 0.7], [0.05, 0.08], [0.6, 0.1]])
    flags = compute_retention_flags(loadings, [0, 1, -1, -1])

    assert flags[2] == (False, ["rule1_below_parent_minimum"])
    assert flags[3] == (True, [])



def test_quality_gate_keeps_items_without_a_validation(monkeypatch):
    from backend.schemas import DimensionScore, ItemValidation, ValidationResponse

    items = [_item(f"distinct item {i}") for i in range(5)]

    def v(idx, score):
        return ItemValidation(
            item_index=idx,
            item_text=items[idx].item_text,
            dimension_scores=[DimensionScore(dimension="clarity", reasoning="", score=int(score))],
            weighted_score=score,
            accept=score >= 7.0,
            attempt=3,
        )

    # Item 3 has no validation (the LLM skipped it); item 1 is below 5.0.
    resp = ValidationResponse(validations=[v(0, 8.0), v(1, 4.0), v(2, 8.0), v(4, 6.0)])
    monkeypatch.setattr(
        "backend.agents.validator.validate_items",
        lambda request, items, attempt: (resp, graph.TokenUsage()),
    )
    state = {**_state(items, 5), "validation_attempt": 3}

    out = graph.validation_node(state).update

    kept = [it.item_text for it in out["draft_items"]]
    assert kept == ["distinct item 0", "distinct item 2", "distinct item 3", "distinct item 4"]
    assert [it.validation_result is None for it in out["draft_items"]] == [False, False, True, False]
    assert out["draft_items"][3].validation_result.weighted_score == 6.0
    assert out["force_accepted_below_threshold"] is True
    assert any("1 item(s) were not scored" in w for w in out["audit_warnings"])


def _validation(idx, text):
    from backend.schemas import DimensionScore, ItemValidation

    return ItemValidation(
        item_index=idx,
        item_text=text,
        dimension_scores=[DimensionScore(dimension="clarity", reasoning="", score=8)],
        weighted_score=8.0,
        accept=True,
        attempt=1,
    )


def test_realign_moves_only_mismatched_validations_to_unclaimed_items():
    from backend.agents.validator import _realign_by_text

    items = [_item("first item"), _item("second item"), _item("first item")]
    validations = [
        _validation(0, "first item"),   # correct
        _validation(2, "first item"),   # correct: duplicate text, own index agrees
        _validation(0, "second item"),  # shifted: belongs to item 1
    ]

    _realign_by_text(validations, items)

    assert [v.item_index for v in validations] == [0, 2, 1]


def test_realign_leaves_index_when_text_matches_no_free_item():
    from backend.agents.validator import _realign_by_text

    items = [_item("first item"), _item("second item")]
    validations = [_validation(0, "first item"), _validation(1, "first item")]

    _realign_by_text(validations, items)

    assert [v.item_index for v in validations] == [0, 1]


def test_budgeted_call_does_not_make_a_second_llm_call(monkeypatch):
    import pytest as _pytest

    from backend.agents import llm_utils
    from backend.schemas import MetaEditorResponse

    calls = []

    class _Runnable:
        def invoke(self, messages):
            calls.append("structured")
            return {"parsed": None, "raw": None, "parsing_error": ValueError("bad json")}

    class _Llm:
        def with_structured_output(self, *args, **kwargs):
            return _Runnable()

        def invoke(self, messages):
            calls.append("fallback")
            raise AssertionError("second call made")

    monkeypatch.setattr(llm_utils.settings, "APP_MODE", "claude")
    monkeypatch.setattr(
        "backend.agents.llm_factory.get_chat_model_for_agent", lambda *a, **k: _Llm()
    )

    with _pytest.raises(ValueError):
        llm_utils.invoke_structured_with_usage(
            MetaEditorResponse, [("human", "x")], agent_name="meta_editor",
            model_provider="claude", client_timeout=30, client_max_retries=0,
        )
    assert calls == ["structured"]
