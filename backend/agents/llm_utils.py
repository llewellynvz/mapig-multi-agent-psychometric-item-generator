from __future__ import annotations

import time
import warnings
import json
import logging
from typing import Callable, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel

from backend.settings import settings

logger = logging.getLogger("lmaig")

SchemaT = TypeVar("SchemaT", bound=BaseModel)
Message = Tuple[str, str]


class TokenUsage(BaseModel):
    """Token usage information from LLM response."""
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0  # Phase 7: GPT-5.2 reasoning token tracking
    total_tokens: int = 0
    model_name: str = ""
    cache_creation_input_tokens: int = 0  # Anthropic: tokens written to cache
    cache_read_input_tokens: int = 0  # Anthropic: tokens read from cache (90% discount)


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

    # Extract cache metrics from response_metadata (not in usage_metadata)
    if hasattr(response_message, "response_metadata"):
        resp_meta = response_message.response_metadata
        # Anthropic: cache metrics in usage dict
        if "usage" in resp_meta:
            claude_usage = resp_meta["usage"]
            usage.cache_creation_input_tokens = claude_usage.get("cache_creation_input_tokens", 0) or 0
            usage.cache_read_input_tokens = claude_usage.get("cache_read_input_tokens", 0) or 0
        # OpenAI: cached tokens in prompt_tokens_details
        elif "token_usage" in resp_meta:
            openai_usage = resp_meta["token_usage"]
            details = openai_usage.get("prompt_tokens_details") or {}
            if isinstance(details, dict):
                usage.cache_read_input_tokens = details.get("cached_tokens", 0) or 0
            elif hasattr(details, "cached_tokens"):
                usage.cache_read_input_tokens = getattr(details, "cached_tokens", 0) or 0

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

    # Determine provider for structured logs
    _model_lower = (model_name or "").lower()
    if "claude" in _model_lower or "anthropic" in _model_lower:
        provider = "anthropic"
    elif "gpt" in _model_lower or "openai" in _model_lower or "o1" in _model_lower:
        provider = "openai"
    else:
        provider = "unknown"

    def _emit_llm_call_log(
        elapsed: float,
        usage_obj: TokenUsage,
        status: str,
        error_type: Optional[str] = None,
    ) -> None:
        """Emit one structured LLM_CALL log line with all observability fields."""
        logger.info(
            "LLM_CALL agent=%s provider=%s model=%s elapsed=%.2fs "
            "input_tokens=%d output_tokens=%d cache_read=%d "
            "schema=%s status=%s%s",
            agent_name or "unknown",
            provider,
            model_name,
            elapsed,
            getattr(usage_obj, "input_tokens", 0) or 0,
            getattr(usage_obj, "output_tokens", 0) or 0,
            getattr(usage_obj, "cache_read_input_tokens", 0) or 0,
            schema.__name__,
            status,
            f" error_type={error_type}" if error_type else "",
        )

    # Primary path: provider/tool-based structured output
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.*")
            try:
                runnable = llm.with_structured_output(schema, strict=True, include_raw=True)
            except TypeError:
                logger.warning(
                    "STRUCTURED_OUTPUT strict=True not supported for model=%s, using non-strict",
                    model_name,
                )
                runnable = llm.with_structured_output(schema, include_raw=True)

            _t0 = time.perf_counter()
            result = runnable.invoke(messages)
            _elapsed = time.perf_counter() - _t0

        # with_structured_output(include_raw=True) returns dict with 'parsed' and 'raw'
        if isinstance(result, dict) and "parsed" in result and "raw" in result:
            parsed = result["parsed"]
            raw_message = result["raw"]
            usage = _extract_token_usage(raw_message, model_name)
            if parsed is None:
                # LangChain sets parsed=None when schema validation fails silently.
                # Fall through to JSON fallback by raising.
                raise ValueError("with_structured_output returned parsed=None")
            _emit_llm_call_log(_elapsed, usage, status="ok")
            return (parsed, usage)
        else:
            # Fallback: no raw message available
            if result is None:
                raise ValueError("with_structured_output returned None")
            usage_minimal = TokenUsage(model_name=model_name)
            _emit_llm_call_log(_elapsed, usage_minimal, status="ok_no_raw")
            return (result, usage_minimal)

    except Exception as e:
        # Fallback: validate returned text as JSON
        logger.warning(
            "STRUCTURED_OUTPUT_FALLBACK agent=%s schema=%s error_type=%s error=%s",
            agent_name or "unknown", schema.__name__, type(e).__name__, e,
            exc_info=True,
        )
        _t0_fb = time.perf_counter()
        ai_msg = llm.invoke(messages)
        _elapsed_fb = time.perf_counter() - _t0_fb
        usage = _extract_token_usage(ai_msg, model_name)
        _emit_llm_call_log(
            _elapsed_fb, usage, status="fallback", error_type=type(e).__name__,
        )

        text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()

        try:
            if pre_validate:
                data = json.loads(cleaned)
                data = pre_validate(data)
                return (schema.model_validate(data), usage)
            return (schema.model_validate_json(cleaned), usage)
        except Exception as parse_err:
            logger.error(
                "STRUCTURED_OUTPUT_FALLBACK_PARSE_FAIL agent=%s schema=%s error_type=%s",
                agent_name or "unknown", schema.__name__, type(parse_err).__name__,
                exc_info=True,
            )
            _emit_llm_call_log(
                _elapsed_fb, usage, status="fail", error_type=type(parse_err).__name__,
            )
            raise
