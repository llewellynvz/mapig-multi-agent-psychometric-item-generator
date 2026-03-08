"""Test suite for reviewer prompts.

This module tests that Content Reviewer and Linguistic Reviewer prompts
contain research-backed evaluation criteria.
"""

import pytest
from pathlib import Path


def test_content_reviewer_criteria():
    """Test that Content Reviewer prompt includes construct correspondence criteria."""
    prompt_path = Path("app/prompts/content_reviewer.md")
    assert prompt_path.exists(), "content_reviewer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for construct definition anchoring
    assert "construct definition anchoring" in content or "definition anchoring" in content, \
        "Prompt must include construct definition anchoring guidance"

    # Check for competitor construct specification
    assert "competitor construct specification" in content or "competitor specification" in content, \
        "Prompt must include competitor construct specification guidance"

    # Check for facet coverage tracking
    assert "facet coverage tracking" in content or "facet coverage" in content, \
        "Prompt must include facet coverage tracking guidance"

    # Check for actionable guidance (key elements)
    assert "key element" in content, \
        "Prompt must instruct extracting key elements from definition"

    # Check for imbalance detection
    assert "imbalance" in content or "2:1" in content, \
        "Prompt must include imbalance detection guidance"


def test_linguistic_reviewer_quantifiers():
    """Test that Linguistic Reviewer prompt includes vague quantifier rules with 3 categories."""
    prompt_path = Path("app/prompts/linguistic_reviewer.md")
    assert prompt_path.exists(), "linguistic_reviewer.md prompt file must exist"

    content = prompt_path.read_text(encoding="utf-8").lower()

    # Check for vague quantifier detection
    assert "vague quantifier" in content or "quantifier" in content, \
        "Prompt must include vague quantifier detection guidance"

    # Check for 3 categories
    assert "category 1" in content, "Prompt must define Category 1 quantifiers"
    assert "category 2" in content, "Prompt must define Category 2 quantifiers"
    assert "category 3" in content, "Prompt must define Category 3 quantifiers"

    # Check for time anchoring
    assert "time anchor" in content or "temporal" in content, \
        "Prompt must include time anchoring guidance"

    # Check for repair guidance
    assert "fix" in content or "repair" in content, \
        "Prompt must include repair guidance for vague quantifiers"

    # Check for specific quantifier examples
    assert "often" in content or "sometimes" in content, \
        "Prompt must include Category 1 quantifier examples"
    assert "never" in content or "always" in content, \
        "Prompt must include Category 2 quantifier examples"
    assert "typically" in content or "generally" in content, \
        "Prompt must include Category 3 quantifier examples"
