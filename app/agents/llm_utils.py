from __future__ import annotations

from typing import List, Tuple, Type, TypeVar

from pydantic import BaseModel

from app.settings import settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)
Message = Tuple[str, str]


def invoke_structured(schema: Type[SchemaT], messages: List[Message]) -> SchemaT:
    """
    Invoke the configured LLM and return validated structured output.

    Works for:
      - APP_MODE=openai
      - APP_MODE=azure

    """
    if settings.APP_MODE not in ("openai", "azure"):
        raise RuntimeError("invoke_structured called in mock mode. Use the mock agents instead.")

    from app.agents.llm_factory import get_chat_model

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
