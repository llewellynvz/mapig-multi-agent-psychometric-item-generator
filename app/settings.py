from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

STANDARD_ITEM_CONSTRAINTS = [
    "No double-barrelled items",
    "Avoid idioms",
    "Minimize reading level",
    "Positively keyed only",
]


class Settings(BaseSettings):
    """App configuration loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime mode
    APP_MODE: Literal["mock", "azure", "openai"] = "mock"

    # OpenAI (used only in APP_MODE=openai)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = "gpt-5-nano"
    OPENAI_BASE_URL: Optional[str] = Field(default=None)

    # Azure OpenAI (used only in APP_MODE=azure)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_VERSION: str = "2023-06-01-preview"

    # Web search (optional)
    SEARCH_PROVIDER: str = "perplexity"  # local | perplexity | hybrid
    PERPLEXITY_API_KEY: Optional[str] = None
    PERPLEXITY_BASE_URL: str = "https://api.perplexity.ai/v2"
    PERPLEXITY_MODEL: str = "sonar-pro"
    PERPLEXITY_SEARCH_MODE: str = "academic"  # academic | web
    PERPLEXITY_MAX_RESULTS: int = 25
    PERPLEXITY_DOMAIN_FILTER: str = ""
    def perplexity_domains(self) -> list[str]:
        """Return allowlisted domains for Perplexity search."""
        raw = (self.PERPLEXITY_DOMAIN_FILTER or "").strip()
        if not raw:
            return []
        return [d.strip() for d in raw.split(",") if d.strip()]

    # Orchestrator tuning
    ITEM_COUNT: int = 10
    MAX_ITERATIONS: int = 2
    CRITIC_MAX_SEVERITY_TO_ACCEPT: int = Field(default=2, ge=1, le=5)

    # Persistence (LangGraph checkpointer)
    CHECKPOINT_DB_PATH: str = ".checkpoints.sqlite"

    # Retrieval allowlist
    APPROVED_SOURCES_DIR: str = "data/approved_sources"


settings = Settings()
