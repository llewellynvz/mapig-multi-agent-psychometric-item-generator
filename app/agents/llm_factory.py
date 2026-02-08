from __future__ import annotations

from functools import lru_cache
from typing import Union

from langchain_openai import AzureChatOpenAI, ChatOpenAI

from app.settings import settings


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


def get_chat_model() -> Union[ChatOpenAI, AzureChatOpenAI]:
    """Return the configured chat model for the current APP_MODE."""
    if settings.APP_MODE == "openai":
        return get_openai_chat_model()
    if settings.APP_MODE == "azure":
        return get_azure_chat_model()
    raise RuntimeError("get_chat_model called in mock mode. Use the mock agents instead.")
