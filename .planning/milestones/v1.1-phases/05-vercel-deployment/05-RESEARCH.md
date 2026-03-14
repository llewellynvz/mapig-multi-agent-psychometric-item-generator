# Phase 5: Vercel Deployment - Research

**Researched:** 2026-03-09
**Domain:** Vercel serverless deployment, FastAPI ASGI applications, Next.js production hosting
**Confidence:** HIGH

## Summary

Vercel provides native support for deploying FastAPI applications as serverless functions using ASGI without requiring the Mangum adapter (which is AWS Lambda-specific). The deployment pattern is straightforward: Vercel auto-detects FastAPI apps exported from standard entry points (api/index.py, app/main.py, etc.) and wraps them automatically. For MAPIG, this means minimal code changes—primarily switching from AsyncSqliteSaver to MemorySaver for in-memory checkpointing, updating CORS origins to include Vercel domains, and ensuring the approved_sources directory is bundled with the deployment.

The user has decided to accept in-memory-only checkpointing for v1 (session resumption won't survive cold starts), rely on Vercel Pro plan's 300-second timeout (configurable up to 800s with Fluid Compute), and defer cold start optimization below 5 seconds to future work. SSE streaming is fully supported in Vercel serverless functions and works with FastAPI's StreamingResponse.

**Primary recommendation:** Deploy FastAPI backend as a single Vercel Function by exposing the `app` instance from `app/main.py` via an `api/index.py` entry point, replace AsyncSqliteSaver with MemorySaver in the lifespan context, configure NEXT_PUBLIC_API_URL to point to the Vercel function URL, and update CORS to allow production domains.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **In-memory checkpoints only** — No persistence across cold starts; checkpoint logic remains active during single runs but session resumption won't work after function cold start; acceptable v1 trade-off
- **Mangum ASGI adapter** — Wrap existing FastAPI app for Vercel compatibility; minimal code changes with `handler = Mangum(app)` in serverless entry point
- **Keep SSE, rely on Vercel Pro plan** — 60s max execution time (user stated); most generations complete within 20-40s; timeout shows error with retry button
- **Accept longer cold starts for v1** — Typical Python serverless 3-8s; no lazy imports or warming strategies initially; DEP-08 (<5s requirement) deferred to v2
- **Backend:** Vercel Python serverless function at `api/index.py`
- **Frontend:** Next.js static export OR standalone server mode (to be determined during planning)
- **Environment variables:** Configure in Vercel dashboard (CLAUDE_API_KEY, OPENAI_API_KEY, CHECKPOINT_DB_PATH, APP_MODE)
- **Monorepo structure:** Keep current structure; Vercel auto-detects Next.js in `frontend/` directory

### Claude's Discretion
- Whether to use Next.js static export vs standalone server mode for frontend deployment
- Exact Mangum configuration (enable_lifespan, api_gateway_base_path settings)
- How to handle `/data/approved_sources` directory in serverless (bundle with deployment vs S3 vs Vercel Blob)
- Error message copy for timeout scenarios
- Whether to add deployment status page or health check endpoint
- Build configuration optimizations (exclude dev dependencies, optimize bundle size)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEP-01 | Convert FastAPI endpoints to Vercel serverless functions | Vercel native FastAPI support via ASGI; no Mangum needed; expose `app` from entry point |
| DEP-02 | Adapt LangGraph state machine for serverless execution | MemorySaver checkpointer (in-memory) replaces AsyncSqliteSaver; graph.invoke() remains unchanged |
| DEP-03 | Maintain SQLite checkpoint compatibility (local storage) | Change to in-memory MemorySaver; logic preserved but storage ephemeral per user decision |
| DEP-04 | Deploy Next.js frontend to Vercel | Vercel auto-detects Next.js in frontend/; static export or standalone mode both supported |
| DEP-05 | Configure CLAUDE_API_KEY and OPENAI_API_KEY in Vercel environment | Vercel environment variables dashboard; standard pattern for secret management |
| DEP-06 | Production URL accessible and functional | Vercel provides production URL automatically; monorepo requires separate projects or Related Projects feature |
| DEP-07 | SSE streaming works in Vercel serverless environment | FastAPI StreamingResponse fully compatible; Vercel supports streaming with 300s default timeout (Pro plan) |
| DEP-08 | Cold start optimization (<5s first request) | Deferred to v2 per user decision; typical Python cold starts 3-8s; accept this for v1 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vercel Functions | Python 3.12+ | Serverless runtime | Official Python runtime for Vercel; auto-scales; no infrastructure management |
| FastAPI | 0.128.0 (current) | ASGI web framework | Native Vercel support; ASGI auto-detected; preserves all existing routes and middleware |
| MemorySaver | langgraph 1.0.6 | In-memory checkpointer | LangGraph built-in; replaces AsyncSqliteSaver for serverless; ephemeral but functional |
| Next.js | 14.2.15 (current) | Frontend framework | First-class Vercel support; auto-detected in monorepo; zero-config deployment |
| uvicorn | 0.40.0 | ASGI server (dev only) | Development server; not needed in Vercel deployment (Vercel provides runtime) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Mangum | 0.19.0 | ASGI adapter for AWS Lambda | **NOT NEEDED for Vercel**; Vercel natively supports ASGI; Mangum only for AWS deployments |
| Vercel CLI | Latest | Deployment tool | Local testing (`vercel dev`), manual deployments, environment variable management |
| python-dotenv | 1.2.1 | Local env loading | Development only; Vercel uses dashboard environment variables in production |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vercel Functions | AWS Lambda + API Gateway | More configuration required; Mangum adapter needed; manual scaling setup |
| Vercel Functions | Railway/Render/Fly.io | Long-running server deployment; simpler CORS; persistent SQLite possible; less auto-scaling |
| MemorySaver | Vercel Postgres + PostgresSaver | Persistent checkpoints across cold starts; added complexity; $0.30/month minimum; overkill for v1 |
| Monorepo | Separate repositories | Simpler Vercel setup; harder to maintain shared types/schemas |
| Next.js static export | Next.js standalone server | Static export simpler but loses SSR capabilities; standalone more flexible for future features |

**Installation:**
```bash
# Backend (no changes to existing dependencies)
# pyproject.toml already has all needed packages

# Frontend (no changes needed)
cd frontend && npm install

# Vercel CLI (optional, for local testing)
npm install -g vercel
```

## Architecture Patterns

### Recommended Project Structure
```
lmaig-langgraph/
├── api/                    # Vercel serverless entry point
│   └── index.py            # Exports FastAPI app for Vercel
├── app/                    # Existing FastAPI application
│   ├── main.py             # FastAPI app instance (modify lifespan)
│   ├── graph.py            # LangGraph workflow
│   ├── settings.py         # Environment configuration
│   └── agents/             # Agent implementations
├── data/
│   └── approved_sources/   # Bundle with deployment (small size)
├── frontend/               # Next.js application
│   ├── src/
│   ├── public/
│   └── package.json
├── vercel.json             # Vercel configuration
└── pyproject.toml          # Python dependencies
```

### Pattern 1: Vercel FastAPI Entry Point
**What:** Vercel auto-detects FastAPI `app` instances from standard entry points
**When to use:** Always for Vercel deployment; no Mangum needed
**Example:**
```python
# api/index.py - Vercel serverless entry point
# Source: https://vercel.com/docs/frameworks/backend/fastapi
from app.main import app

# Vercel automatically wraps this ASGI app
# No handler function needed - just export 'app'
```

**Critical:** User decision mandates Mangum adapter, but research shows Vercel doesn't need it. This is a conflict—Mangum is AWS-specific and adds unnecessary complexity for Vercel. Recommend updating plan to use native Vercel pattern instead.

### Pattern 2: In-Memory Checkpointing for Serverless
**What:** Replace AsyncSqliteSaver with MemorySaver for ephemeral storage
**When to use:** Serverless environments where filesystem/SQLite persistence isn't practical
**Example:**
```python
# app/main.py - Modify lifespan context
# Source: LangGraph checkpointer docs https://pypi.org/project/langgraph-checkpoint/
from contextlib import asynccontextmanager
from langgraph.checkpoint.memory import MemorySaver

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    # Use in-memory checkpointer for serverless
    checkpointer = MemorySaver()
    app.state.graph = build_graph(checkpointer=checkpointer)
    yield
    # No cleanup needed for MemorySaver

app = FastAPI(lifespan=lifespan)
```

### Pattern 3: CORS for Vercel Production Domains
**What:** Update allow_origins to include Vercel deployment domains
**When to use:** Always for production; localhost for development
**Example:**
```python
# app/main.py - Update CORS middleware
# Source: https://fastapi.tiangolo.com/tutorial/cors/
import os

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",  # Preview deployments
        "https://yourdomain.com",  # Production domain
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # Alternative pattern
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Pattern 4: Next.js Environment Variable Configuration
**What:** Use NEXT_PUBLIC_ prefix for client-side API URLs
**When to use:** Always when Next.js needs to call backend APIs
**Example:**
```bash
# Vercel environment variables dashboard
# Source: https://nextjs.org/docs/pages/guides/environment-variables

# Backend (server-side only)
CLAUDE_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
APP_MODE=claude
CHECKPOINT_DB_PATH=:memory:  # Not used with MemorySaver but keep for compatibility

# Frontend (client-side accessible)
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
```

**Note:** NEXT_PUBLIC_ vars are inlined at build time, not runtime. For dynamic URLs, consider using Next.js API routes as a proxy or server-side rendering.

### Pattern 5: Monorepo with Separate Vercel Projects
**What:** Deploy frontend and backend as separate Vercel projects from same repo
**When to use:** When frontend and backend live in separate directories
**Example:**
```json
// vercel.json for backend (root)
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "echo 'No build needed for Python'",
  "installCommand": "pip install -r requirements.txt || poetry install",
  "functions": {
    "api/**/*.py": {
      "excludeFiles": "{tests/**,__tests__/**,**/*.test.py,**/test_*.py,frontend/**,.planning/**}"
    }
  }
}

// vercel.json for frontend (frontend/)
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "npm run build",
  "outputDirectory": ".next"
}
```

**Alternative:** Use Vercel's "Related Projects" feature to link frontend preview deployments to corresponding backend preview URLs automatically.

### Pattern 6: Static File Bundling in Serverless
**What:** Include data/approved_sources directory in function bundle
**When to use:** When static files are small (<10MB) and read-only
**Example:**
```python
# app/agents/retrieval_agent.py
# Source: https://vercel.com/docs/functions/runtimes/python (relative file reading)
import os
from pathlib import Path

# Use absolute path from project root (cwd is project base in Vercel)
def load_approved_sources():
    sources_dir = Path(os.getcwd()) / "data" / "approved_sources"
    # Or relative to current file
    # sources_dir = Path(__file__).parent.parent.parent / "data" / "approved_sources"

    if not sources_dir.exists():
        raise FileNotFoundError(f"Approved sources not found at {sources_dir}")

    return list(sources_dir.glob("*.md"))
```

**Size check:** Current data/approved_sources is ~3KB (4 markdown files). Well within 500MB Python function limit.

### Anti-Patterns to Avoid
- **Using Mangum with Vercel:** Mangum is AWS-specific; Vercel natively supports ASGI without adapters
- **Hardcoding localhost URLs:** Use environment variables for API URLs; different per environment
- **Using AsyncSqliteSaver in serverless:** SQLite files don't persist across cold starts; use MemorySaver or external DB
- **Wildcard CORS origins (`*`):** Security risk; explicitly list allowed domains
- **Large file bundling:** Don't include >50MB files in function bundle; use Vercel Blob or external storage
- **Build-time secrets in NEXT_PUBLIC_:** Frontend env vars are public in JS bundle; use server-side for secrets

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ASGI → Serverless adapter | Custom request/response mapping | Vercel native ASGI support | Vercel runtime handles ASGI automatically; no adapter needed; reducing dependencies reduces cold start time |
| Session persistence across cold starts | Custom SQLite file sync | MemorySaver (accept ephemeral) or Vercel Postgres | Filesystem isn't persistent in serverless; building sync logic is complex and unreliable |
| API request routing | Custom domain proxy | Vercel Related Projects | Automatically links preview deployments; handles environment-specific URLs |
| Secret management | .env file in deployment | Vercel environment variables dashboard | Secrets in repo = security risk; Vercel encrypts and injects at runtime |
| Static file serving | Custom FastAPI static routes | Vercel CDN (`public/**` directory) | Vercel serves static files via CDN; faster and no function invocation cost |
| Cold start warming | Periodic ping requests | Accept initial latency (v1) or Vercel Fluid Compute | Warming requests cost money; Fluid Compute optimizes automatically; manual warming is fragile |
| Timeout handling | Custom polling fallback | Accept 300s limit + user retry | Adding polling complexity for edge cases isn't worth it for v1; most runs complete in 20-40s |

**Key insight:** Vercel's platform handles infrastructure concerns (scaling, routing, caching, secret management) better than custom code. Trust the platform; focus on application logic.

## Common Pitfalls

### Pitfall 1: Assuming Mangum is Required for Vercel
**What goes wrong:** Developer adds Mangum dependency and wraps FastAPI app unnecessarily
**Why it happens:** Mangum documentation is prominent for "FastAPI serverless" searches; confusion between AWS Lambda and Vercel runtimes
**How to avoid:** Check Vercel-specific documentation first; Vercel has native ASGI support since 2023
**Warning signs:** `from mangum import Mangum` in Vercel deployment code; AWS Lambda environment variables expected

### Pitfall 2: CORS Errors in Production
**What goes wrong:** Frontend deployed to Vercel can't access backend API; browser blocks requests with CORS error
**Why it happens:** allow_origins still hardcoded to localhost; Vercel preview URLs are dynamic (e.g., `project-abc123.vercel.app`)
**How to avoid:** Use allow_origin_regex for Vercel pattern (`r"https://.*\.vercel\.app"`) or environment variable for production domain
**Warning signs:** API works in local dev but fails in Vercel preview/production; console shows "CORS policy: No 'Access-Control-Allow-Origin' header"

### Pitfall 3: Environment Variables Not Available
**What goes wrong:** CLAUDE_API_KEY or OPENAI_API_KEY undefined in deployed function; API calls fail with authentication errors
**Why it happens:** Forgot to add environment variables in Vercel dashboard; or used wrong variable names (Anthropic uses `ANTHROPIC_API_KEY` in some contexts)
**How to avoid:** Verify environment variable names in settings.py match Vercel dashboard; redeploy after adding new variables; test with `vercel dev` locally
**Warning signs:** Error logs show "CLAUDE_API_KEY not configured" despite setting in dashboard; verify exact variable name spelling

### Pitfall 4: Frontend Can't Reach Backend (Monorepo)
**What goes wrong:** Next.js frontend shows connection errors when calling `/v1/generate-items-stream`
**Why it happens:** NEXT_PUBLIC_API_URL points to localhost or wrong Vercel project URL; frontend and backend deployed as separate projects with different domains
**How to avoid:** Use Vercel Related Projects feature to auto-link preview deployments; or manually set NEXT_PUBLIC_API_URL per environment (development, preview, production)
**Warning signs:** Network tab shows 404 or connection refused; API URL still has `localhost:8000`

### Pitfall 5: Function Size Exceeds 500MB Limit
**What goes wrong:** Deployment fails with "Serverless Function has exceeded the unzipped maximum size of 500 MB"
**Why it happens:** All project files bundled into function; frontend/ directory included; .planning/ docs included; test fixtures included
**How to avoid:** Configure excludeFiles in vercel.json to exclude frontend/, tests/, .planning/; use lightweight dependencies; check bundle size with `du -sh` before deploy
**Warning signs:** Slow upload during deployment; deployment fails at "Building Serverless Function" step

### Pitfall 6: SSE Timeout After 60 Seconds
**What goes wrong:** Long-running item generation hits timeout; frontend shows incomplete results
**Why it happens:** User mentioned "60s max execution time" but default Vercel Pro timeout is 300s (5 min); confusion between plans or outdated information
**How to avoid:** Verify actual timeout limit in Vercel dashboard (default 300s for Pro); configure maxDuration in vercel.json if needed; most MAPIG runs complete in 20-40s so unlikely to hit limit
**Warning signs:** Function terminates at exactly 60s or 300s with FUNCTION_INVOCATION_TIMEOUT error; incomplete SSE stream

### Pitfall 7: Checkpoints Lost After Cold Start
**What goes wrong:** User refreshes browser expecting to resume generation; new run starts from scratch
**Why it happens:** MemorySaver stores checkpoints in RAM; serverless function recycles after inactivity; developer expected SQLite-like persistence
**How to avoid:** Document behavior in UI ("Session resumption not available in v1"); accept as known limitation per user decision; consider Vercel Postgres for v2 if critical
**Warning signs:** User confusion reports; expected behavior from local dev doesn't work in production

### Pitfall 8: approved_sources Directory Not Found
**What goes wrong:** Retrieval agent errors with FileNotFoundError; evidence sources can't be loaded
**Why it happens:** Relative path assumptions break in serverless (cwd vs file location); excludeFiles accidentally removes data/
**How to avoid:** Use `os.getcwd()` for project root or `__file__` for relative-to-file paths; verify data/ included in bundle; add logging to show resolved path
**Warning signs:** Error only in production, not local; path shows `/var/task/` instead of expected directory

## Code Examples

Verified patterns from official sources:

### Vercel FastAPI Entry Point
```python
# api/index.py
# Source: https://vercel.com/docs/frameworks/backend/fastapi
from app.main import app

# Vercel automatically detects and wraps the ASGI app
# No additional configuration needed
```

### Modified Lifespan for Serverless
```python
# app/main.py
# Source: https://pypi.org/project/langgraph-checkpoint/ (MemorySaver docs)
from contextlib import asynccontextmanager
from langgraph.checkpoint.memory import MemorySaver
from app.graph import build_graph
from app.logging_setup import configure_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    # Replace AsyncSqliteSaver with MemorySaver for serverless
    # Checkpoints are ephemeral (lost on cold start) but functional during run
    checkpointer = MemorySaver()
    app.state.graph = build_graph(checkpointer=checkpointer)

    yield
    # No cleanup needed for MemorySaver (in-memory only)

app = FastAPI(
    title="MAPIG: Multi-Agent Psychometric Item Generator",
    version="0.1.0",
    lifespan=lifespan,
)
```

### Updated CORS Configuration
```python
# app/main.py
# Source: https://fastapi.tiangolo.com/tutorial/cors/
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # Matches all Vercel preview/prod URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variable Access
```python
# app/settings.py (no changes needed)
# Source: https://vercel.com/docs/environment-variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Vercel injects these from dashboard at runtime
    CLAUDE_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    APP_MODE: Literal["mock", "azure", "openai", "claude"] = "mock"

    model_config = SettingsConfigDict(
        env_file=".env",  # Only used locally; Vercel uses dashboard vars
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

### Vercel Configuration
```json
// vercel.json (root directory)
// Source: https://vercel.com/docs/functions/runtimes/python
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "api/**/*.py": {
      "maxDuration": 300,
      "excludeFiles": "{tests/**,__tests__/**,**/*.test.py,**/test_*.py,frontend/**,.planning/**,.git/**,.venv/**,**/__pycache__/**,**/*.pyc}"
    }
  }
}
```

### Frontend API URL Configuration
```typescript
// frontend/src/lib/api.ts
// Source: https://nextjs.org/docs/pages/guides/environment-variables
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function generateItems(request: UserRequest) {
  const response = await fetch(`${API_BASE_URL}/v1/generate-items-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return response;
}
```

### Reading Static Files in Serverless
```python
# app/agents/retrieval_agent.py
# Source: https://vercel.com/docs/functions/runtimes/python (Reading Relative Files)
import os
from pathlib import Path

def load_approved_sources():
    # Vercel working directory is project root
    sources_dir = Path(os.getcwd()) / "data" / "approved_sources"

    if not sources_dir.exists():
        # Fallback: relative to this file
        sources_dir = Path(__file__).parent.parent.parent / "data" / "approved_sources"

    if not sources_dir.exists():
        raise FileNotFoundError(f"Approved sources directory not found")

    return list(sources_dir.glob("*.md"))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mangum adapter required | Native ASGI support | Vercel Python runtime 2023 | Simpler deployments; one less dependency; faster cold starts |
| Separate Git repos for frontend/backend | Monorepo with Vercel Related Projects | Vercel 2024 | Easier shared types; atomic deployments; preview URL linking |
| Environment variables in .env files | Vercel dashboard encryption | Always (best practice) | Prevents secret leaks; per-environment configuration |
| Manual CORS domain lists | Regex patterns for dynamic domains | FastAPI CORSMiddleware feature | Handles Vercel preview URLs automatically |
| AsyncSqliteSaver in serverless | MemorySaver or external DB | LangGraph best practices | Avoids filesystem persistence issues; explicit tradeoff documentation |
| 60s Vercel timeout (Hobby) | 300s default, 800s configurable (Pro with Fluid Compute) | Vercel Fluid Compute 2025 | Long-running AI workflows feasible without polling fallback |
| Python 3.11 | Python 3.12+ default | Vercel runtime Feb 2026 | Better performance; improved error messages |

**Deprecated/outdated:**
- **Mangum for Vercel deployments**: Was never required; confusion from AWS Lambda tutorials; Vercel has native ASGI since 2023
- **10s Hobby timeout**: Now 300s default even on Hobby plan with Fluid Compute; old docs referenced legacy 10s limit
- **250MB Python function limit**: Increased to 500MB in 2025; still use excludeFiles but more headroom
- **ANTHROPIC_API_KEY vs CLAUDE_API_KEY**: MAPIG uses CLAUDE_API_KEY; Anthropic's official SDK uses ANTHROPIC_API_KEY; either works but consistency matters

## Open Questions

1. **Should we use Next.js static export or standalone server mode?**
   - What we know: Static export simpler; no server-side code; all pages pre-rendered. Standalone mode enables SSR, API routes, middleware.
   - What's unclear: Do we need SSR for any current or planned features? API routes for backend proxy?
   - Recommendation: Use standalone mode—more flexible for future features (SSR for auth, middleware for logging); Vercel optimizes both equally; migration from static to standalone is harder than vice versa.

2. **How should we link frontend and backend preview deployments?**
   - What we know: Separate Vercel projects = different domains; NEXT_PUBLIC_API_URL must match backend URL per environment.
   - What's unclear: Manual environment variable updates or Vercel Related Projects feature?
   - Recommendation: Use Related Projects feature—automatically links preview deployments; reduces manual configuration; documented in official monorepo guide.

3. **Should approved_sources directory stay bundled or move to Vercel Blob?**
   - What we know: Current size ~3KB; Vercel Blob adds complexity; filesystem access works fine in Vercel Functions.
   - What's unclear: Future growth of approved sources; performance tradeoffs.
   - Recommendation: Keep bundled for v1—simple, fast, small size; revisit if directory exceeds 10MB or needs dynamic updates.

4. **Do we need explicit maxDuration configuration or rely on default 300s?**
   - What we know: Default 300s timeout; typical runs 20-40s; user mentioned "60s limit" but Pro plan actually has 300s.
   - What's unclear: Longest possible run time with complex constructs; whether to configure higher limit proactively.
   - Recommendation: Start with default 300s; monitor timeout errors in production; increase to 600s or 800s (Fluid Compute) only if needed.

5. **Should we add a health check endpoint for deployment verification?**
   - What we know: `/healthz` exists; returns app status; useful for monitoring.
   - What's unclear: Whether Vercel needs explicit health checks; impact on cold start frequency.
   - Recommendation: Keep existing `/healthz` endpoint; add to vercel.json as health check path; minimal cost and useful for debugging.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (backend), vitest 4.0.18 (frontend) |
| Config file | pytest.ini (none—see Wave 0), vitest.config.ts (exists) |
| Quick run command | `pytest tests/test_smoke.py -x` (backend), `npm --prefix frontend test` (frontend) |
| Full suite command | `pytest tests/ -v` (backend), `npm --prefix frontend test` (frontend) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEP-01 | FastAPI app exposed via api/index.py | integration | `pytest tests/test_deployment.py::test_vercel_entry_point -x` | ❌ Wave 0 |
| DEP-02 | LangGraph executes with MemorySaver | unit | `pytest tests/test_graph.py::test_memory_checkpointer -x` | ❌ Wave 0 |
| DEP-03 | Checkpoints work during run (ephemeral) | integration | `pytest tests/test_checkpointing.py::test_ephemeral_checkpoint -x` | ❌ Wave 0 |
| DEP-04 | Frontend build succeeds for Vercel | integration | `npm --prefix frontend run build` (not a test but validation step) | ✅ package.json |
| DEP-05 | Environment variables loaded correctly | unit | `pytest tests/test_settings.py::test_env_vars -x` | ❌ Wave 0 |
| DEP-06 | Health check endpoint accessible | smoke | `curl http://localhost:8000/healthz` (manual) | ✅ /healthz exists |
| DEP-07 | SSE streaming returns events | integration | `pytest tests/test_streaming.py::test_sse_stream -x` | ❌ Wave 0 |
| DEP-08 | Cold start performance measurement | manual | Vercel analytics dashboard (not automated in v1) | N/A (deferred) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_smoke.py -x && npm --prefix frontend test` (runs in <30s)
- **Per wave merge:** `pytest tests/ -v && npm --prefix frontend test` (full suite)
- **Phase gate:** Full suite green + manual Vercel preview deployment verification before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_deployment.py` — covers DEP-01 (Vercel entry point exposes app correctly)
- [ ] `tests/test_graph.py::test_memory_checkpointer` — covers DEP-02 (graph works with MemorySaver)
- [ ] `tests/test_checkpointing.py` — covers DEP-03 (ephemeral checkpoints function during run)
- [ ] `tests/test_settings.py` — covers DEP-05 (environment variable loading)
- [ ] `tests/test_streaming.py` — covers DEP-07 (SSE streaming works)
- [ ] `pytest.ini` — pytest configuration file (currently using defaults)
- [ ] Update `tests/test_smoke.py` — to use MemorySaver instead of AsyncSqliteSaver if not already

## Sources

### Primary (HIGH confidence)
- [Vercel FastAPI Documentation](https://vercel.com/docs/frameworks/backend/fastapi) - Official guide for deploying FastAPI on Vercel; confirms native ASGI support without adapters
- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python) - Python version support, dependencies, file handling, bundle size limits
- [Vercel Functions Limitations](https://vercel.com/docs/functions/limitations) - Timeout limits by plan (300s default, 800s max with Fluid Compute), payload size (4.5MB), function size (500MB for Python)
- [FastAPI CORS Tutorial](https://fastapi.tiangolo.com/tutorial/cors/) - Official CORS configuration patterns including regex for dynamic origins
- [Next.js Environment Variables](https://nextjs.org/docs/pages/guides/environment-variables) - NEXT_PUBLIC_ prefix for client-side variables; build-time inlining behavior
- [LangGraph Checkpoint Package](https://pypi.org/project/langgraph-checkpoint/) - MemorySaver documentation; in-memory vs persistent checkpointer tradeoffs

### Secondary (MEDIUM confidence)
- [GitHub: FastAPI Vercel Deployment Examples](https://github.com/hebertcisco/deploy-python-fastapi-in-vercel) - Community example showing zero-config deployment
- [DEV Community: FastAPI on Vercel](https://dev.to/abdadeel/deploying-fastapi-app-on-vercel-serverless-18b1) - Practical deployment walkthrough
- [Vercel Monorepos Guide](https://vercel.com/docs/monorepos) - Monorepo deployment patterns; Related Projects feature
- [Medium: FastAPI Lambda Container](https://rafrasenberg.com/fastapi-lambda/) - Confirms Mangum is AWS-specific, not Vercel
- [How to Enable CORS on Vercel](https://vercel.com/kb/guide/how-to-enable-cors) - CORS configuration for production domains
- [Vercel Environment Variables Guide](https://vercel.com/kb/guide/how-to-add-vercel-environment-variables) - Dashboard configuration for secrets

### Tertiary (LOW confidence)
- WebSearch results for "Vercel serverless timeout limits 2026" - Confirmed 300s default, 800s max with Fluid Compute (cross-verified with official docs)
- WebSearch results for "Python serverless cold start optimization 2026" - SnapStart improvements (AWS-specific); Python 3.12 cold start benchmarks (2.1-3.5s typical)
- WebSearch results for "LangGraph MemorySaver vs AsyncSqliteSaver" - Community recommendations favor MemorySaver for serverless (verified with official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Vercel official documentation confirms native FastAPI/ASGI support; MemorySaver documented in LangGraph package
- Architecture: HIGH - Patterns verified from official Vercel and FastAPI docs; monorepo structure documented in Vercel guides
- Pitfalls: MEDIUM-HIGH - Based on official troubleshooting docs + community experience; CORS and environment variable issues are well-documented

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (30 days - platform features stable; timeout limits confirmed current)

**CRITICAL FINDING:** User decision specifies using Mangum adapter, but research confirms Vercel does NOT need Mangum (which is AWS Lambda-specific). Vercel has native ASGI support. This should be corrected in planning phase to avoid unnecessary complexity and slower cold starts.
