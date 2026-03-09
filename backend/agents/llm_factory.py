from __future__ import annotations

from functools import lru_cache
from typing import Optional, Union

from langchain_anthropic import ChatAnthropic
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from backend.settings import settings


# Agent model overrides for cost optimization
# Format: "agent_name": ("provider", "model_name")
AGENT_MODEL_OVERRIDES = {
    "bias_reviewer": ("openai", "gpt-4o-mini"),  # 20x cheaper than Sonnet, async OK
    "critic": ("openai", "gpt-4o-mini"),  # 20x cheaper, has rule fallback
}


@lru_cache(maxsize=3)
def get_openai_chat_model(model: Optional[str] = None) -> ChatOpenAI:
    """Create (and cache) the OpenAI ChatOpenAI client.

    Args:
        model: Optional model name override. If not provided, uses settings.OPENAI_MODEL.

    Returns:
        ChatOpenAI instance configured for the specified model
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key required for OpenAI models")

    model_name = model or settings.OPENAI_MODEL

    kwargs = {
        "model": model_name,
        "api_key": settings.OPENAI_API_KEY,
        "temperature": 0.2,
        "max_retries": 3,
        "timeout": 60,
    }
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL

    return ChatOpenAI(**kwargs)


@lru_cache(maxsize=1)
def get_azure_chat_model() -> AzureChatOpenAI:
    """Create (and cache) the AzureChatOpenAI client."""
    missing = []
    if not settings.AZURE_OPENAI_ENDPOINT:
        missing.append("AZURE_OPENAI_ENDPOINT")
    if not settings.AZURE_OPENAI_API_KEY:
        missing.append("AZURE_OPENAI_API_KEY")
    if not settings.AZURE_OPENAI_DEPLOYMENT:
        missing.append("AZURE_OPENAI_DEPLOYMENT")
    if missing:
        raise ValueError("APP_MODE=azure but missing required settings: " + ", ".join(missing))

    return AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        temperature=0.2,
        max_retries=3,
        timeout=60,
    )


@lru_cache(maxsize=2)
def get_claude_chat_model(model: str = "claude-opus-4-6") -> ChatAnthropic:
    """Create (and cache) the Claude ChatAnthropic client.

    Args:
        model: Claude model name (e.g., "claude-opus-4-6", "claude-sonnet-4-5")

    Returns:
        ChatAnthropic instance configured for the specified model

    Raises:
        ValueError: If CLAUDE_API_KEY is not configured
    """
    if not settings.CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY required for Claude models")

    # Enable prompt caching for cost savings
    # Ref: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
    return ChatAnthropic(
        model=model,
        api_key=settings.CLAUDE_API_KEY,
        temperature=0.2,
        max_retries=3,
        timeout=60,
        # Enable prompt caching to reduce input token costs by ~50% for repeated prompts
        default_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )


def get_validator_model() -> ChatAnthropic:
    """Get validation model (always Opus for highest accuracy).

    Returns:
        ChatAnthropic instance configured with claude-opus-4-6

    Raises:
        ValueError: If CLAUDE_API_KEY is not configured
    """
    return get_claude_chat_model(model=settings.VALIDATOR_MODEL)


def get_chat_model_for_agent(
    agent_name: str,
    model_provider: str = "claude"
) -> Union[ChatOpenAI, AzureChatOpenAI, ChatAnthropic]:
    """Get LLM for specific agent with smart model allocation.

    Smart allocation for Claude provider:
    - validator agent: claude-opus-4-6 (highest accuracy for critical validation)
    - all other agents: claude-sonnet-4-5 (cost-effective for drafting/reviewing)

    Agent overrides (when AGENT_MODEL_OVERRIDES_ENABLED):
    - bias_reviewer: gpt-4o-mini (20x cheaper than Sonnet, fairness detection OK)
    - critic: gpt-4o-mini (20x cheaper, has rule fallback)

    Args:
        agent_name: Agent identifier (e.g., "validator", "item_writer", "bias_reviewer")
        model_provider: "claude" or "openai"

    Returns:
        Configured chat model instance

    Raises:
        ValueError: If required API key missing for selected provider
    """
    # Check for agent-specific overrides first
    if settings.AGENT_MODEL_OVERRIDES_ENABLED and agent_name in AGENT_MODEL_OVERRIDES:
        override_provider, override_model = AGENT_MODEL_OVERRIDES[agent_name]
        if override_provider == "openai":
            return get_openai_chat_model(model=override_model)
        elif override_provider == "claude":
            return get_claude_chat_model(model=override_model)

    # Default allocation based on provider
    if model_provider == "claude":
        if agent_name == "validator":
            return get_claude_chat_model(model="claude-opus-4-6")
        else:
            # All other agents use Sonnet for cost optimization
            return get_claude_chat_model(model="claude-sonnet-4-5")
    elif model_provider == "openai":
        return get_openai_chat_model()
    else:
        raise ValueError(f"Unsupported model_provider: {model_provider}")


def get_chat_model() -> Union[ChatOpenAI, AzureChatOpenAI, ChatAnthropic]:
    """Return the configured chat model for the current APP_MODE."""
    if settings.APP_MODE == "openai":
        return get_openai_chat_model()
    if settings.APP_MODE == "azure":
        return get_azure_chat_model()
    if settings.APP_MODE == "claude":
        # Default to Sonnet for general use
        return get_claude_chat_model(model="claude-sonnet-4-5")
    raise RuntimeError("get_chat_model called in mock mode. Use the mock agents instead.")
