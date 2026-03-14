# Technology Stack

**Analysis Date:** 2026-03-08

## Languages

**Primary:**
- Python 3.11+ - Backend logic and LangGraph orchestration
- TypeScript 5.6+ - Frontend and desktop application code
- JavaScript - Electron and build scripts

**Secondary:**
- SQL (SQLite) - Checkpoint storage and state persistence

## Runtime

**Environment:**
- Python 3.11-3.12 (via Poetry)
- Node.js (for frontend and desktop builds)
- Electron 33.3.0 - Desktop application runtime

**Package Manager:**
- Poetry 1.8.0+ - Python dependency management
  - Lockfile: `poetry.lock` (present)
- npm - Node.js/JavaScript dependencies
  - Lockfile: `package-lock.json` (implicit via workspaces)

## Frameworks

**Backend/Core:**
- FastAPI 0.128.0 - REST API and HTTP server
- LangGraph 1.0.6 - Multi-agent orchestration and state management
- LangChain-Core 1.2.8 - LLM abstraction and base utilities
- Pydantic 2.12.5 - Data validation and settings management
- Uvicorn 0.40.0 - ASGI web server

**Frontend:**
- Next.js 14.2.15 - React framework with SSR/SSG
- React 18.3.1 - UI component library
- React Hook Form 7.53.2 - Form state management
- TanStack React Query 5.59.0 - Server state management and caching
- Tailwind CSS 3.4.14 - Utility-first styling
- Radix UI - Unstyled component primitives

**Desktop:**
- Electron 33.3.0 - Cross-platform desktop application
- Electron-Builder 25.1.8 - Application packaging and distribution

**Development & Build:**
- TypeScript - Type checking
- ESLint 8.57.1 - Linting
- PostCSS 8.4.47 - CSS transformation
- Autoprefixer 10.4.20 - CSS vendor prefixing

## Key Dependencies

**Critical:**
- `langgraph` 1.0.6 - Multi-agent graph execution engine with checkpointing
- `langchain-openai` 1.1.7 - OpenAI and Azure OpenAI integrations
- `langgraph-checkpoint-sqlite` 3.0.3 - SQLite-based state persistence for thread resumption
- `pydantic` 2.12.5 - Request/response validation and settings loading
- `fastapi` 0.128.0 - HTTP API framework with automatic OpenAPI documentation

**Infrastructure:**
- `httpx` 0.28.1 - Async HTTP client for Perplexity API calls
- `python-dotenv` 1.2.1 - Environment variable loading from .env
- `pydantic-settings` 2.12.0 - Configuration management from environment

**Testing:**
- `pytest` 9.0.2 - Test framework

**Frontend:**
- `zod` 3.23.8 - TypeScript-first schema validation
- `@hookform/resolvers` 3.9.1 - Form validation resolvers
- `lucide-react` 0.454.0 - Icon library
- `class-variance-authority` 0.7.0 - Component variant management

## Configuration

**Environment:**
- Backend loads from `.env` file via `pydantic-settings`
- Frontend uses `NEXT_PUBLIC_API_URL` for runtime API configuration
- Configuration supports three modes: `mock`, `openai`, `azure`
- See `app/settings.py` for full configuration schema

**Build:**
- `pyproject.toml` - Python project manifest (Poetry)
- `frontend/tsconfig.json` - TypeScript configuration with path alias (`@/*`)
- `frontend/next.config.js` - Next.js configuration (standalone output mode)
- `frontend/tailwind.config.ts` - Tailwind CSS customization
- `frontend/postcss.config.js` - PostCSS plugins
- `desktop/package.json` - Electron app configuration with NSIS installer settings

**Persistence:**
- SQLite checkpoint database at `.checkpoints.sqlite` (configurable via `CHECKPOINT_DB_PATH`)
- Approved sources directory at `data/approved_sources`

## Platform Requirements

**Development:**
- Python 3.11-3.12
- Node.js 18+ (for frontend/desktop development)
- Windows/macOS/Linux for backend
- Windows build tools for Electron (powershell scripts)

**Production:**
- Backend: Any system supporting Python 3.11+
- Frontend: Static Next.js build deployable to any static host or standalone server
- Desktop: Windows x64 (NSIS installer via Electron-Builder)

**Deployment Targets:**
- Backend: Docker-compatible environments or standalone Python execution
- Frontend: Vercel, static hosts, or standalone Next.js server
- Desktop: Windows MSI/NSIS installer distribution

---

*Stack analysis: 2026-03-08*
