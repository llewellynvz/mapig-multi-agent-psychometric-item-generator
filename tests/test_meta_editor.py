"""Tests for meta_editor rationale truncation and pre-validation hook."""

import os

os.environ["APP_MODE"] = "mock"

import pytest
from backend.agents.meta_editor import _truncate_rationale, _clamp_rationales, _RATIONALE_MAX


class TestTruncateRationale:
    """Tests for _truncate_rationale sentence-boundary truncation."""

    def test_short_rationale_unchanged(self):
        text = "Targets affective engagement with work tasks."
        assert _truncate_rationale(text) == text

    def test_exactly_at_limit_unchanged(self):
        text = "x" * _RATIONALE_MAX
        assert _truncate_rationale(text) == text

    def test_truncates_at_sentence_boundary(self):
        # Two sentences: first fits, second pushes over limit
        first = "Targets cognitive flexibility in problem-solving contexts."  # 59 chars
        second = "x" * (_RATIONALE_MAX - 30)  # Pushes total well over limit
        text = f"{first} {second}"
        result = _truncate_rationale(text)
        assert len(result) <= _RATIONALE_MAX
        assert result.endswith(".")

    def test_hard_truncation_when_no_sentence_boundary(self):
        # Single long word with no periods
        text = "a" * (_RATIONALE_MAX + 100)
        result = _truncate_rationale(text)
        assert len(result) <= _RATIONALE_MAX
        assert result.endswith("...")

    def test_truncates_at_semicolon_boundary(self):
        first = "Measures behavioral intent" + "x" * 300
        text = first + "; also captures affective resonance with daily routines and habits across domains."
        assert len(text) > _RATIONALE_MAX
        result = _truncate_rationale(text)
        assert len(result) <= _RATIONALE_MAX

    def test_preserves_period_in_parenthetical(self):
        first = "Assesses self-regulation (per Bandura, 1997.)" + " " + "x" * 350
        result = _truncate_rationale(first)
        assert len(result) <= _RATIONALE_MAX


class TestClampRationales:
    """Tests for _clamp_rationales pre-validation hook."""

    def test_clamps_oversized_rationale(self):
        data = {
            "revised_items": [
                {
                    "item_text": "I feel satisfied with my life.",
                    "construct_name": "Life Satisfaction",
                    "rationale": "x" * 500,
                    "evidence_citations": [],
                }
            ],
            "revision_plan": {"summary": "test"},
        }
        result = _clamp_rationales(data)
        assert len(result["revised_items"][0]["rationale"]) <= _RATIONALE_MAX

    def test_leaves_short_rationale_unchanged(self):
        original = "Targets core affective engagement."
        data = {
            "revised_items": [
                {
                    "item_text": "test",
                    "construct_name": "test",
                    "rationale": original,
                    "evidence_citations": [],
                }
            ],
            "revision_plan": {"summary": "test"},
        }
        result = _clamp_rationales(data)
        assert result["revised_items"][0]["rationale"] == original

    def test_clamps_multiple_items(self):
        data = {
            "revised_items": [
                {"item_text": f"item {i}", "construct_name": "test",
                 "rationale": "y" * 500, "evidence_citations": []}
                for i in range(5)
            ],
            "revision_plan": {"summary": "test"},
        }
        result = _clamp_rationales(data)
        for item in result["revised_items"]:
            assert len(item["rationale"]) <= _RATIONALE_MAX

    def test_handles_missing_revised_items(self):
        data = {"revision_plan": {"summary": "test"}}
        result = _clamp_rationales(data)
        assert result == data

    def test_handles_empty_revised_items(self):
        data = {"revised_items": [], "revision_plan": {"summary": "test"}}
        result = _clamp_rationales(data)
        assert result["revised_items"] == []
