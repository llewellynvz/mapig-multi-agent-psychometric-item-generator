"""Unit tests for the near-duplicate item removal fix."""

import numpy as np

from backend.agents import deduplicator
from backend.schemas import DraftItem


def _item(text):
    return DraftItem(item_text=text, construct_name="Test", rationale="reasonable")


def test_single_item_noop():
    kept, dropped = deduplicator.deduplicate_items([_item("only item")])
    assert len(kept) == 1
    assert dropped == []


def test_exact_duplicate_fallback(monkeypatch):
    """When embedding is unavailable, fall back to exact-string dedup."""
    import backend.agents.correlation_estimator as ce

    def _boom(*a, **k):
        raise RuntimeError("offline")

    monkeypatch.setattr(ce, "embed_items_sync", _boom)
    items = [
        _item("I feel energised at work"),
        _item("I feel energised at work"),
        _item("a different item"),
    ]
    kept, dropped = deduplicator.deduplicate_items(items)
    assert dropped == [1]
    assert len(kept) == 2


def test_near_duplicate_cosine_dedup(monkeypatch):
    """Items 0 and 1 are near-identical; item 1 must be dropped at threshold 0.85."""
    import backend.agents.correlation_estimator as ce

    vecs = {
        "I feel energised when I work": [1.0, 0.0],
        "I feel energised while I work": [0.99, 0.01],
        "a totally different item": [0.0, 1.0],
    }

    def fake_embed(texts, model=None):
        return np.array([vecs[t] for t in texts])

    def fake_cosine(emb):
        emb = np.asarray(emb, dtype=float)
        emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)
        return emb @ emb.T

    monkeypatch.setattr(ce, "embed_items_sync", fake_embed)
    monkeypatch.setattr(ce, "compute_cosine_similarity_matrix", fake_cosine)

    items = [
        _item("I feel energised when I work"),
        _item("I feel energised while I work"),
        _item("a totally different item"),
    ]
    kept, dropped = deduplicator.deduplicate_items(items, threshold=0.85)
    assert dropped == [1]
    assert len(kept) == 2


def test_distinct_items_kept(monkeypatch):
    import backend.agents.correlation_estimator as ce

    vecs = {
        "first item": [1.0, 0.0],
        "second item": [0.0, 1.0],
    }

    def fake_embed(texts, model=None):
        return np.array([vecs[t] for t in texts])

    def fake_cosine(emb):
        emb = np.asarray(emb, dtype=float)
        emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)
        return emb @ emb.T

    monkeypatch.setattr(ce, "embed_items_sync", fake_embed)
    monkeypatch.setattr(ce, "compute_cosine_similarity_matrix", fake_cosine)

    items = [_item("first item"), _item("second item")]
    kept, dropped = deduplicator.deduplicate_items(items, threshold=0.85)
    assert dropped == []
    assert len(kept) == 2
