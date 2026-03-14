# External Integrations

**Analysis Date:** 2026-03-08

## APIs & External Services

**Large Language Models:**
- OpenAI ChatGPT - Primary LLM for item generation and review
  - SDK/Client: `langchain-openai`
  - Auth: `OPENAI_API_KEY`
  - Endpoint: Configurable via `OPENAI_BASE_URL` (optional)
  - Model: Configured via `OPENAI_MODEL` (default: `gpt-5-nano`)
  - Mode: Activated when `APP_MODE=openai`
  - Implementation: `app/agents/llm_factory.py:get_openai_chat_model()`

- Azure OpenAI - Alternative LLM provider for enterprise deployments
  - SDK/Client: `langchain-openai.AzureChatOpenAI`
  - Auth: `AZURE_OPENAI_API_KEY`
  - Endpoint: `AZURE_OPENAI_ENDPOINT`
  - Deployment: `AZURE_OPENAI_DEPLOYMENT`
  - API Version: `AZURE_OPENAI_API_VERSION` (default: `2023-06-01-preview`)
  - Mode: Activated when `APP_MODE=azure`
  - Implementation: `app/agents/llm_factory.py:get_azure_chat_model()`

**Web Search & Retrieval:**
- Perplexity API - Academic and web search for evidence gathering
  - SDK/Client: `httpx` (custom HTTP client)
  - Auth: `PERPLEXITY_API_KEY`
  - Endpoint: `PERPLEXITY_BASE_URL` (default: `https://api.perplexity.ai/v2`)
  - Model: `PERPLEXITY_MODEL` (default: `sonar-pro`)
  - Search modes: `academic` or `web` (default: `academic`)
  - Max results: `PERPLEXITY_MAX_RESULTS` (default: 25)
  - Domain filtering: `PERPLEXITY_DOMAIN_FILTER` (comma-separated allowlist)
  - Implementation: `app/agents/web_surfer.py:surf()`
  - Requires approved domains via `PERPLEXITY_DOMAIN_FILTER` or request body `approved_domains`
  - Pre-configured domains: apa.org, jstor.org, sciencedirect.com, frontiersin.org, psycnet.apa.org, tandfonline.com, journals.sagepub.com, wiley.com, springer.com

## Data Storage

**Databases:**
- SQLite (local file-based)
  - Location: `.checkpoints.sqlite` (configurable via `CHECKPOINT_DB_PATH`)
  - Client: `langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver`
  - Purpose: Durable thread state checkpointing for LangGraph (enables resuming agent runs)
  - Async support: `aiosqlite` included with `langgraph-checkpoint-sqlite`

**File Storage:**
- Local filesystem only
  - Approved sources directory: `data/approved_sources/` (configurable via `APPROVED_SOURCES_DIR`)
  - Debug logs: User home directory `~/.mapig/logs/debug.log` or custom path via `MAPIG_DEBUG_LOG_PATH` or `MAPIG_DEBUG_DIR`

**Caching:**
- Frontend: React Query (TanStack) - Client-side data caching and synchronization
- Backend: Python LRU cache for LLM client initialization (`llm_factory.py`)
- No distributed caching layer (Redis, Memcached) detected

## Authentication & Identity

**Auth Provider:**
- None (stateless API design)
- Current implementation uses optional thread IDs for session tracking via `X-Thread-ID` header
- All external API authentication via API keys in environment variables (OpenAI, Azure, Perplexity)

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry, Rollbar, or similar)

**Logs:**
- Backend: Python logging configured in `app/logging_setup.py`
- Debug logging: Custom debug log file appended to `~/.mapig/logs/debug.log` (JSON format)
  - Tracks requests, SSE events, hypothesis execution, performance metrics
  - Configurable path via environment: `MAPIG_DEBUG_LOG_PATH` or `MAPIG_DEBUG_DIR`
- Frontend: Console logging only (standard browser DevTools)
- Performance metrics: `app/logging_utils.py:get_performance_summary()` exposed at `GET /v1/performance-summary`

## CI/CD & Deployment

**Hosting:**
- Not configured in codebase
- Supports standalone Python/FastAPI deployment
- Supports Next.js standalone mode (`output: "standalone"`)
- Desktop: Windows NSIS installer via Electron-Builder

**CI Pipeline:**
- Not detected in codebase
- Supports GitHub Actions (no configuration present)

## Environment Configuration

**Required env vars (OpenAI mode):**
- `APP_MODE=openai`
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_MODEL` - Model identifier (default: `gpt-5-nano`)
- `SEARCH_PROVIDER=perplexity` (if using web search)
- `PERPLEXITY_API_KEY` - Perplexity API key
- `PERPLEXITY_DOMAIN_FILTER` - Comma-separated allowlist of approved domains

**Required env vars (Azure mode):**
- `APP_MODE=azure`
- `AZURE_OPENAI_ENDPOINT` - Azure endpoint URL
- `AZURE_OPENAI_API_KEY` - Azure API key
- `AZURE_OPENAI_DEPLOYMENT` - Deployment name
- Same Perplexity vars if using web search

**Optional env vars:**
- `OPENAI_BASE_URL` - Custom OpenAI endpoint (proxy, self-hosted)
- `PERPLEXITY_BASE_URL` - Custom Perplexity endpoint (default: official API)
- `PERPLEXITY_SEARCH_MODE` - `academic` or `web` (default: `academic`)
- `PERPLEXITY_MODEL` - Model identifier (default: `sonar-pro`)
- `PERPLEXITY_MAX_RESULTS` - Max search results (default: 25)
- `LOG_LEVEL` - Logging level (default: INFO)
- `CHECKPOINT_DB_PATH` - Path to SQLite database (default: `.checkpoints.sqlite`)
- `APPROVED_SOURCES_DIR` - Path to approved sources (default: `data/approved_sources`)

**Secrets location:**
- `.env` file (local development, not committed to git)
- Environment variables (production)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected
- Server-Sent Events (SSE) streaming used for real-time progress: `POST /v1/generate-items-stream`

## API Integration Points

**Backend Endpoints:**
- `POST /v1/generate-items` - Generate items (blocking)
- `POST /v1/generate-items-stream` - Generate items with SSE streaming
- `GET /v1/runs/{thread_id}/status` - Check run status
- `GET /v1/performance-summary` - Get performance metrics
- `GET /healthz` - Health check

**Frontend API Client:**
- Location: `frontend/src/lib/api.ts`
- Base URL: `NEXT_PUBLIC_API_URL` environment variable or `http://localhost:8000` (default)
- Runtime configuration: `window.__MAPIG_API_BASE_URL__` global or `apiBaseUrl` query parameter
- Query client: TanStack React Query with default stale time configuration

---

*Integration audit: 2026-03-08*
