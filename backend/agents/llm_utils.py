from __future__ import annotations

import time
import warnings
import json
import logging
import re
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
        # usage_metadata is a TypedDict (plain dict); tolerate attribute form too
        if isinstance(metadata, dict):
            _get = lambda k: metadata.get(k, 0) or 0
        else:
            _get = lambda k: getattr(metadata, k, 0) or 0
        usage.input_tokens = _get("input_tokens")
        usage.output_tokens = _get("output_tokens")
        usage.total_tokens = _get("total_tokens")

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


def truncate_review_comment_fields(data: dict) -> dict:
    """pre_validate hook for reviewer responses: clamp per-comment field
    lengths to the ReviewComment schema caps so an over-long LLM suggestion
    degrades to truncation instead of a validation failure."""
    for comment in data.get("comments", []) or []:
        if isinstance(comment, dict):
            if isinstance(comment.get("issue"), str):
                comment["issue"] = comment["issue"][:210]
            if isinstance(comment.get("suggested_edit"), str):
                comment["suggested_edit"] = comment["suggested_edit"][:300]
    return data


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
    strict: Optional[bool] = True,
    client_timeout: Optional[int] = None,
    client_max_retries: Optional[int] = None,
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
        strict: Sent to the provider as-is: True requests strict structured output
                (default), False sends strict=false, None omits the flag so the
                provider's own default applies.
        client_timeout / client_max_retries: Override the agent's client timeout
                and SDK retries (used by callers with a hard time budget).

    Returns:
        Tuple of (validated response instance, token usage)
    """
    if settings.APP_MODE not in ("openai", "azure", "claude"):
        raise RuntimeError("invoke_structured called in mock mode. Use the mock agents instead.")

    # Use smart allocation if both parameters provided
    if agent_name and model_provider:
        from backend.agents.llm_factory import get_chat_model_for_agent
        llm = get_chat_model_for_agent(
            agent_name, model_provider, use_chatgpt_critics,
            timeout=client_timeout, max_retries=client_max_retries,
        )
    else:
        # Fall back to default get_chat_model()
        from backend.agents.llm_factory import get_chat_model
        llm = get_chat_model()

    # Determine model name for tracking
    model_name = (
        getattr(llm, "model_name", None)
        or getattr(llm, "model", None)
        or getattr(llm, "deployment_name", None)
        or "unknown"
    )

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
    fallback_reason: Optional[Exception] = None
    _t0 = time.perf_counter()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.*")
            structured_kwargs = {"include_raw": True}
            if strict is not None:
                structured_kwargs["strict"] = strict
            try:
                runnable = llm.with_structured_output(schema, **structured_kwargs)
            except TypeError:
                if strict is None:
                    raise
                logger.warning(
                    "STRUCTURED_OUTPUT strict=%s not supported for model=%s, omitting the flag",
                    strict, model_name,
                )
                runnable = llm.with_structured_output(schema, include_raw=True)

            _t0 = time.perf_counter()
            result = runnable.invoke(messages)
            _elapsed = time.perf_counter() - _t0
    except Exception as e:
        if _is_timeout_error(e):
            # The client already retried internally; a second plain call would
            # just double the wall-clock cost of a slow provider.
            _emit_llm_call_log(
                time.perf_counter() - _t0, TokenUsage(model_name=model_name),
                status="fail", error_type=type(e).__name__,
            )
            raise
        fallback_reason = e
    else:
        # with_structured_output(include_raw=True) returns dict with 'parsed' and 'raw'
        if isinstance(result, dict) and "parsed" in result and "raw" in result:
            parsed = result["parsed"]
            raw_message = result["raw"]
            usage = _extract_token_usage(raw_message, model_name)
            if parsed is not None:
                _emit_llm_call_log(_elapsed, usage, status="ok")
                return (parsed, usage)
            # LangChain sets parsed=None when schema validation fails silently.
            # The raw response is already paid for, so recover from it before
            # making a second call.
            recovered = _recover_from_raw(schema, raw_message, pre_validate)
            if recovered is not None:
                logger.warning(
                    "STRUCTURED_OUTPUT_RAW_RECOVERED agent=%s schema=%s parsing_error=%s",
                    agent_name or "unknown", schema.__name__, result.get("parsing_error"),
                )
                _emit_llm_call_log(_elapsed, usage, status="ok_raw")
                return (recovered, usage)
            fallback_reason = result.get("parsing_error") or ValueError(
                "with_structured_output returned parsed=None and raw output was unusable"
            )
        elif result is None:
            fallback_reason = ValueError("with_structured_output returned None")
        else:
            # Fallback: no raw message available
            usage_minimal = TokenUsage(model_name=model_name)
            _emit_llm_call_log(_elapsed, usage_minimal, status="ok_no_raw")
            return (result, usage_minimal)

    # Fallback: no usable structured/raw output — ask again and validate the text as JSON
    e = fallback_reason
    if client_timeout is not None:
        # A budgeted caller sized timeout × retries to fit its time left; a
        # second full call would run outside that budget. Fail instead.
        logger.warning(
            "STRUCTURED_OUTPUT_NO_FALLBACK agent=%s schema=%s (time-budgeted call) error_type=%s",
            agent_name or "unknown", schema.__name__, type(e).__name__,
        )
        if isinstance(e, BaseException):
            raise e
        raise ValueError(f"structured output unusable: {e}")
    logger.warning(
        "STRUCTURED_OUTPUT_FALLBACK agent=%s schema=%s error_type=%s error=%s",
        agent_name or "unknown", schema.__name__, type(e).__name__, e,
        exc_info=e,
    )
    _t0_fb = time.perf_counter()
    ai_msg = llm.invoke(messages)
    _elapsed_fb = time.perf_counter() - _t0_fb
    usage = _extract_token_usage(ai_msg, model_name)
    _emit_llm_call_log(
        _elapsed_fb, usage, status="fallback", error_type=type(e).__name__,
    )

    try:
        return (_validate_payload(schema, _content_text(ai_msg.content), pre_validate), usage)
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


def _is_timeout_error(exc: BaseException) -> bool:
    """True for client/transport timeouts (openai/anthropic APITimeoutError,
    httpx timeouts, builtin TimeoutError), including when wrapped via ``from``."""
    while exc is not None:
        if isinstance(exc, TimeoutError) or any(
            "Timeout" in cls.__name__ for cls in type(exc).__mro__
        ):
            return True
        exc = exc.__cause__
    return False


def _content_text(content) -> str:
    """Flatten a message's content (str or list of content blocks) to text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text") or "")
        return "".join(parts)
    return "" if content is None else str(content)


def strip_code_fence(text: str) -> str:
    """Strip only a leading ```/```json fence and a trailing ``` fence.

    (A blanket replace("json", "") would also corrupt keys like "json_path".)"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    return cleaned


def _validate_payload(
    schema: Type[SchemaT],
    payload,
    pre_validate: Optional[Callable[[dict], dict]],
) -> SchemaT:
    """Validate a JSON string (optionally ```-fenced) or an already-decoded dict."""
    if isinstance(payload, str):
        cleaned = strip_code_fence(payload)
        if not pre_validate:
            return schema.model_validate_json(cleaned)
        payload = json.loads(cleaned)
    data = dict(payload)
    if pre_validate:
        data = pre_validate(data)
    return schema.model_validate(data)


def _recover_from_raw(
    schema: Type[SchemaT],
    raw_message,
    pre_validate: Optional[Callable[[dict], dict]],
) -> Optional[SchemaT]:
    """Try to validate the first response's tool-call args / content blocks /
    text. Returns None when nothing in it validates against the schema."""
    if raw_message is None:
        return None
    candidates: list = []
    for call in getattr(raw_message, "tool_calls", None) or []:
        args = call.get("args") if isinstance(call, dict) else getattr(call, "args", None)
        if isinstance(args, dict) and args:
            candidates.append(args)
    content = getattr(raw_message, "content", None)
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("input"), dict) and block["input"]:
                candidates.append(block["input"])  # Anthropic tool_use block
    text = _content_text(content)
    if text.strip():
        candidates.append(text)

    for payload in candidates:
        try:
            return _validate_payload(schema, payload, pre_validate)
        except Exception as err:
            logger.debug(
                "STRUCTURED_OUTPUT_RAW_UNUSABLE schema=%s error_type=%s",
                schema.__name__, type(err).__name__,
            )
    return None
