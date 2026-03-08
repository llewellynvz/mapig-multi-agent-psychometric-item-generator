"""Test suite for LLM factory Claude model selection.

This module tests the LLM factory's ability to create Claude Opus
and Sonnet models with proper configuration.
"""

import os
import pytest

os.environ["APP_MODE"] = "mock"


def test_validator_uses_opus():
    """Verify get_validator_model() returns ChatAnthropic with Claude Opus.

    Tests VAL-07: Claude Opus model for validation agent (highest accuracy).

    Expected behavior:
    - get_validator_model() returns ChatAnthropic instance
    - Model name is "claude-opus-4-6"
    - Temperature is set to 0.2 (deterministic scoring)
    - API key is configured from settings.CLAUDE_API_KEY
    - Function is cached (lru_cache) for performance
    """
    pytest.skip("Awaiting LLM factory Claude integration in plan 01-02")


def test_claude_api_key_required():
    """Verify get_validator_model() raises ValueError if CLAUDE_API_KEY not set.

    Tests error handling for missing Claude API credentials.

    Expected behavior:
    - When CLAUDE_API_KEY is None or empty string
    - get_validator_model() raises ValueError
    - Error message is clear: "CLAUDE_API_KEY required for Claude models"
    - No API calls are made if key is missing
    """
    pytest.skip("Awaiting LLM factory Claude integration in plan 01-02")
