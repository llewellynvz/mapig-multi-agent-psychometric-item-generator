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

    # Runtime mode (claude mode uses CLAUDE_API_KEY for all agents)
    APP_MODE: Literal["mock", "azure", "openai", "claude"] = "mock"

    # OpenAI (used only in APP_MODE=openai)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = "gpt-5-nano"
    OPENAI_BASE_URL: Optional[str] = Field(default=None)

    # Hybrid model strategy (cost optimization)
    # Some agents can use cheaper OpenAI models instead of Claude
    AGENT_MODEL_OVERRIDES_ENABLED: bool = True  # Enable per-agent model selection
    OPENAI_CHEAP_MODEL: str = "gpt-4o-mini"  # Cheaper model for peripheral agents (~60% cheaper than Sonnet)

    # Azure OpenAI (used only in APP_MODE=azure)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_VERSION: str = "2023-06-01-preview"

    # Anthropic Claude (used for validation)
    CLAUDE_API_KEY: Optional[str] = Field(default=None)
    VALIDATOR_MODEL: str = "claude-opus-4-6"  # Highest accuracy for validation

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
    # Cost optimization: Max 2 iterations prevents excessive token usage
    # Each iteration ~$0.05-0.08, so 2 iterations provides quality/cost balance
    MAX_ITERATIONS: int = 2
    CRITIC_MAX_SEVERITY_TO_ACCEPT: int = Field(default=2, ge=1, le=5)

    # Persistence (LangGraph checkpointer)
    CHECKPOINT_DB_PATH: str = ".checkpoints.sqlite"

    # Retrieval allowlist
    APPROVED_SOURCES_DIR: str = "data/approved_sources"


settings = Settings()
