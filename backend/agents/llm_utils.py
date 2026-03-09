from __future__ import annotations

from typing import List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel

from backend.settings import settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)
Message = Tuple[str, str]


def invoke_structured(
    schema: Type[SchemaT],
    messages: List[Message],
    agent_name: Optional[str] = None,
    model_provider: Optional[str] = None,
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

    Returns:
        Validated response instance of schema type
    """
    if settings.APP_MODE not in ("openai", "azure", "claude"):
        raise RuntimeError("invoke_structured called in mock mode. Use the mock agents instead.")

    # Use smart allocation if both parameters provided
    if agent_name and model_provider:
        from backend.agents.llm_factory import get_chat_model_for_agent
        llm = get_chat_model_for_agent(agent_name, model_provider)
    else:
        # Fall back to default get_chat_model()
        from backend.agents.llm_factory import get_chat_model
        llm = get_chat_model()

    # Primary path: provider/tool-based structured output
    try:
        try:
            runnable = llm.with_structured_output(schema, strict=True)
        except TypeError:
            runnable = llm.with_structured_output(schema)
        return runnable.invoke(messages)
    except Exception:
        # Fallback: validate returned text as JSON
        ai_msg = llm.invoke(messages)
        text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()

        return schema.model_validate_json(cleaned)
