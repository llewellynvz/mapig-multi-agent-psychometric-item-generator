"""Regression tests for agent follow-up fixes: structured-output raw recovery,
per-agent client timeouts, response-scale parsing, evidence retry dedup,
embeddings-unavailable signalling, and distinct mock meta-editor stems.
No network, no LLM.
"""

import asyncio
from typing import List

import httpx
import openai
import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from backend.agents import correlation_estimator as ce
from backend.agents import llm_factory, llm_utils, synthetic_respondents as sr
from backend.agents.meta_editor import _mock_revision
from backend.agents.web_surfer import _evidence_key
from backend.schemas import DraftItem, EvidenceChunk, UserRequest
from backend.settings import settings


# ---- llm_utils.invoke_structured_with_usage raw recovery ----


class _Out(BaseModel):
    label: str
    score: int


class _FakeRunnable:
    def __init__(self, result=None, exc=None):
        self.result, self.exc = result, exc

    def invoke(self, messages):
        if self.exc is not None:
            raise self.exc
        return self.result


class _FakeLLM:
    model_name = "gpt-test"

    def __init__(self, runnable, fallback_content='{"label": "second", "score": 2}'):
        self.runnable = runnable
        self.fallback_content = fallback_content
        self.invoke_calls = 0

    def with_structured_output(self, schema, **kwargs):
        return self.runnable

    def invoke(self, messages):
        self.invoke_calls += 1
        return AIMessage(content=self.fallback_content)


@pytest.fixture
def fake_llm(monkeypatch):
    monkeypatch.setattr(settings, "APP_MODE", "openai")

    def _install(llm):
        monkeypatch.setattr(llm_factory, "get_chat_model", lambda: llm)
        return llm

    return _install


def _call(pre_validate=None):
    return llm_utils.invoke_structured_with_usage(
        _Out, [("human", "hi")], pre_validate=pre_validate
    )


def test_parsed_none_recovers_from_tool_call_args_without_second_call(fake_llm):
    raw = AIMessage(
        content="",
        tool_calls=[{"name": "_Out", "args": {"label": "raw", "score": 1}, "id": "t1"}],
    )
    llm = fake_llm(_FakeLLM(_FakeRunnable({"parsed": None, "raw": raw, "parsing_error": None})))
    out, _ = _call()
    assert out == _Out(label="raw", score=1)
    assert llm.invoke_calls == 0


def test_parsed_none_recovers_from_fenced_raw_text_with_pre_validate(fake_llm):
    raw = AIMessage(content='```json\n{"label": "a-very-long-label", "score": 3}\n```')
    llm = fake_llm(_FakeLLM(_FakeRunnable({"parsed": None, "raw": raw})))

    def _clip(data):
        data["label"] = data["label"][:6]
        return data

    out, _ = _call(pre_validate=_clip)
    assert out == _Out(label="a-very", score=3)
    assert llm.invoke_calls == 0


def test_parsed_none_recovers_from_anthropic_content_blocks(fake_llm):
    raw = AIMessage(
        content=[{"type": "tool_use", "id": "t1", "name": "_Out", "input": {"label": "blk", "score": 4}}]
    )
    llm = fake_llm(_FakeLLM(_FakeRunnable({"parsed": None, "raw": raw})))
    out, _ = _call()
    assert out == _Out(label="blk", score=4)
    assert llm.invoke_calls == 0


def test_unusable_raw_makes_one_second_call(fake_llm):
    raw = AIMessage(content="sorry, I cannot help with that")
    llm = fake_llm(_FakeLLM(_FakeRunnable({"parsed": None, "raw": raw})))
    out, _ = _call()
    assert out == _Out(label="second", score=2)
    assert llm.invoke_calls == 1


def test_timeout_is_reraised_without_second_call(fake_llm):
    exc = openai.APITimeoutError(request=httpx.Request("POST", "https://example.invalid"))
    llm = fake_llm(_FakeLLM(_FakeRunnable(exc=exc)))
    with pytest.raises(openai.APITimeoutError):
        _call()
    assert llm.invoke_calls == 0


def test_non_timeout_error_still_falls_back(fake_llm):
    llm = fake_llm(_FakeLLM(_FakeRunnable(exc=ValueError("bad schema"))))
    out, _ = _call()
    assert out == _Out(label="second", score=2)
    assert llm.invoke_calls == 1


def test_no_include_raw_result_is_returned_as_is(fake_llm):
    llm = fake_llm(_FakeLLM(_FakeRunnable(_Out(label="direct", score=5))))
    out, usage = _call()
    assert out == _Out(label="direct", score=5)
    assert usage.input_tokens == 0
    assert llm.invoke_calls == 0


# ---- llm_factory per-agent timeout ----


@pytest.fixture
def clean_factory(monkeypatch):
    monkeypatch.setattr(settings, "AZURE_TEST_OVERRIDE", False)
    monkeypatch.setattr(settings, "CLAUDE_API_KEY", "sk-ant-test")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "CLAUDE_BASE_URL", None)
    monkeypatch.setattr(settings, "META_EDITOR_TIMEOUT_SECONDS", 120)
    llm_factory.get_claude_chat_model.cache_clear()
    llm_factory.get_openai_chat_model.cache_clear()
    yield
    llm_factory.get_claude_chat_model.cache_clear()
    llm_factory.get_openai_chat_model.cache_clear()


def _timeout(model):
    return getattr(model, "default_request_timeout", None) or getattr(model, "request_timeout", None)


@pytest.mark.parametrize("provider", ["claude", "openai"])
def test_meta_editor_gets_long_timeout_on_every_path(clean_factory, provider):
    meta = llm_factory.get_chat_model_for_agent("meta_editor", provider)
    other = llm_factory.get_chat_model_for_agent("content_reviewer", provider)
    assert _timeout(meta) == 120
    assert _timeout(other) == llm_factory.DEFAULT_CLIENT_TIMEOUT_SECONDS == 45


def test_agent_client_honours_explicit_timeout_and_retries(clean_factory):
    model = llm_factory.get_chat_model_for_agent("meta_editor", "claude", timeout=70, max_retries=0)
    assert _timeout(model) == 70
    assert model.max_retries == 0


@pytest.mark.parametrize(
    "budget, expected",
    [(None, (None, None)), (20, (15, 0)), (100, (90, 0)), (250, (120, 1)), (1700, (120, 3))],
)
def test_meta_editor_call_fits_its_time_budget(budget, expected):
    from backend.agents.meta_editor import _client_budget

    timeout, retries = _client_budget(budget)
    assert (timeout, retries) == expected
    if budget is not None:
        assert (retries + 1) * timeout <= budget


def test_meta_editor_timeout_via_claude_proxy(clean_factory, monkeypatch):
    monkeypatch.setattr(settings, "CLAUDE_BASE_URL", "https://openrouter.invalid/api/v1")
    assert _timeout(llm_factory.get_chat_model_for_agent("meta_editor", "claude")) == 120
    assert _timeout(llm_factory.get_chat_model_for_agent("item_writer", "claude")) == 45


# ---- synthetic_respondents scale parsing ----


@pytest.mark.parametrize(
    "scale, expected",
    [
        ("5-point Likert", (5, 1)),
        ("7 point agreement", (7, 1)),
        ("1-7 agreement", (7, 1)),
        ("1 to 7", (7, 1)),
        ("0-10", (11, 0)),
        ("0 – 10 slider", (11, 0)),
        ("Strongly disagree (1) ... Strongly agree (7)", (7, 1)),
        ("Never (0) - Always (4)", (5, 0)),
        ("-3 to +3", (7, -3)),
        ("Likert", (5, 1)),
        ("0-100 visual analogue", (5, 1)),  # not representable on 1..11
    ],
)
def test_parse_scale(scale, expected):
    assert sr._parse_scale(scale) == expected
    assert sr._parse_scale_points(scale) == expected[0]


def _request(scale: str) -> UserRequest:
    return UserRequest(
        construct_name="Belonging",
        construct_definition="The feeling of being accepted and valued at work.",
        target_population="Working adults",
        response_scale=scale,
    )


def _items(n: int) -> List[DraftItem]:
    return [
        DraftItem(item_text=f"Item number {i} text", construct_name="Belonging", rationale="reasonable")
        for i in range(n)
    ]


def test_zero_based_scale_prompt_maps_anchors_onto_1_to_k(monkeypatch):
    captured = {}

    def _fake_invoke(schema, messages, **kwargs):
        captured["human"] = messages[1][1]
        return schema(ratings=[]), llm_utils.TokenUsage()

    monkeypatch.setattr(sr, "invoke_structured_with_usage", _fake_invoke)
    import numpy as np

    sr._rate_items_for_respondent(_request("0-10"), _items(2), ["Belonging"], np.zeros(1), 11)
    human = captured["human"]
    assert "11-point scale" in human
    assert "integer from 1 (lowest scale option) to 11" in human
    assert "record 0 as 1" in human and "10 as 11" in human


def test_one_to_seven_ratings_above_five_are_kept(monkeypatch):
    import numpy as np

    monkeypatch.setattr(settings, "APP_MODE", "openai")
    items = _items(3)

    def _fake_rate(request, items_, facet_names, theta_row, scale_points):
        ratings = [sr._RespondentRating(item_index=i, rating=7 - i) for i in range(len(items_))]
        return sr._RespondentOutput(ratings=ratings), llm_utils.TokenUsage()

    monkeypatch.setattr(sr, "_rate_items_for_respondent", _fake_rate)
    scale_points = sr._parse_scale_points("1 to 7")
    matrix, failed, _ = sr._collect_matrix(
        _request("1 to 7"), items, ["Belonging"], np.zeros((6, 1)), scale_points, seed=1
    )
    assert failed == 0
    assert matrix.shape == (6, 3)
    assert matrix[0].tolist() == [7.0, 6.0, 5.0]


# ---- web_surfer retry dedup key ----


def _chunk(source_id="", url="", quote="q"):
    return EvidenceChunk(source_id=source_id, title="t", snippet=quote[:240], url_or_docref=url, quote=quote)


def test_evidence_key_keeps_distinct_chunks_without_source_id():
    a = _chunk(url="https://a.org/1", quote="Belonging is a fundamental human need.")
    b = _chunk(url="https://b.org/2", quote="Belonging predicts engagement at work.")
    c = _chunk(url="https://a.org/1", quote="A second, different quote from the same page.")
    assert len({_evidence_key(x) for x in (a, b, c)}) == 3


def test_evidence_key_collapses_whitespace_and_case_duplicates():
    a = _chunk(source_id="S1", quote="Belonging  is a fundamental\nhuman need.")
    b = _chunk(source_id="s1", url="https://x.org", quote="belonging is a fundamental human need.")
    assert _evidence_key(a) == _evidence_key(b)


# ---- correlation_estimator: no credentials ----


def test_embeddings_unavailable_raised_before_client_construction(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "AZURE_TEST_OVERRIDE", False)

    def _no_client(*a, **k):
        raise AssertionError("client must not be constructed")

    monkeypatch.setattr(ce, "OpenAI", _no_client)
    monkeypatch.setattr(ce, "AsyncOpenAI", _no_client)
    with pytest.raises(ce.EmbeddingsUnavailable):
        ce.embed_items_sync(["a", "b"])
    with pytest.raises(ce.EmbeddingsUnavailable):
        asyncio.run(ce.embed_items(["a", "b"]))
    assert issubclass(ce.EmbeddingsUnavailable, RuntimeError)


# ---- meta_editor mock revision ----


def test_mock_revision_gives_every_item_a_distinct_wording():
    items = [
        DraftItem(
            item_text=f"Original item {i}",
            construct_name="Belonging",
            rationale="reasonable",
            facet_name=["Acceptance", "Inclusion"][i % 2],
        )
        for i in range(15)
    ]
    texts = [it.item_text for it in _mock_revision(items).revised_items]
    assert len(texts) == 15
    assert len({t.strip().lower() for t in texts}) == 15
