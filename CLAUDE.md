# CLAUDE.md - Project Memory for MAPIG

This file provides persistent context for Claude Code across sessions. It documents architectural decisions, project conventions, and important patterns.

## Project Overview

**MAPIG (Multi-Agent Psychometric Item Generator)** is a multi-agent platform for generating psychometrically sound assessment items. It combines LLM orchestration with psychometric principles to create, review, and refine survey items with full auditability.

- **Backend**: FastAPI + LangGraph (Python 3.12+)
- **Frontend**: Next.js 14 (App Router, TypeScript)
- **Deployment**: Vercel (single-project monorepo)

## Critical Architectural Decisions

### 1. Single-Project Vercel Deployment (2026-03-09)

**Decision**: Deploy as a single Vercel project with Next.js at root and Python serverless functions in `/api`.

**Previous Architecture** (before 2026-03-09):
- Frontend in `/frontend` subdirectory
- Planned as 2 separate Vercel projects (frontend + backend)

**Current Architecture** (after 2026-03-09):
- Next.js at repository root (`/src`, `/public`, `next.config.js`, etc.)
- Python serverless functions in `/api` directory
- Single Vercel project, single domain, same-origin architecture

**Rationale**:
- Vercel natively supports this pattern (Next.js at root + Python in `/api`)
- Single domain = no CORS configuration needed
- Simpler deployment (one project vs two)
- Easier environment variable management
- Better DX for preview deployments

**Key Files**:
- `/api/index.py` - Serverless entry point for FastAPI
- `/src/*` - Next.js pages and components
- `/vercel.json` - Vercel configuration (function timeouts, excludes)
- `.env.production` - Production environment template

**Migration Notes**:
- Old `/frontend` directory archived to `/_archived/frontend-old`
- All Next.js dependencies moved to root `package.json`
- Scripts updated: `npm run dev` runs Next.js, `npm run dev:backend` runs FastAPI

### 2. In-Memory Checkpointing for Serverless

**Decision**: Use LangGraph's `MemorySaver` (in-memory checkpointing) instead of `AsyncSqliteSaver`.

**Rationale**:
- Vercel serverless functions are ephemeral
- No persistent file system across invocations
- Session resumption after cold start is not critical for v1
- Avoids complexity of Vercel Postgres integration

**Trade-offs**:
- ✅ Simpler deployment, no database setup
- ✅ Checkpoint logic still works during single generation run
- ❌ Session resumption (browser refresh) won't work after function cold start
- ❌ Deferred to v2: persistent checkpoints with Vercel Postgres

**Implementation**: See `app/main.py` lifespan context.

### 3. Native ASGI Pattern (Not Mangum)

**Decision**: Use Vercel's native ASGI support, not the Mangum adapter.

**Rationale**:
- Research proved Vercel has native ASGI support (since 2023)
- Mangum is AWS Lambda-specific and doesn't work with Vercel
- Native approach is simpler and officially supported

**Implementation**: `api/index.py` directly exports the FastAPI `app` instance.

## Repository Structure

```
lmaig-langgraph/
├── api/                    # Vercel serverless entry point
│   └── index.py           # Exports FastAPI app for Vercel
├── app/                   # FastAPI application code
│   ├── main.py           # FastAPI app, lifespan, routes
│   ├── graph.py          # LangGraph workflow definition
│   ├── agents/           # Agent implementations
│   ├── schemas/          # Pydantic models
│   └── settings.py       # Environment configuration
├── src/                  # Next.js source (App Router)
│   ├── app/             # Next.js pages
│   ├── components/      # React components
│   └── lib/             # Utilities, API client
├── public/              # Static assets
├── data/                # Approved sources for evidence retrieval
├── tests/               # Backend tests
├── .planning/           # GSD workflow tracking
├── next.config.js       # Next.js configuration
├── vercel.json          # Vercel serverless config
├── package.json         # Frontend dependencies + scripts
├── pyproject.toml       # Backend dependencies (Poetry)
└── README.md            # User-facing documentation
```

## Development Workflow

### Local Development
```bash
# Install dependencies
poetry install          # Backend
npm install            # Frontend

# Run both services
npm run dev            # Runs Next.js dev server (port 3000)
npm run dev:backend    # Runs FastAPI with uvicorn (port 8000)

# Alternative: run both together
python run_dev.py      # Starts both backend + frontend
```

### Testing
```bash
npm run build          # Next.js production build
npm run type-check     # TypeScript validation
npm test               # Vitest frontend tests
pytest                 # Backend tests
```

### Deployment
- Push to `main` → Vercel auto-deploys
- PRs → Vercel creates preview deployment
- Environment variables configured in Vercel dashboard

## Code Conventions

### Frontend (TypeScript/Next.js)
- App Router (not Pages Router)
- Server-side fetching where possible
- shadcn/ui component patterns (Radix primitives)
- TanStack Query for API state management
- Zod for validation, React Hook Form for forms

### Backend (Python/FastAPI)
- Pydantic v2 for schemas
- Async/await patterns throughout
- Type hints required (enforced by Pyright)
- LangGraph for agent orchestration
- Structured logging to stdout (for Vercel)

### API Contract
- All endpoints under `/v1/*`
- Request/response validated with Pydantic
- SSE streaming for progress events (`/v1/generate-items-stream`)
- Health check at `/healthz`

## Environment Variables

### Development (.env)
```env
APP_MODE=claude                    # or 'openai' or 'mock'
CLAUDE_API_KEY=...
OPENAI_API_KEY=...
SEARCH_PROVIDER=perplexity
PERPLEXITY_API_KEY=...
PERPLEXITY_DOMAIN_FILTER=doi.org,psycnet.apa.org,...
```

### Production (Vercel Dashboard)
```env
CLAUDE_API_KEY=...                # Required
OPENAI_API_KEY=...                # Optional
APP_MODE=claude                   # Default: mock
SEARCH_PROVIDER=perplexity        # Optional
PERPLEXITY_API_KEY=...           # Optional
NEXT_PUBLIC_API_URL=https://your-project.vercel.app
```

## Known Constraints

### Vercel Function Limits
- **Timeout**: 300s default (Pro plan), 800s max with Fluid Compute
- **Cold start**: 3-8s for Python runtime (typical)
- **Memory**: 1024 MB default, configurable up to 3008 MB

### Typical Generation Times
- Most runs: 20-40s
- Longer runs (50 items, many iterations): 60-120s
- If timeout: Frontend shows error with retry button

### Not Supported in v1
- Session resumption after cold start (requires persistent checkpoints)
- Real-time collaboration (single-user workflow only)
- File uploads (approved sources are deployment-time only)

## GSD Planning Structure

Project uses Get Shit Done (GSD) workflow for structured execution:
- `.planning/` directory contains all planning artifacts
- Phases executed sequentially with atomic commits
- Current milestone: **v1.1 Deployment** (Phases 5-6)
- See `.planning/ROADMAP.md` for full plan

## Common Tasks

### Add a new agent
1. Create agent class in `app/agents/`
2. Define input/output schemas in `app/schemas/`
3. Register in graph: `app/graph.py`
4. Update frontend to handle new agent events (if streaming)

### Update API contract
1. Modify schemas in `app/schemas/`
2. Update frontend types in `src/lib/types.ts`
3. Update API client in `src/lib/api.ts`
4. Regenerate OpenAPI docs: restart backend, visit `/docs`

### Add approved sources
1. Place PDFs/text files in `data/approved_sources/`
2. Files are automatically indexed by retrieval agent
3. Vercel deployment bundles this directory

### Modify constraints
- Baseline constraints: `app/agents/item_writer_agent.py`
- User-provided constraints: merged at runtime (additive, not replacement)

## Troubleshooting

### "Module not found" in Vercel
- Check `.vercelignore` doesn't exclude required files
- Verify `pyproject.toml` dependencies are correct
- Ensure `vercel.json` `excludeFiles` pattern is correct

### CORS errors in production
- Shouldn't happen with single-project setup (same origin)
- If needed, update `allow_origins` in `app/main.py`

### SSE streaming not working
- Vercel supports SSE, but verify Pro plan timeout is sufficient
- Check frontend EventSource implementation in `src/lib/api.ts`
- Ensure `Content-Type: text/event-stream` header is set

### Cold start too slow
- Normal for Python runtime (3-8s)
- Deferred to v2: lazy imports, dependency pruning
- Not a blocker for v1 deployment

## Future Work (v2+)

- **Persistent checkpoints**: Vercel Postgres + PostgresSaver
- **Cold start optimization**: Lazy imports, warming strategies (<5s target)
- **Polling fallback**: If SSE timeout becomes issue
- **Multi-project deployments**: Support multiple instruments concurrently
- **Advanced evaluation**: Comprehensive evaluation framework (Phase 6)

---

**Last Updated**: 2026-03-09
**Maintainer**: Psynalytics team
**GSD Milestone**: v1.1 Deployment (Phase 5 in progress)
