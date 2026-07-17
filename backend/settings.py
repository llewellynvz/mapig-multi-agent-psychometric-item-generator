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
    CHATGPT_CRITIC_MODEL: str = "gpt-5.2"  # GPT-5.2 for critic agents when toggle enabled
    OPENAI_BASE_URL: Optional[str] = Field(default=None)

    # Hybrid model strategy (cost optimization)
    # Some agents can use cheaper OpenAI models instead of Claude
    AGENT_MODEL_OVERRIDES_ENABLED: bool = True  # Enable per-agent model selection

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

    # TEMPORARY: Azure test override (remove after evaluation)
    AZURE_TEST_OVERRIDE: bool = False
    AZURE_TEST_SCOPE: Literal["openai_agents", "all_agents"] = "openai_agents"
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_CERT_PATH: Optional[str] = None
    AZURE_CLIENT_CERT_PASSWORD: Optional[str] = None
    AZURE_FRONTIER_DEPLOYMENT: str = "gpt-5.1"
    AZURE_CHEAP_DEPLOYMENT: str = "gpt-5.4-mini"

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
    EVIDENCE_MAX_RETRIES: int = 3

    # Orchestrator tuning. Stagnation detection typically triggers by
    # iteration 2; 3 iterations fits the Vercel 300s budget.
    MAX_ITERATIONS: int = 3

    # Persistence (LangGraph checkpointer)
    CHECKPOINT_DB_PATH: str = ".checkpoints.sqlite"

    # Retrieval allowlist
    APPROVED_SOURCES_DIR: str = "data/approved_sources"

    # Optional shared key for generation endpoints. Cost-abuse protection,
    # not authentication: when unset (default) every request is accepted.
    MAPIG_API_KEY: Optional[str] = None

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    def cors_origins(self) -> list[str]:
        """Return browser origins allowed to call the API cross-origin."""
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return []
        return [o.strip() for o in raw.split(",") if o.strip()]

    # Phase 9: Instrument comparison and plagiarism detection
    PUBLISHER_BLOCKLIST: str = "pearson.com,parinc.com,mhs.com,wpspublish.com,hogrefe.com,proedinc.com,mindgarden.com"
    PLAGIARISM_SIMILARITY_THRESHOLD: float = 0.75

    # Phase 10: GPT-5.2 analytics budget cap
    ANALYTICS_BUDGET_CAP: float = 2.00  # Maximum USD per analytics run (correlation + comparison + cross-construct)

    # Phase 14: Pseudo-Factor Analysis (Varrasi et al., 2026)
    PFA_ENABLED: bool = True
    # Single embedding model for ALL similarity surfaces (correlation panel,
    # diversity check, convergent validity, PFA) so adjacent statistics are
    # computed in the same embedding space.
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    PFA_EMBEDDING_MODEL: str = "text-embedding-3-large"
    # Multiply requested item_count by this for initial pool. Lowered from 2.0 to 1.3
    # so validation+regen passes don't blow the 300s Vercel budget.
    PFA_OVERGENERATE_FACTOR: float = 1.3
    # Absolute cap on extra items added by over-generation (prevents 20+-item validation slowdowns).
    PFA_OVERGENERATE_MAX_EXTRA: int = 5
    # Skip over-generation entirely when item_count is already this high (e.g., 12+).
    PFA_OVERGENERATE_DISABLE_ABOVE: int = 12
    PFA_TUCKERS_THRESHOLD_FAIR: float = 0.85
    PFA_TUCKERS_THRESHOLD_EXCELLENT: float = 0.95
    PFA_PRUNING_MAX_ITERS: int = 5
    # Time guard for the pruning loop (in seconds) — break if remaining budget below this.
    PFA_PRUNING_MIN_REMAINING_SECS: int = 30
    PFA_RMSR_GOOD: float = 0.05
    PFA_RECOVERY_GOOD: float = 0.80
    PFA_RECOVERY_ACCEPTABLE: float = 0.60

    # Phase 15: Expert Panel
    EXPERT_PANEL_ENABLED: bool = True
    EXPERT_PANEL_DEBATE_ROUNDS: int = 1  # 0 disables debate; 1 = single revision round
    EXPERT_PANEL_IRR_MIN: float = 0.6  # Below this, log warning + surface in UI
    EXPERT_PANEL_DISSENT_SD: float = 1.0  # Item-level dissent flag threshold
    # Reliability follow-up (post-investigation): graceful-degradation thresholds.
    # Below GATE we skip the panel entirely; below DEBATE_MIN we still run round 1
    # but skip the debate; below PARTIAL_MIN we return whatever round-1 evals
    # completed by deadline.
    EXPERT_PANEL_GATE_SECONDS: int = 25
    EXPERT_PANEL_DEBATE_MIN_REMAINING: int = 15
    EXPERT_PANEL_PARTIAL_MIN_REMAINING: int = 8

    # Phase 17: Synthetic-respondent pilot (opt-in; simulated data, item triage only)
    SYNTHETIC_PILOT_ENABLED: bool = False
    SYNTHETIC_N_RESPONDENTS: int = 50
    # Skip the pilot when less than this many seconds remain in the Vercel budget.
    SYNTHETIC_PILOT_MIN_REMAINING_SECS: int = 60

    # Phase 16: Persona Validator
    PERSONA_VALIDATOR_ENABLED: bool = True
    PERSONA_VALIDATOR_PERSONAS: int = 3  # Set 0 to disable
    PERSONA_VALIDATOR_DISAGREEMENT_THRESHOLD: int = 2  # Likert points; SD ≥ this flags item
    # Reliability follow-up: persona descriptors can occasionally exceed the
    # schema cap when LLMs emit prose preamble. The truncation is rare with the
    # new "JSON only, max 400 chars" prompt — but we keep it for robustness.
    PERSONA_LABEL_MAX_CHARS: int = 1500
    PERSONA_LABEL_TRUNCATION_ENABLED: bool = True

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
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_DEPLOYMENT',
        'AZURE_OPENAI_API_VERSION',
        'AZURE_TEST_SCOPE',
        'AZURE_TENANT_ID',
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_CERT_PATH',
        'AZURE_CLIENT_CERT_PASSWORD',
        'AZURE_FRONTIER_DEPLOYMENT',
        'AZURE_CHEAP_DEPLOYMENT',
        'CLAUDE_API_KEY',
        'MAPIG_API_KEY',
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
