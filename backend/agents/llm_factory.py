from __future__ import annotations

from functools import lru_cache
from typing import Union

from langchain_anthropic import ChatAnthropic
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from backend.settings import settings


@lru_cache(maxsize=1)
def get_openai_chat_model() -> ChatOpenAI:
    """Create (and cache) the OpenAI ChatOpenAI client."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("APP_MODE=openai but missing required setting: OPENAI_API_KEY")

    kwargs = {
        "model": settings.OPENAI_MODEL,
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

    return ChatAnthropic(
        model=model,
        api_key=settings.CLAUDE_API_KEY,
        temperature=0.2,
        max_retries=3,
        timeout=60,
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

    Args:
        agent_name: Agent identifier (e.g., "validator", "item_writer", "bias_reviewer")
        model_provider: "claude" or "openai"

    Returns:
        Configured chat model instance

    Raises:
        ValueError: If required API key missing for selected provider
    """
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
