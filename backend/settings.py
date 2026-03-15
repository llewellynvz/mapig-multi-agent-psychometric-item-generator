from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field, field_validator
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
    OPENAI_MODEL: str = "gpt-4o"  # Default GPT-4o for general use
    CHATGPT_CRITIC_MODEL: str = "gpt-4o"  # GPT 5.2 (gpt-4o) for critic agents when toggle enabled
    OPENAI_BASE_URL: Optional[str] = Field(default=None)

    # Hybrid model strategy (cost optimization)
    # Some agents can use cheaper OpenAI models instead of Claude
    AGENT_MODEL_OVERRIDES_ENABLED: bool = True  # Enable per-agent model selection
    OPENAI_CHEAP_MODEL: str = "gpt-4o-mini"  # Cheaper model for peripheral agents (~60% cheaper than Sonnet)

    # Smart validation (cost optimization)
    # Use Sonnet for first validation attempt, only Opus if items fail
    SMART_VALIDATION_ENABLED: bool = True  # Tiered Sonnet→Opus validation (~80% cost savings on passing items)

    # Rule-based critic (cost optimization)
    # Use deterministic logic for clear accept/reject decisions (severity <3 → accept, ≥4 → revise)
    # Only invoke LLM for borderline cases (severity = 3)
    RULE_BASED_CRITIC_ENABLED: bool = True  # ~90% critic calls use zero tokens (~2% overall cost savings)

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
    PERPLEXITY_MAX_RESULTS: int = 40
    PERPLEXITY_DOMAIN_FILTER: str = ""
    def perplexity_domains(self) -> list[str]:
        """Return allowlisted domains for Perplexity search."""
        raw = (self.PERPLEXITY_DOMAIN_FILTER or "").strip()
        if not raw:
            return []
        return [d.strip() for d in raw.split(",") if d.strip()]

    # Evidence depth
    EVIDENCE_MIN_CHUNKS: int = 20
    EVIDENCE_MAX_RETRIES: int = 2

    # Orchestrator tuning
    ITEM_COUNT: int = 10
    # Max 3 iterations: rounds 1-2 are strict, round 3 is a rare safety net
    MAX_ITERATIONS: int = 3
    CRITIC_MAX_SEVERITY_TO_ACCEPT: int = Field(default=2, ge=1, le=5)

    # Persistence (LangGraph checkpointer)
    CHECKPOINT_DB_PATH: str = ".checkpoints.sqlite"

    # Retrieval allowlist
    APPROVED_SOURCES_DIR: str = "data/approved_sources"

    # Phase 9: Instrument comparison and plagiarism detection
    PUBLISHER_BLOCKLIST: str = "pearson.com,parinc.com,mhs.com,wpspublish.com,hogrefe.com,proedinc.com,mindgarden.com"
    PLAGIARISM_SIMILARITY_THRESHOLD: float = 0.75

    # Phase 10: GPT-5.2 analytics budget cap
    ANALYTICS_BUDGET_CAP: float = 2.00  # Maximum USD per analytics run (correlation + comparison + cross-construct)

    def publisher_blocklist_domains(self) -> list[str]:
        """Return blocked publisher domains for copyright protection."""
        raw = (self.PUBLISHER_BLOCKLIST or "").strip()
        if not raw:
            return []
        return [d.strip() for d in raw.split(",") if d.strip()]

    @field_validator(
        'APP_MODE',
        'OPENAI_API_KEY',
        'OPENAI_MODEL',
        'CHATGPT_CRITIC_MODEL',
        'OPENAI_BASE_URL',
        'OPENAI_CHEAP_MODEL',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_DEPLOYMENT',
        'AZURE_OPENAI_API_VERSION',
        'CLAUDE_API_KEY',
        'VALIDATOR_MODEL',
        'SEARCH_PROVIDER',
        'PERPLEXITY_API_KEY',
        'PERPLEXITY_BASE_URL',
        'PERPLEXITY_MODEL',
        'PERPLEXITY_SEARCH_MODE',
        'PERPLEXITY_DOMAIN_FILTER',
        'CHECKPOINT_DB_PATH',
        'APPROVED_SOURCES_DIR',
        'PUBLISHER_BLOCKLIST',
        mode='before'
    )
    @classmethod
    def strip_whitespace(cls, v):
        """Strip leading/trailing whitespace from string values.

        This prevents validation errors when environment variables contain
        trailing newlines or spaces (common when copying from UI forms).
        """
        if isinstance(v, str):
            return v.strip()
        return v


settings = Settings()
