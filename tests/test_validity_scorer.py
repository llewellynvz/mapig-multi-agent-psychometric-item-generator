"""Phase 9 Plan 02 Task 1: Dual-direction validity scoring tests (TDD)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.agents.validity_scorer import (
    score_convergent_validity,
    score_discriminant_validity,
)
from backend.schemas import ConstructPairAnalysis


# Test 1: score_convergent_validity returns float 0.0-1.0 by averaging forward and reverse scores
def test_convergent_validity_returns_averaged_float():
    """Convergent validity score averages forward and reverse LLM judgments."""
    generated_items = [
        "I feel confident in my abilities",
        "I believe I can succeed at most tasks"
    ]
    instrument_name = "Self-Efficacy Scale"
    instrument_construct = "self-efficacy"
    target_construct = "self-efficacy"

    # Mock GPT-5.2 to return different scores for forward/reverse
    mock_model = MagicMock()
    mock_forward_response = {
        "parsed": MagicMock(score=0.8, reasoning="Strong alignment forward")
    }
    mock_reverse_response = {
        "parsed": MagicMock(score=0.6, reasoning="Moderate alignment reverse")
    }

    # First call returns forward, second returns reverse
    mock_model.with_structured_output.return_value.invoke.side_effect = [
        mock_forward_response,
        mock_reverse_response
    ]

    with patch("backend.agents.validity_scorer.get_gpt52_analytics_model", return_value=mock_model):
        score, method = score_convergent_validity(
            generated_items, instrument_name, instrument_construct, target_construct
        )

    # Should average: (0.8 + 0.6) / 2.0 = 0.7
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert score == pytest.approx(0.7, abs=0.01)
    assert method == "llm-as-judge"


# Test 2: Forward and reverse scores are both called (dual-direction verified)
def test_convergent_validity_calls_both_directions():
    """Verify dual-direction pattern: both forward and reverse scoring invoked."""
    generated_items = ["Item 1", "Item 2"]

    mock_model = MagicMock()
    mock_response = {
        "parsed": MagicMock(score=0.75, reasoning="Test reasoning")
    }
    mock_model.with_structured_output.return_value.invoke.return_value = mock_response

    with patch("backend.agents.validity_scorer.get_gpt52_analytics_model", return_value=mock_model):
        score_convergent_validity(
            generated_items, "Test Scale", "test-construct", "test-construct"
        )

    # Should be called exactly twice (forward + reverse)
    assert mock_model.with_structured_output.return_value.invoke.call_count == 2


# Test 3: score_discriminant_validity returns ConstructPairAnalysis with estimated_correlation and validity_flag
def test_discriminant_validity_returns_construct_pair_analysis():
    """Discriminant validity scoring returns structured ConstructPairAnalysis."""
    generated_items = ["Self-esteem item 1", "Self-esteem item 2"]
    instrument_name = "Self-Efficacy Scale"
    instrument_construct = "self-efficacy"
    target_construct = "self-esteem"

    # Mock GPT-5.2 to return correlation estimates
    mock_model = MagicMock()
    mock_forward_response = {
        "parsed": MagicMock(estimated_correlation=0.50, reasoning="Moderate overlap forward")
    }
    mock_reverse_response = {
        "parsed": MagicMock(estimated_correlation=0.60, reasoning="Moderate overlap reverse")
    }
    mock_model.with_structured_output.return_value.invoke.side_effect = [
        mock_forward_response,
        mock_reverse_response
    ]

    with patch("backend.agents.validity_scorer.get_gpt52_analytics_model", return_value=mock_model):
        result, method = score_discriminant_validity(
            generated_items, instrument_name, instrument_construct, target_construct
        )

    assert isinstance(result, ConstructPairAnalysis)
    assert method == "llm-as-judge"
    assert result.construct_a == target_construct
    assert result.construct_b == instrument_construct
    assert result.estimated_correlation is not None
    # Should average: (0.50 + 0.60) / 2.0 = 0.55
    assert result.estimated_correlation == pytest.approx(0.55, abs=0.01)
    assert result.discriminant_validity_flag in ["adequate", "concern", "poor"]
    assert result.reasoning is not None


# Test 4: discriminant_validity_flag is "concern" when estimated_correlation > 0.85
def test_discriminant_flag_concern_for_high_correlation():
    """High correlation (>0.85) triggers 'concern' validity flag."""
    generated_items = ["Test item"]

    # Mock very high correlation (averaged to 0.90)
    mock_model = MagicMock()
    mock_response = {
        "parsed": MagicMock(estimated_correlation=0.90, reasoning="High overlap")
    }
    mock_model.with_structured_output.return_value.invoke.return_value = mock_response

    with patch("backend.agents.validity_scorer.get_gpt52_analytics_model", return_value=mock_model):
        result, _ = score_discriminant_validity(
            generated_items, "High Overlap Scale", "nearly-identical", "target"
        )

    assert result.discriminant_validity_flag == "concern"


# Test 5: discriminant_validity_flag is "adequate" when estimated_correlation < 0.85
def test_discriminant_flag_adequate_for_low_correlation():
    """Low correlation (<0.85) results in 'adequate' validity flag."""
    generated_items = ["Test item"]

    # Mock low correlation (averaged to 0.40)
    mock_model = MagicMock()
    mock_response = {
        "parsed": MagicMock(estimated_correlation=0.40, reasoning="Low overlap")
    }
    mock_model.with_structured_output.return_value.invoke.return_value = mock_response

    with patch("backend.agents.validity_scorer.get_gpt52_analytics_model", return_value=mock_model):
        result, _ = score_discriminant_validity(
            generated_items, "Distinct Scale", "unrelated-construct", "target"
        )

    assert result.discriminant_validity_flag == "adequate"


# Test 6: Both scoring functions handle LLM errors gracefully (return sensible defaults)
def test_convergent_validity_handles_llm_error_gracefully():
    """LLM errors result in neutral default score (0.5), not exceptions."""
    generated_items = ["Test item"]

    # Mock LLM error
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value.invoke.side_effect = Exception("LLM timeout")

    with patch("backend.agents.validity_scorer.get_gpt52_analytics_model", return_value=mock_model):
        score, method = score_convergent_validity(
            generated_items, "Test Scale", "test", "test"
        )

    # Should return neutral default on error
    assert score == 0.5
    assert method == "llm-as-judge"


def test_discriminant_validity_handles_llm_error_gracefully():
    """LLM errors result in sensible defaults, not exceptions."""
    generated_items = ["Test item"]

    # Mock LLM error
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value.invoke.side_effect = RuntimeError("Parse failure")

    with patch("backend.agents.validity_scorer.get_gpt52_analytics_model", return_value=mock_model):
        result, method = score_discriminant_validity(
            generated_items, "Test Scale", "test", "target"
        )

    # Should return sensible defaults
    assert isinstance(result, ConstructPairAnalysis)
    assert method == "llm-as-judge"
    assert result.estimated_correlation is not None
    assert result.discriminant_validity_flag == "adequate"
    assert "unavailable" in result.reasoning.lower() or "error" in result.reasoning.lower()
