"""Test suite for Bias Reviewer agent.

This module tests the Bias Reviewer prompt structure and evaluation process.
"""

import pytest
from pathlib import Path


def test_structured_checklist():
    """Test that Bias Reviewer prompt includes structured checklist format.

    AGT-08: Structured checklist enables comprehensive single-pass evaluation.

    Expected behavior:
    - Prompt includes step-by-step evaluation process
    - Checklist format with explicit steps (Step 1, Step 2, etc.)
    - Intersectional bias check as separate step
    - Severity escalation rule for intersectional flags (≥4)
    """
    prompt_path = Path("app/prompts/bias_reviewer.md")
    assert prompt_path.exists(), "bias_reviewer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify structured checklist format present
    assert "structured checklist" in content_lower or "evaluation process" in content_lower, \
        "Prompt must include structured checklist or evaluation process section"

    # Verify step-by-step format
    assert "step 1" in content_lower and "step 2" in content_lower, \
        "Prompt must include step-by-step evaluation process (Step 1, Step 2, etc.)"

    # Verify intersectional bias check as separate step
    assert "intersectional bias" in content_lower, \
        "Prompt must include intersectional bias check"

    # Verify severity escalation rule
    assert "severity" in content_lower, \
        "Prompt must include severity guidance"

    # Verify escalation for intersectional bias (≥4 or "major")
    has_escalation = "≥4" in content or ">=4" in content or "4 or higher" in content_lower or \
                     ("intersectional" in content_lower and "major" in content_lower)
    assert has_escalation, \
        "Prompt must specify severity escalation rule for intersectional bias (≥4 or major issue)"
