"""Tests for meta_editor rationale truncation and pre-validation hook."""

import os

os.environ["APP_MODE"] = "mock"

import pytest
from backend.agents.meta_editor import (
    _RATIONALE_MAX,
    _clamp_rationales,
    _contains_negation,
    _enforce_positive_keying,
    _truncate_rationale,
)
from backend.schemas import DraftItem, UserRequest


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


# ----- Phase 14-16 follow-up: positive-keying enforcement -----


def _make_request(constraints: list[str] | None = None) -> UserRequest:
    return UserRequest(
        construct_name="Test Construct",
        construct_definition="An operational definition for testing.",
        target_population="adults",
        response_scale="5-point Likert",
        item_count=3,
        constraints=constraints or [],
        model_provider="claude",
    )


def _make_item(text: str) -> DraftItem:
    return DraftItem(
        item_text=text,
        construct_name="Test Construct",
        rationale="synthetic rationale",
        facet_name="Single Factor",
    )


class TestNegationDetection:
    def test_detects_not(self):
        assert _contains_negation("This does not work")
        assert _contains_negation("This Does NOT Work")  # case-insensitive

    def test_detects_contraction(self):
        assert _contains_negation("This doesn't work")
        assert _contains_negation("I haven't tried it")

    def test_detects_never(self):
        assert _contains_negation("I never try a new approach")

    def test_detects_no_as_word(self):
        assert _contains_negation("I have no plan when things change")

    def test_does_not_match_word_substrings(self):
        # "another" contains "not" as substring but not as a word
        assert not _contains_negation("I try another approach")
        # "innovate" contains "no" as substring but not as word
        assert not _contains_negation("I innovate when problems arise")

    def test_clean_positive_text_passes(self):
        assert not _contains_negation("I try a different way when my method falls short")


class TestEnforcePositiveKeying:
    def test_reverts_when_llm_introduces_negation(self):
        request = _make_request(["Positively keyed only"])
        original = [_make_item("When my first method fails, I try a different way.")]
        revised = [_make_item("When my first method does not work, I try a different way.")]

        out = _enforce_positive_keying(request, original, revised)
        # Revised item should be reverted to the original text
        assert out[0].item_text == original[0].item_text

    def test_does_not_revert_when_negation_was_already_in_original(self):
        # If the user's original item already had "no" (e.g., baseline drafts)
        # we don't revert — the LLM didn't introduce it.
        request = _make_request(["Positively keyed only"])
        original = [_make_item("I have no problems with the work.")]
        revised = [_make_item("I have no problems with my work.")]
        out = _enforce_positive_keying(request, original, revised)
        # Revised text is kept (LLM didn't introduce negation)
        assert out[0].item_text == revised[0].item_text

    def test_does_nothing_when_constraint_absent(self):
        # When "Positively keyed only" is NOT in constraints, no enforcement.
        request = _make_request(constraints=["No double-barrelled items"])
        original = [_make_item("When my first method fails, I try a different way.")]
        revised = [_make_item("When my first method does not work, I try a different way.")]
        out = _enforce_positive_keying(request, original, revised)
        assert out[0].item_text == revised[0].item_text  # negation kept

    def test_clean_revisions_pass_through(self):
        request = _make_request(["Positively keyed only"])
        original = [_make_item("When plans change, I switch.")]
        revised = [_make_item("When plans change, I switch to a different plan.")]
        out = _enforce_positive_keying(request, original, revised)
        assert out[0].item_text == revised[0].item_text

    def test_partial_revert_only_for_violators(self):
        """Multi-item revert: only the violating item is reverted, others kept."""
        request = _make_request(["Positively keyed only"])
        original = [
            _make_item("When plans change, I switch."),
            _make_item("I adjust my approach when needed."),
        ]
        revised = [
            _make_item("When plans change, I switch to a new plan."),
            _make_item("I adjust my approach when something does not work."),  # has "not"
        ]
        out = _enforce_positive_keying(request, original, revised)
        assert out[0].item_text == revised[0].item_text  # clean — kept
        assert out[1].item_text == original[1].item_text  # negation introduced — reverted
