from __future__ import annotations

import time
import warnings
import json
import logging
from typing import Callable, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel

from backend.settings import settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)
Message = Tuple[str, str]


class TokenUsage(BaseModel):
    """Token usage information from LLM response."""
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0  # Phase 7: GPT-5.2 reasoning token tracking
    total_tokens: int = 0
    model_name: str = ""


def _extract_token_usage(response_message, model_name: str = "") -> TokenUsage:
    """Extract token usage from LangChain response message.

    Args:
        response_message: LangChain AI message with usage_metadata
        model_name: Model identifier for tracking

    Returns:
        TokenUsage instance with extracted counts
    """
    usage = TokenUsage(model_name=model_name)

    # LangChain standardizes usage in response_metadata.usage_metadata
    if hasattr(response_message, "usage_metadata") and response_message.usage_metadata:
        metadata = response_message.usage_metadata
        usage.input_tokens = getattr(metadata, "input_tokens", 0)
        usage.output_tokens = getattr(metadata, "output_tokens", 0)
        usage.total_tokens = getattr(metadata, "total_tokens", 0)

    # Fallback: check response_metadata directly
    elif hasattr(response_message, "response_metadata"):
        metadata = response_message.response_metadata
        # Claude format
        if "usage" in metadata:
            claude_usage = metadata["usage"]
            usage.input_tokens = claude_usage.get("input_tokens", 0)
            usage.output_tokens = claude_usage.get("output_tokens", 0)
            usage.total_tokens = usage.input_tokens + usage.output_tokens
        # OpenAI format
        elif "token_usage" in metadata:
            openai_usage = metadata["token_usage"]
            usage.input_tokens = openai_usage.get("prompt_tokens", 0)
            usage.output_tokens = openai_usage.get("completion_tokens", 0)
            usage.total_tokens = openai_usage.get("total_tokens", 0)

    return usage


def invoke_structured(
    schema: Type[SchemaT],
    messages: List[Message],
    agent_name: Optional[str] = None,
    model_provider: Optional[str] = None,
    use_cache_control: bool = True,
    use_chatgpt_critics: bool = False,
) -> SchemaT:
    """
    Invoke the configured LLM and return validated structured output.

    Works for:
      - APP_MODE=openai
      - APP_MODE=azure
      - APP_MODE=claude

    Args:
        schema: Pydantic model class for response validation
        messages: List of chat messages
        agent_name: Optional agent identifier for smart allocation
        model_provider: Optional provider override ("claude" or "openai")
        use_cache_control: Enable prompt caching for system messages (default: True)
        use_chatgpt_critics: Use ChatGPT for critic agents (cost comparison mode)

    Returns:
        Validated response instance of schema type
    """
    result, _ = invoke_structured_with_usage(schema, messages, agent_name, model_provider, use_cache_control, use_chatgpt_critics)
    return result


def invoke_structured_with_usage(
    schema: Type[SchemaT],
    messages: List[Message],
    agent_name: Optional[str] = None,
    model_provider: Optional[str] = None,
    use_cache_control: bool = True,
    use_chatgpt_critics: bool = False,
    pre_validate: Optional[Callable[[dict], dict]] = None,
) -> Tuple[SchemaT, TokenUsage]:
    """
    Invoke the configured LLM and return validated structured output WITH token usage.

    Works for:
      - APP_MODE=openai
      - APP_MODE=azure
      - APP_MODE=claude

    Args:
        schema: Pydantic model class for response validation
        messages: List of chat messages
        agent_name: Optional agent identifier for smart allocation
        model_provider: Optional provider override ("claude" or "openai")
        use_cache_control: Enable prompt caching for system messages (default: True)
        use_chatgpt_critics: Use ChatGPT for critic agents (cost comparison mode)
        pre_validate: Optional callable to transform raw JSON dict before Pydantic
                      validation. Used for field-level fixups (e.g. truncating strings).

    Returns:
        Tuple of (validated response instance, token usage)
    """
    if settings.APP_MODE not in ("openai", "azure", "claude"):
        raise RuntimeError("invoke_structured called in mock mode. Use the mock agents instead.")

    # Use smart allocation if both parameters provided
    if agent_name and model_provider:
        from backend.agents.llm_factory import get_chat_model_for_agent
        llm = get_chat_model_for_agent(agent_name, model_provider, use_chatgpt_critics)
    else:
        # Fall back to default get_chat_model()
        from backend.agents.llm_factory import get_chat_model
        llm = get_chat_model()

    # Determine model name for tracking
    model_name = getattr(llm, "model_name", getattr(llm, "model", "unknown"))

    # Convert messages to LangChain format with optional cache_control
    # Only apply cache control for Claude models (Anthropic API)
    is_claude = "claude" in model_name.lower() or settings.APP_MODE == "claude"

    if use_cache_control and is_claude:
        from langchain_core.messages import HumanMessage, SystemMessage

        lc_messages = []
        for role, content in messages:
            if role == "system":
                # Mark system prompts for caching (5-minute TTL per Claude API)
                lc_messages.append(
                    SystemMessage(
                        content=content,
                        additional_kwargs={"cache_control": {"type": "ephemeral"}}
                    )
                )
            elif role == "human":
                lc_messages.append(HumanMessage(content=content))
            else:
                # Other roles: use tuple format
                lc_messages.append((role, content))
        messages = lc_messages

    # Primary path: provider/tool-based structured output
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.*")
            try:
                runnable = llm.with_structured_output(schema, strict=True, include_raw=True)
            except TypeError:
                runnable = llm.with_structured_output(schema, include_raw=True)

            _t0 = time.perf_counter()
            result = runnable.invoke(messages)
            _elapsed = time.perf_counter() - _t0
            logging.getLogger("lmaig").info(
                "LLM_CALL agent=%s model=%s elapsed=%.1fs",
                agent_name or "unknown", model_name, _elapsed,
            )

        # with_structured_output(include_raw=True) returns dict with 'parsed' and 'raw'
        if isinstance(result, dict) and "parsed" in result and "raw" in result:
            parsed = result["parsed"]
            raw_message = result["raw"]
            usage = _extract_token_usage(raw_message, model_name)
            if parsed is None:
                # LangChain sets parsed=None when schema validation fails silently.
                # Fall through to JSON fallback by raising.
                raise ValueError("with_structured_output returned parsed=None")
            return (parsed, usage)
        else:
            # Fallback: no raw message available
            if result is None:
                raise ValueError("with_structured_output returned None")
            return (result, TokenUsage(model_name=model_name))

    except Exception as e:
        # Fallback: validate returned text as JSON
        _logger = logging.getLogger("lmaig")
        _logger.warning(
            "STRUCTURED_OUTPUT_FALLBACK agent=%s schema=%s error=%s",
            agent_name or "unknown", schema.__name__, e,
        )
        _t0_fb = time.perf_counter()
        ai_msg = llm.invoke(messages)
        _elapsed_fb = time.perf_counter() - _t0_fb
        _logger.info(
            "LLM_CALL agent=%s model=%s elapsed=%.1fs (fallback)",
            agent_name or "unknown", model_name, _elapsed_fb,
        )
        usage = _extract_token_usage(ai_msg, model_name)

        text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()

        if pre_validate:
            data = json.loads(cleaned)
            data = pre_validate(data)
            return (schema.model_validate(data), usage)
        return (schema.model_validate_json(cleaned), usage)
