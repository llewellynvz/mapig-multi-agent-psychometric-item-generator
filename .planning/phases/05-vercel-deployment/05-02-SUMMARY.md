---
phase: 05-vercel-deployment
plan: 02
subsystem: deployment
tags:
  - vercel
  - next.js
  - standalone-mode
  - production-config
  - documentation
dependency_graph:
  requires:
    - 05-01-PLAN.md (Vercel serverless backend conversion)
  provides:
    - Next.js standalone build configuration
    - Production environment template (.env.production)
    - Comprehensive Vercel deployment documentation
  affects:
    - Frontend deployment process
    - Production build configuration
    - Developer deployment workflows
tech_stack:
  added:
    - Next.js standalone output mode
    - .env.production template
  patterns:
    - Environment-based API URL configuration
    - Vercel-optimized build settings
key_files:
  created:
    - frontend/.env.production (production environment template)
  modified:
    - frontend/next.config.js (added standalone output mode)
    - frontend/.gitignore (allow .env.production to be committed)
    - README.md (comprehensive Vercel deployment documentation)
decisions:
  - decision: Commit .env.production as template file
    rationale: Serves as documentation for required environment variables; actual values set in Vercel dashboard
    outcome: Added gitignore exception for .env.production
  - decision: Use standalone output mode for Next.js
    rationale: Vercel's recommended configuration for optimal serverless performance
    outcome: Added output:'standalone' to next.config.js
  - decision: Replace existing Vercel documentation with comprehensive version
    rationale: Original docs lacked architecture details, troubleshooting, and known limitations
    outcome: Enhanced README with prerequisites, step-by-step deployment, verification, and troubleshooting sections
metrics:
  duration_minutes: 3.02
  tasks_completed: 3
  files_created: 1
  files_modified: 3
  commits: 2
  completed_date: 2026-03-09
---

# Phase 05 Plan 02: Frontend Production Configuration Summary

**One-liner:** Next.js configured for Vercel deployment with standalone mode, production environment template, and comprehensive deployment documentation.

## What Was Built

Configured Next.js frontend for production Vercel deployment with environment-specific API URL handling and optimized build settings.

### Task Breakdown

| Task | Name | Status | Commit | Files |
|------|------|--------|--------|-------|
| 1 | Configure Next.js for Vercel standalone deployment | ✓ Complete | ace53bc | frontend/next.config.js, frontend/.env.production, frontend/.gitignore |
| 2 | Verify frontend build and API client configuration | ✓ Complete | (verification only) | frontend/src/lib/api.ts (no changes needed) |
| 3 | Document Vercel deployment setup in README | ✓ Complete | c4a11cf | README.md |

## Technical Implementation

### 1. Next.js Standalone Configuration

**File:** `frontend/next.config.js`

Added `output: 'standalone'` to Next.js configuration:
- Optimizes for Vercel serverless deployment
- Reduces deployment bundle size
- Improves cold start performance
- Vercel's recommended Next.js configuration

### 2. Production Environment Template

**File:** `frontend/.env.production`

Created production environment template with:
- `NEXT_PUBLIC_API_URL` placeholder for backend Vercel Function URL
- Inline comments explaining Vercel dashboard configuration
- Security warning about NEXT_PUBLIC_ variable exposure to browser
- Template serves as documentation; actual values set in Vercel dashboard per environment

**Gitignore exception:** Modified `frontend/.gitignore` to allow `.env.production` to be committed as template while still blocking `.env.local` and other sensitive env files.

### 3. API Client Verification

**File:** `frontend/src/lib/api.ts`

Verified existing configuration already correct:
- Uses `process.env.NEXT_PUBLIC_API_URL` with fallback to `http://localhost:8000`
- Environment-based URL switching works for development and production
- No changes needed

### 4. Frontend Build Verification

Ran `npm run build` successfully:
- TypeScript compilation passed
- Next.js production build completed without errors
- Static pages generated (6/6)
- Build traces collected for standalone deployment
- Verified `.env.production` loaded during build (shown in build output)

### 5. Comprehensive Deployment Documentation

**File:** `README.md`

Replaced basic Vercel section with comprehensive deployment guide:

**Prerequisites section:**
- Vercel account requirements (free vs Pro)
- Pro plan recommendation for longer timeouts (300s-800s)
- Required API keys

**Architecture section:**
- Backend: Python serverless function at `api/index.py`
- Frontend: Next.js standalone mode
- Checkpointing: In-memory only (MemorySaver)
- SSE Streaming: Supported within 300s timeout
- Typical run times: 20-40s

**Backend Deployment:**
- Step-by-step Vercel project setup
- Framework preset settings (Other)
- Build command configuration
- Environment variable list (CLAUDE_API_KEY, OPENAI_API_KEY, APP_MODE, SEARCH_PROVIDER, PERPLEXITY_API_KEY)
- Backend URL format

**Frontend Deployment:**
- Separate or monorepo project setup
- Framework preset (Next.js)
- Root directory: `frontend`
- Environment variable: NEXT_PUBLIC_API_URL
- Frontend URL format

**Monorepo Linking (Optional):**
- Vercel "Related Projects" feature
- Automatic preview URL linking
- Configuration steps

**Verification:**
- Health check endpoint: `/healthz`
- Expected response: `{"status": "healthy"}`
- Frontend load verification
- End-to-end generation test

**Known Limitations (v1):**
- No session resumption after cold start (in-memory checkpoints)
- Cold start time: 3-8 seconds
- 300s execution timeout (configurable to 800s on Pro)
- Most runs complete in 20-40s

**Troubleshooting:**
- CORS errors: Verify NEXT_PUBLIC_API_URL matches backend domain
- Environment variables not found: Check spelling and redeploy
- Function timeout errors: Review timeout settings, consider vercel.json maxDuration
- Approved sources not found: Verify data/ directory committed and not in .vercelignore

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Issue] .env.production ignored by gitignore**

- **Found during:** Task 1
- **Issue:** `frontend/.gitignore` had `.env.*` rule that blocked `.env.production` from being committed. Plan requires `.env.production` to be committed as a template file for documentation purposes.
- **Fix:** Added `!.env.production` exception to `frontend/.gitignore` after existing `!.env.example` exception. This allows the production template to be committed while still blocking actual environment files like `.env.local`.
- **Files modified:** frontend/.gitignore
- **Commit:** ace53bc (included in Task 1 commit)
- **Rationale:** .env.production serves as documentation (not containing secrets), while .env.local and similar files should remain blocked. This aligns with common practice of committing example/template env files.

## Verification Results

### Automated Checks

All verification checks passed:

- ✓ Next.js standalone mode configured (`grep` check passed)
- ✓ .env.production exists with API URL template (`test -f` and `grep` checks passed)
- ✓ API client uses NEXT_PUBLIC_API_URL environment variable (`grep` check passed)
- ✓ README has comprehensive Vercel deployment documentation (`grep` checks passed)
- ✓ .env.production will be committed (not in gitignore, `git check-ignore` returns empty)

### Build Verification

Frontend production build completed successfully:
```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Generating static pages (6/6)
✓ Finalizing page optimization
✓ Collecting build traces
```

Environment file loaded during build:
```
Environments: .env.production
```

### Manual Verification

All success criteria met:

- ✓ frontend/next.config.js configured with standalone output mode
- ✓ frontend/.env.production created with API URL template and explanatory comments
- ✓ frontend/src/lib/api.ts uses NEXT_PUBLIC_API_URL environment variable (already configured)
- ✓ Frontend builds successfully (`npm run build` completes without errors)
- ✓ README.md contains comprehensive Vercel deployment documentation
- ✓ Deployment section covers prerequisites, architecture, setup, verification, limitations, and troubleshooting

## Key Files

### Created

- **frontend/.env.production**
  - Production environment template
  - Documents NEXT_PUBLIC_API_URL requirement
  - Includes security warnings and configuration instructions
  - Committed to git as template (actual values set in Vercel dashboard)

### Modified

- **frontend/next.config.js**
  - Added `output: 'standalone'` for Vercel optimization
  - Preserves existing `reactStrictMode: true` setting

- **frontend/.gitignore**
  - Added `!.env.production` exception
  - Allows template to be committed while blocking other .env files

- **README.md**
  - Replaced basic Vercel section with comprehensive deployment guide
  - Added architecture overview, step-by-step instructions, verification steps
  - Documented known limitations and troubleshooting guidance
  - 76 insertions, 41 deletions (net +35 lines)

## Decisions Made

### 1. Commit .env.production as Template File

**Context:** Standard practice is to ignore all `.env.*` files to prevent secrets from being committed.

**Decision:** Add gitignore exception to allow `.env.production` to be committed as documentation.

**Rationale:**
- File contains placeholder values, not actual secrets
- Serves as in-repo documentation of required environment variables
- Similar pattern to `.env.example` which is commonly committed
- Actual production values set in Vercel dashboard, not in file
- Reduces deployment friction by documenting exact variable names and format

**Outcome:** Modified `frontend/.gitignore` to add `!.env.production` exception while maintaining blocks on `.env`, `.env.*`, and `.env*.local` files.

### 2. Use Standalone Output Mode

**Context:** Next.js supports multiple build output modes including default server mode and standalone mode.

**Decision:** Configure `output: 'standalone'` in next.config.js.

**Rationale:**
- Vercel's recommended configuration for serverless deployment
- Produces optimized, self-contained build output
- Reduces deployment bundle size by excluding development dependencies
- Improves cold start performance in serverless environment
- Aligns with 05-CONTEXT.md decision to use native Vercel patterns

**Outcome:** Added single line to next.config.js: `output: 'standalone'`

### 3. Replace Existing Vercel Documentation

**Context:** README already had a basic Vercel deployment section (57 lines) with environment variables, deploy commands, verification, error handling, and cost monitoring.

**Decision:** Replace entire section with comprehensive version from plan (92 lines).

**Rationale:**
- Original section lacked architecture overview (backend/frontend split, in-memory checkpoints, SSE streaming)
- Missing detailed project setup steps (framework presets, root directory, build commands)
- No troubleshooting guidance for common issues (CORS, env vars, timeouts, approved sources)
- Didn't document known limitations (session resumption, cold starts)
- Plan version provides step-by-step deployment workflow reducing friction for first-time deployers

**Outcome:** Enhanced README with prerequisites, architecture, separate backend/frontend sections, monorepo linking, verification steps, known limitations, and troubleshooting guide. Net change: +35 lines with improved organization and completeness.

## Dependencies

### Requires

- **05-01-PLAN.md** (Vercel Serverless Conversion)
  - Backend already converted to native Vercel ASGI pattern
  - api/index.py exists and serves FastAPI via ASGI
  - CORS configuration supports Vercel frontend domains

### Provides

- **Next.js standalone build configuration** for Vercel deployment
- **Production environment template** documenting required variables
- **Comprehensive deployment documentation** for backend and frontend

### Affects

- **Frontend deployment process:** Developers now have clear step-by-step Vercel deployment guide
- **Production build configuration:** Standalone mode optimizes for serverless
- **Developer workflows:** .env.production template reduces environment setup friction

## Integration Points

### Frontend → Backend

- `NEXT_PUBLIC_API_URL` environment variable points to backend Vercel Function URL
- Frontend API client (`api.ts`) already configured to use environment-based URLs
- Development: `http://localhost:8000` (fallback)
- Production: Backend Vercel URL (set via Vercel dashboard)

### Build System

- Next.js standalone mode generates optimized serverless output
- Production build verified to succeed without errors
- Environment variables loaded at build time for NEXT_PUBLIC_ prefix

### Documentation

- README now serves as single source of truth for Vercel deployment
- Covers both backend and frontend deployment in one guide
- Troubleshooting section addresses common deployment issues

## Testing Evidence

### Frontend Build Test

Ran `npm run build` in frontend directory:
- ✓ TypeScript compilation succeeded
- ✓ Linting passed
- ✓ Type checking passed
- ✓ 6 static pages generated
- ✓ Build traces collected
- ✓ .env.production loaded (shown in build output)
- ✓ No errors or warnings

Output:
```
▲ Next.js 14.2.15
- Environments: .env.production

Creating an optimized production build ...
✓ Compiled successfully
Linting and checking validity of types ...
Collecting page data ...
Generating static pages (0/6) ...
✓ Generating static pages (6/6)
Finalizing page optimization ...
Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    59 kB           173 kB
├ ○ /_not-found                          873 B            88 kB
├ ○ /api/debug-ping                      0 B                0 B
└ ○ /stepper-story                       1.92 kB        96.5 kB
+ First Load JS shared by all            87.1 kB
ƒ Middleware                             26.7 kB
○  (Static)  prerendered as static content
```

### Configuration Verification

Verified all configuration files:

**next.config.js:**
```javascript
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Optimized for Vercel serverless deployment
};
```

**.env.production template:**
```bash
# Frontend Production Environment Variables
# IMPORTANT: Set these in Vercel dashboard, not in this file (which is committed)

# Backend API URL (Vercel Function URL)
# Format: https://your-project.vercel.app
# For monorepo with separate projects: https://your-backend-project.vercel.app
NEXT_PUBLIC_API_URL=https://your-backend-project.vercel.app

# NOTE: NEXT_PUBLIC_ variables are inlined at build time and exposed to browser
# Do NOT put secrets here - they will be visible in client-side JavaScript bundle
```

**API client (api.ts):**
```typescript
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
```

## Metrics

- **Duration:** 3.02 minutes (181 seconds)
- **Tasks completed:** 3/3
- **Files created:** 1 (frontend/.env.production)
- **Files modified:** 3 (next.config.js, .gitignore, README.md)
- **Commits:** 2
  - ace53bc: feat(05-02): configure Next.js for Vercel standalone deployment
  - c4a11cf: docs(05-02): document Vercel deployment setup in README
- **Auto-fixes:** 1 (gitignore blocking .env.production)

## Next Steps

With frontend now configured for Vercel deployment:

1. **Deploy backend to Vercel** (if not already done in 05-01)
2. **Deploy frontend to Vercel** following README guide
3. **Set NEXT_PUBLIC_API_URL** in Vercel frontend project environment variables
4. **Verify deployment** using health check and end-to-end generation test
5. **Optional:** Configure Vercel "Related Projects" for automatic preview URL linking

## Completion Status

**Plan Status:** ✓ Complete

All tasks executed successfully. Frontend is production-ready for Vercel deployment with optimized build configuration, environment variable template, and comprehensive documentation.

## Self-Check

### File Existence

- ✓ FOUND: frontend/.env.production
- ✓ FOUND: frontend/next.config.js (modified)
- ✓ FOUND: frontend/.gitignore (modified)
- ✓ FOUND: README.md (modified)

### Commit Verification

```bash
git log --oneline --all | grep ace53bc
# ace53bc feat(05-02): configure Next.js for Vercel standalone deployment

git log --oneline --all | grep c4a11cf
# c4a11cf docs(05-02): document Vercel deployment setup in README
```

- ✓ FOUND: ace53bc
- ✓ FOUND: c4a11cf

## Self-Check: PASSED

All files created and modified as documented. All commits exist in git history.
