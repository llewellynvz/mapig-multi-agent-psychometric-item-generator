"""Regression tests for small agent-level fixes (token usage, validator
recalc, pseudo-omega NaN guard, critic immutability, instrument search
fallbacks, persona mock determinism). No network, no LLM.
"""

import zlib

import httpx
import numpy as np
from langchain_core.messages import AIMessage

from backend.agents import instrument_searcher
from backend.agents.critic import _downgrade_construct_level_bias
from backend.agents.llm_utils import _extract_token_usage
from backend.agents.pfa_estimator import compute_pseudo_omega
from backend.agents.validator import _recalc_weighted_score
from backend.schemas import DimensionScore, ReviewComment
from backend.settings import settings


# ---- llm_utils._extract_token_usage ----


def test_extract_token_usage_reads_dict_usage_metadata():
    msg = AIMessage(
        content="x",
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    )
    usage = _extract_token_usage(msg, "m")
    assert (usage.input_tokens, usage.output_tokens, usage.total_tokens) == (10, 5, 15)


# ---- validator._recalc_weighted_score ----


def _ds(dim, score):
    return DimensionScore(dimension=dim, reasoning="", score=score)


def test_recalc_normalises_dimension_names():
    scores = [
        _ds("Correspondence ", 8),
        _ds("construct_distinctiveness", 8),
        _ds("CLARITY", 8),
        _ds("specificity", 8),
    ]
    assert abs(_recalc_weighted_score(scores) - 8.0) < 1e-9


def test_recalc_ignores_duplicate_dimensions():
    scores = [
        _ds("correspondence", 8),
        _ds("correspondence", 2),
        _ds("distinctiveness", 8),
        _ds("clarity", 8),
        _ds("specificity", 8),
    ]
    assert abs(_recalc_weighted_score(scores) - 8.0) < 1e-9


def test_recalc_returns_none_when_dimension_missing():
    scores = [_ds("relevance", 9), _ds("distinctiveness", 8), _ds("clarity", 8), _ds("specificity", 8)]
    assert _recalc_weighted_score(scores) is None


# ---- pfa_estimator.compute_pseudo_omega ----


def test_pseudo_omega_nan_loadings_returns_none():
    loadings = np.array([[0.7], [np.nan], [0.6]])
    assert compute_pseudo_omega(loadings) is None


def test_pseudo_omega_finite_loadings_unchanged():
    loadings = np.array([[0.7], [0.6], [0.5]])
    omega = compute_pseudo_omega(loadings)
    assert omega is not None and 0.0 < omega < 1.0


# ---- critic._downgrade_construct_level_bias ----


def test_construct_level_bias_downgrade_does_not_mutate_originals():
    originals = [
        ReviewComment(type="bias", item_index=i, issue="construct assumes western cultural norms", severity=4)
        for i in range(3)
    ]
    out = _downgrade_construct_level_bias(list(originals))
    assert all(c.severity == 1 for c in out)
    assert all(c.severity == 4 for c in originals)


# ---- instrument_searcher fallbacks ----


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


def _fake_client(behaviour):
    class _Client:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, *a, **kw):
            return behaviour()

    return _Client


def test_instrument_search_connect_error_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "PERPLEXITY_API_KEY", "test-key")

    def boom():
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(instrument_searcher.httpx, "Client", _fake_client(boom))
    assert instrument_searcher._search_perplexity_instrument("Grit", "convergent") is None


def test_instrument_search_empty_choices_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "PERPLEXITY_API_KEY", "test-key")
    monkeypatch.setattr(
        instrument_searcher.httpx, "Client", _fake_client(lambda: _FakeResponse({"choices": []}))
    )
    assert instrument_searcher._search_perplexity_instrument("Grit", "convergent") is None


def test_fetch_items_strips_citation_markers(monkeypatch):
    monkeypatch.setattr(settings, "PERPLEXITY_API_KEY", "test-key")
    content = (
        'According to Duckworth [1], the items are: '
        '["I finish whatever I begin", "I am a hard worker", "I am diligent always"] [2][3]'
    )
    monkeypatch.setattr(
        instrument_searcher.httpx,
        "Client",
        _fake_client(lambda: _FakeResponse({"choices": [{"message": {"content": content}}]})),
    )
    inst = instrument_searcher.ComparisonInstrument(
        name="Grit Scale", measured_construct="grit", source_citation="Duckworth (2007)",
    )
    out = instrument_searcher._fetch_instrument_items(inst)
    assert out.items == ["I finish whatever I begin", "I am a hard worker", "I am diligent always"]


# ---- persona_validator mock determinism ----


def test_persona_mock_offset_is_process_stable(monkeypatch):
    from backend.agents import persona_validator

    monkeypatch.setattr(settings, "APP_MODE", "mock")
    label = "A retired teacher in rural Kenya"
    out, _ = persona_validator._rate_items_for_persona(None, label, [object(), object()])
    offset = zlib.crc32(label.encode("utf-8")) % 5
    assert out.ratings[0].rating == (offset % 5) + 1
