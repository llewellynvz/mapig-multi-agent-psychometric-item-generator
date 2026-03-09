# Phase 5: Vercel Deployment - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy MAPIG to Vercel serverless infrastructure with production URL. Convert FastAPI backend to serverless functions using Mangum adapter, maintain SSE streaming within Pro plan limits, use in-memory checkpoints (no cross-invocation persistence), deploy Next.js frontend, and configure environment variables (CLAUDE_API_KEY, OPENAI_API_KEY). Accept longer cold starts for v1 deployment.

</domain>

<decisions>
## Implementation Decisions

### Checkpoint Storage Strategy
- **In-memory only** — No persistence across cold starts
- Checkpoint logic remains active during single generation runs
- Session resumption (browser refresh) will NOT work after function cold start
- Acceptable trade-off for v1: simplifies deployment, avoids new infrastructure (Postgres/KV)
- **CRITICAL:** This changes DEP-03 from "maintain compatibility" to "maintain logic, accept ephemeral storage"
- Future v2: Can migrate to Vercel Postgres with LangGraph Postgres checkpoint adapter if resume needed

### FastAPI Serverless Conversion
- **Mangum ASGI adapter** — Wrap existing FastAPI app for Vercel compatibility
- Minimal code changes: Add Mangum handler in serverless entry point
- Preserves all FastAPI features: routing, middleware, dependency injection, SSE streaming
- Standard pattern for FastAPI serverless (AWS Lambda/Vercel)
- Entry point: Create `api/index.py` with `handler = Mangum(app)` wrapping `app/main.py` FastAPI app

### SSE Streaming with Execution Limits
- **Keep SSE, rely on Vercel Pro plan** — 60s max execution time
- Most generations complete within 60s (typical: 20-40s based on current performance)
- If timeout occurs: Frontend displays error, user can retry
- No polling fallback for v1 — keep implementation simple
- Frontend should show timeout error gracefully with retry button
- **Note:** Vercel Pro required (Hobby plan 10s limit insufficient)

### Cold Start Optimization
- **Accept longer cold starts for v1** — Typical Python serverless: 3-8s
- Do NOT implement lazy imports or warming strategies initially
- Focus on warm function performance (most user requests hit warm functions)
- Document cold start behavior in README for user expectations
- DEP-08 (<5s requirement) deferred to v2 optimization phase

### Deployment Structure
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

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **FastAPI app:** `app/main.py` exports `app` — ready to wrap with Mangum
- **AsyncSqliteSaver:** `app/main.py` lifespan initializes checkpoint database — will need in-memory adapter for serverless
- **SSE streaming:** `/v1/generate-items-stream` already implemented with `StreamingResponse` — compatible with Mangum
- **Environment config:** `app/settings.py` uses pydantic-settings to load from environment — Vercel env vars work seamlessly
- **Next.js frontend:** `frontend/` already has standalone build configuration in `next.config.js`

### Established Patterns
- **Lifespan context:** `app/main.py` uses FastAPI lifespan to initialize graph and checkpointer — may need adjustment for serverless cold starts
- **Thread ID header:** `X-Thread-ID` header pattern for checkpoint persistence — logic preserved but storage ephemeral
- **RUN_STATUS_REGISTRY:** In-memory dict tracking run status — works in serverless (per-function instance)
- **CORS configuration:** Restricts to localhost — needs update to allow Vercel production domain
- **Logging:** Uses file logging to `.mapig/logs/` — serverless needs stdout logging (Vercel captures stdout)

### Integration Points
- **Checkpoint initialization:** `AsyncSqliteSaver(conn=AsyncConnection.create())` in lifespan — replace with in-memory checkpointer
- **API endpoints:** All routes in `app/main.py` preserve current paths — Mangum maintains routing
- **Evidence sources:** `data/approved_sources/` directory accessed by retrieve_evidence — needs to be included in serverless deployment bundle
- **Frontend API URL:** `NEXT_PUBLIC_API_URL` environment variable — update to Vercel serverless function URL
- **CORS origins:** Update `allow_origin_regex` to include Vercel frontend domain pattern

</code_context>

<specifics>
## Specific Ideas

- Mangum entry point should be minimal: just import app and wrap with Mangum(app)
- In-memory checkpoint decision means we can use LangGraph's `MemorySaver` instead of `AsyncSqliteSaver`
- Update README with "Deployment" section showing Vercel-specific setup (environment variables, domain configuration)
- Consider adding a simple `/health` endpoint for Vercel deployment verification
- Vercel Pro plan is a deployment requirement (document in README prerequisites)
- Cold start messaging: Frontend could show "Warming up..." on first request to set expectations
- Timeout error should be actionable: "Generation took longer than expected. Click Retry to try again."

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope (deployment to Vercel).

Future optimizations noted for v2:
- Cold start optimization (<5s via lazy imports, dependency pruning)
- Persistent checkpoint storage (Vercel Postgres if session resume becomes critical)
- Polling fallback for SSE timeouts (if 60s proves insufficient)
- Vercel Edge Functions for lower latency (limited Python support currently)

</deferred>

---

*Phase: 05-vercel-deployment*
*Context gathered: 2026-03-09*
