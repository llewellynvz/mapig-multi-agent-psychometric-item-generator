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
    from unittest.mock import patch
    from app.agents.llm_factory import get_validator_model, get_claude_chat_model
    from app.settings import settings
    from langchain_anthropic import ChatAnthropic

    # Mock the settings object's CLAUDE_API_KEY
    with patch.object(settings, 'CLAUDE_API_KEY', "test-key-12345"):
        # Clear any cached instances
        if hasattr(get_claude_chat_model, 'cache_clear'):
            get_claude_chat_model.cache_clear()

        model = get_validator_model()

        # Verify type
        assert isinstance(model, ChatAnthropic), "get_validator_model should return ChatAnthropic"

        # Verify model name
        assert model.model == "claude-opus-4-6", "Validator should use claude-opus-4-6"

        # Verify temperature
        assert model.temperature == 0.2, "Temperature should be 0.2 for deterministic scoring"

        # Verify max_retries
        assert model.max_retries == 3, "Max retries should be 3"


def test_claude_api_key_required():
    """Verify get_validator_model() raises ValueError if CLAUDE_API_KEY not set.

    Tests error handling for missing Claude API credentials.

    Expected behavior:
    - When CLAUDE_API_KEY is None or empty string
    - get_validator_model() raises ValueError
    - Error message is clear: "CLAUDE_API_KEY required for Claude models"
    - No API calls are made if key is missing
    """
    from unittest.mock import patch
    from app.agents.llm_factory import get_validator_model, get_claude_chat_model
    from app.settings import settings

    # Mock settings to have no API key
    with patch.object(settings, 'CLAUDE_API_KEY', None):
        # Clear cache
        if hasattr(get_claude_chat_model, 'cache_clear'):
            get_claude_chat_model.cache_clear()

        with pytest.raises(ValueError) as exc_info:
            get_validator_model()

        error_msg = str(exc_info.value).lower()
        assert "claude_api_key" in error_msg or "claude" in error_msg, \
            "Error message should mention CLAUDE_API_KEY or Claude models"


# Phase 03: Smart Model Allocation Tests


def test_smart_allocation_validator_uses_opus():
    """Phase 03-01: get_chat_model_for_agent('validator', 'claude') returns Opus."""
    from unittest.mock import patch
    from app.agents.llm_factory import get_chat_model_for_agent, get_claude_chat_model
    from app.settings import settings
    from langchain_anthropic import ChatAnthropic

    # Mock CLAUDE_API_KEY
    with patch.object(settings, 'CLAUDE_API_KEY', "test-key-12345"):
        # Clear cache
        if hasattr(get_claude_chat_model, 'cache_clear'):
            get_claude_chat_model.cache_clear()

        # Act: Get model for validator agent with Claude provider
        model = get_chat_model_for_agent("validator", "claude")

        # Assert: Returns ChatAnthropic with Opus model
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-opus-4-6"
        assert model.temperature == 0.2


def test_smart_allocation_other_agents_use_sonnet():
    """Phase 03-01: Non-validator agents use Sonnet for cost optimization."""
    from unittest.mock import patch
    from app.agents.llm_factory import get_chat_model_for_agent, get_claude_chat_model
    from app.settings import settings
    from langchain_anthropic import ChatAnthropic

    # Mock CLAUDE_API_KEY
    with patch.object(settings, 'CLAUDE_API_KEY', "test-key-12345"):
        # Clear cache
        if hasattr(get_claude_chat_model, 'cache_clear'):
            get_claude_chat_model.cache_clear()

        # Test multiple agent names
        for agent_name in ["item_writer", "bias_reviewer", "linguistic_reviewer", "content_reviewer"]:
            model = get_chat_model_for_agent(agent_name, "claude")

            assert isinstance(model, ChatAnthropic)
            assert model.model == "claude-sonnet-4-5", f"{agent_name} should use Sonnet"
            assert model.temperature == 0.2


def test_openai_provider_returns_openai_model():
    """Phase 03-01: get_chat_model_for_agent with 'openai' provider returns ChatOpenAI."""
    from unittest.mock import patch
    from app.agents.llm_factory import get_chat_model_for_agent, get_openai_chat_model
    from app.settings import settings
    from langchain_openai import ChatOpenAI

    # Mock OPENAI_API_KEY
    with patch.object(settings, 'OPENAI_API_KEY', "test-openai-key"):
        # Clear cache
        if hasattr(get_openai_chat_model, 'cache_clear'):
            get_openai_chat_model.cache_clear()

        # Act: Get model with openai provider
        model = get_chat_model_for_agent("validator", "openai")

        # Assert: Returns ChatOpenAI (not Claude)
        assert isinstance(model, ChatOpenAI)


def test_missing_claude_key_raises_error():
    """Phase 03-01: Missing CLAUDE_API_KEY raises ValueError for claude provider."""
    from unittest.mock import patch
    from app.agents.llm_factory import get_chat_model_for_agent, get_claude_chat_model
    from app.settings import settings

    # Mock settings to have no Claude API key
    with patch.object(settings, 'CLAUDE_API_KEY', None):
        # Clear cache
        if hasattr(get_claude_chat_model, 'cache_clear'):
            get_claude_chat_model.cache_clear()

        # Act & Assert: Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            get_chat_model_for_agent("validator", "claude")

        error_msg = str(exc_info.value).lower()
        assert "claude" in error_msg or "api" in error_msg
