from __future__ import annotations

from functools import lru_cache
from typing import Optional, Union

from langchain_anthropic import ChatAnthropic
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from backend.settings import settings


# Agent model overrides for cost optimization
# Format: "agent_name": ("provider", "model_name")
AGENT_MODEL_OVERRIDES = {
    "bias_reviewer": ("openai", "gpt-5.4-mini"),  # Cost-effective for fairness detection
    "critic": ("openai", "gpt-5.4-mini"),  # Cost-effective, has rule fallback (90% zero-token)
    # Phase 14-16: PFA + Expert Panel + Persona Validator
    "persona_validator": ("openai", "gpt-5.4-mini"),  # Lightweight ambiguity detection
    "expert_panel_psychometric": ("openai", "gpt-5.4-mini"),  # Cost-controlled face validity
    "expert_panel_domain": ("openai", "gpt-5.4-mini"),  # Cost-controlled construct fidelity
    "expert_panel_localization": ("openai", "gpt-5.4-mini"),  # Cost-controlled cultural fit
    # Phase 17: Synthetic-respondent pilot
    "synthetic_respondent": ("openai", "gpt-5.4-mini"),  # One cheap call per simulated respondent
}

# Default per-request client timeout; agents with long outputs (meta_editor)
# get a larger budget via _agent_timeout().
DEFAULT_CLIENT_TIMEOUT_SECONDS = 45


DEFAULT_CLIENT_MAX_RETRIES = 3


def _agent_timeout(agent_name: str, default: int = DEFAULT_CLIENT_TIMEOUT_SECONDS) -> int:
    """Default client timeout for an agent (part of the client cache key).

    The meta-editor writes long outputs and gets its own timeout on every
    path. Callers with a hard time budget (the meta-editor node) pass an
    explicit timeout/max_retries to get_chat_model_for_agent instead."""
    if agent_name == "meta_editor":
        return settings.META_EDITOR_TIMEOUT_SECONDS
    return default


@lru_cache(maxsize=6)
def get_openai_chat_model(
    model: Optional[str] = None,
    timeout: int = DEFAULT_CLIENT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_CLIENT_MAX_RETRIES,
) -> ChatOpenAI:
    """Create (and cache) the OpenAI ChatOpenAI client.

    Args:
        model: Optional model name override. If not provided, uses settings.OPENAI_MODEL.
        timeout: Per-request timeout in seconds.
        max_retries: SDK retries after a failed or timed-out request.

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
        "max_retries": max_retries,
        "timeout": timeout,
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
        timeout=45,
    )


AZURE_CLIENT_TIMEOUT_SECONDS = 180


# TEMPORARY — remove after Azure evaluation
@lru_cache(maxsize=8)
def get_azure_test_chat_model(
    deployment: str, timeout: int, max_retries: int = DEFAULT_CLIENT_MAX_RETRIES
) -> AzureChatOpenAI:
    """Create (and cache) an AzureChatOpenAI client authenticated via Azure AD certificate."""
    if not settings.AZURE_OPENAI_ENDPOINT:
        raise RuntimeError(
            "AZURE_TEST_OVERRIDE is enabled but AZURE_OPENAI_ENDPOINT is not set. "
            "Set it in .env, then restart the backend."
        )

    from backend.agents.azure_auth import (
        azure_token_provider,
        azure_token_provider_async,
        get_azure_credential,
    )

    get_azure_credential()

    return AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        azure_deployment=deployment,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_ad_token_provider=azure_token_provider,
        azure_ad_async_token_provider=azure_token_provider_async,
        max_retries=max_retries,
        timeout=timeout,
    )


# TEMPORARY — remove after Azure evaluation
def _azure_test_route(
    agent_name: str,
    model_provider: str,
    use_chatgpt_critics: bool,
    timeout: Optional[int] = None,
    max_retries: int = DEFAULT_CLIENT_MAX_RETRIES,
) -> Optional[AzureChatOpenAI]:
    """Mirror of the get_chat_model_for_agent decision tree for the Azure test override.

    Returns None for Claude-bound agents so the caller falls through to the
    normal allocation logic unchanged.
    """
    deployment = _azure_deployment_for(agent_name, model_provider, use_chatgpt_critics)
    if deployment is None:
        return None
    return get_azure_test_chat_model(
        deployment, timeout or _agent_timeout(agent_name, AZURE_CLIENT_TIMEOUT_SECONDS), max_retries
    )


def _azure_deployment_for(
    agent_name: str,
    model_provider: str,
    use_chatgpt_critics: bool,
) -> Optional[str]:
    if settings.AZURE_TEST_SCOPE == "all_agents":
        return settings.AZURE_FRONTIER_DEPLOYMENT

    CRITIC_AGENTS = ["linguistic_reviewer", "bias_reviewer", "content_reviewer", "critic"]

    if use_chatgpt_critics and agent_name in CRITIC_AGENTS:
        return settings.AZURE_FRONTIER_DEPLOYMENT

    if agent_name == "item_writer":
        return None

    if settings.AGENT_MODEL_OVERRIDES_ENABLED and agent_name in AGENT_MODEL_OVERRIDES:
        override_provider, _ = AGENT_MODEL_OVERRIDES[agent_name]
        if override_provider == "openai":
            return settings.AZURE_CHEAP_DEPLOYMENT
        return None

    if model_provider == "openai":
        return settings.AZURE_FRONTIER_DEPLOYMENT

    return None


# TEMPORARY — remove after Azure evaluation
def _get_azure_test_analytics_model() -> AzureChatOpenAI:
    """Azure-hosted replacement for the GPT-5.2 analytics client."""
    if not settings.AZURE_OPENAI_ENDPOINT:
        raise RuntimeError(
            "AZURE_TEST_OVERRIDE is enabled but AZURE_OPENAI_ENDPOINT is not set. "
            "Set it in .env, then restart the backend."
        )

    from backend.agents.azure_auth import (
        azure_token_provider,
        azure_token_provider_async,
        get_azure_credential,
    )

    get_azure_credential()

    kwargs = {
        "azure_endpoint": settings.AZURE_OPENAI_ENDPOINT,
        "azure_deployment": settings.AZURE_FRONTIER_DEPLOYMENT,
        "api_version": settings.AZURE_OPENAI_API_VERSION,
        "azure_ad_token_provider": azure_token_provider,
        "azure_ad_async_token_provider": azure_token_provider_async,
        "max_tokens": 25000,
        "max_retries": 2,
        "timeout": 30,
    }

    from pydantic import ValidationError

    try:
        return AzureChatOpenAI(reasoning_effort="high", **kwargs)
    except (TypeError, ValidationError):
        import logging

        logging.getLogger(__name__).warning(
            "AzureChatOpenAI rejected reasoning_effort='high'; creating analytics client without it"
        )
        return AzureChatOpenAI(**kwargs)


def _to_openrouter_slug(model: str) -> str:
    """Map internal model names (claude-sonnet-4-5) to OpenRouter slugs (anthropic/claude-sonnet-4.5)."""
    head, sep, tail = model.rpartition("-")
    if sep and tail.isdigit():
        return f"anthropic/{head}.{tail}"
    return f"anthropic/{model}"


@lru_cache(maxsize=6)
def get_claude_chat_model(
    model: str = "claude-opus-4-6",
    temperature: float = 0.2,
    timeout: int = DEFAULT_CLIENT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_CLIENT_MAX_RETRIES,
):
    """Create (and cache) the Claude chat client.

    When CLAUDE_BASE_URL is set, Claude routes through an OpenAI-compatible
    endpoint (e.g. OpenRouter) using the OpenAI SDK, so we can run Claude
    without a direct Anthropic key. Otherwise uses the native Anthropic SDK.

    Args:
        model: Claude model name (e.g., "claude-opus-4-6", "claude-sonnet-4-5")
        temperature: sampling temperature
        timeout: Per-request timeout in seconds

    Raises:
        ValueError: If CLAUDE_API_KEY is not configured
    """
    if not settings.CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY required for Claude models")

    if settings.CLAUDE_BASE_URL:
        # Route Claude through an OpenAI-compatible proxy (OpenRouter).
        return ChatOpenAI(
            model=_to_openrouter_slug(model),
            api_key=settings.CLAUDE_API_KEY,
            base_url=settings.CLAUDE_BASE_URL,
            temperature=temperature,
            max_retries=max_retries,
            timeout=timeout,
        )

    # Direct Anthropic path (prompt caching enabled)
    return ChatAnthropic(
        model=model,
        api_key=settings.CLAUDE_API_KEY,
        temperature=temperature,
        max_retries=max_retries,
        timeout=timeout,
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


def get_gpt52_analytics_model() -> Union[ChatOpenAI, AzureChatOpenAI]:
    """Get GPT-5.2 reasoning model for analytics tasks.

    Configured with hardcoded high reasoning effort per user decision.
    Used by correlation_node, comparison_node, cross_construct_node in Phases 8-10.
    GPT-5.2 for analytics only — item writer/reviewers stay Claude (existing allocation preserved).

    Returns:
        ChatOpenAI configured with GPT-5.2 and high reasoning effort

    Raises:
        ValueError: If OPENAI_API_KEY not configured
    """
    if settings.AZURE_TEST_OVERRIDE:
        return _get_azure_test_analytics_model()

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY required for GPT-5.2 analytics")

    reasoning_config = {
        "effort": "high",    # Hardcoded per user decision (not configurable)
        "summary": "auto",
    }

    # Note: Using max_tokens instead of max_completion_tokens for compatibility
    # langchain-openai maps max_tokens to the appropriate OpenAI parameter
    return ChatOpenAI(
        model="gpt-5.2",
        api_key=settings.OPENAI_API_KEY,
        reasoning=reasoning_config,
        max_tokens=25000,
        temperature=0.2,
        max_retries=2,
        timeout=30,  # Tight budget for Vercel 300s limit
    )


def get_chat_model_for_agent(
    agent_name: str,
    model_provider: str = "claude",
    use_chatgpt_critics: bool = False,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> Union[ChatOpenAI, AzureChatOpenAI, ChatAnthropic]:
    """Get LLM for specific agent with smart model allocation.

    ``timeout``/``max_retries`` override the agent's defaults, so a caller with
    a hard time budget gets a client whose worst case fits inside it.

    Smart allocation for Claude provider:
    - validator agent: claude-opus-4-6 (highest accuracy for critical validation)
    - all other agents: claude-sonnet-4-5 (cost-effective for drafting/reviewing)

    Agent overrides (when AGENT_MODEL_OVERRIDES_ENABLED):
    - see AGENT_MODEL_OVERRIDES at module top (bias_reviewer, critic, persona
      validator, expert panel, synthetic respondent → gpt-5.4-mini)

    ChatGPT critics toggle (when use_chatgpt_critics=True):
    - All critic agents (validator, linguistic_reviewer, bias_reviewer, content_reviewer, critic)
      use ChatGPT o1-5.2-flex for cost comparison
    - Item writer ALWAYS uses Claude Sonnet (unaffected by toggle)

    Args:
        agent_name: Agent identifier (e.g., "validator", "item_writer", "bias_reviewer")
        model_provider: "claude" or "openai"
        use_chatgpt_critics: Use ChatGPT for critic agents (cost comparison mode)

    Returns:
        Configured chat model instance

    Raises:
        ValueError: If required API key missing for selected provider
    """
    retries = DEFAULT_CLIENT_MAX_RETRIES if max_retries is None else max_retries
    if settings.AZURE_TEST_OVERRIDE:
        azure_model = _azure_test_route(
            agent_name, model_provider, use_chatgpt_critics, timeout, retries
        )
        if azure_model is not None:
            return azure_model

    timeout = timeout or _agent_timeout(agent_name)

    # Define critic agents that can be switched to ChatGPT
    # NOTE: validator excluded — always uses Claude (Sonnet first, Opus on retry)
    # to prevent lazy identical-score evaluations from GPT models
    CRITIC_AGENTS = ["linguistic_reviewer", "bias_reviewer", "content_reviewer", "critic"]

    # Special case: ChatGPT critics toggle
    # When enabled, critic agents use ChatGPT (validator always stays on Claude)
    if use_chatgpt_critics and agent_name in CRITIC_AGENTS:
        return get_openai_chat_model(model=settings.CHATGPT_CRITIC_MODEL, timeout=timeout, max_retries=retries)

    # Ensure item writer ALWAYS uses Claude Sonnet (ignore toggle)
    if agent_name == "item_writer":
        return get_claude_chat_model(model="claude-sonnet-4-5", timeout=timeout, max_retries=retries)

    # Check for agent-specific overrides
    if settings.AGENT_MODEL_OVERRIDES_ENABLED and agent_name in AGENT_MODEL_OVERRIDES:
        override_provider, override_model = AGENT_MODEL_OVERRIDES[agent_name]
        if override_provider == "openai":
            return get_openai_chat_model(model=override_model, timeout=timeout, max_retries=retries)
        elif override_provider == "claude":
            return get_claude_chat_model(model=override_model, timeout=timeout, max_retries=retries)

    # Default allocation based on provider
    if model_provider == "claude":
        if agent_name == "validator":
            return get_claude_chat_model(model="claude-opus-4-6", timeout=timeout, max_retries=retries)
        else:
            # All other agents use Sonnet for cost optimization
            return get_claude_chat_model(model="claude-sonnet-4-5", timeout=timeout, max_retries=retries)
    elif model_provider == "openai":
        return get_openai_chat_model(timeout=timeout, max_retries=retries)
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
