# Architecture Decision: Single-Project Vercel Deployment

**Date**: 2026-03-09
**Status**: Implemented
**Decision**: Deploy MAPIG as a single Vercel project instead of two separate projects

## Context

Original plans (05-01, 05-02, 05-03) specified deploying MAPIG as **two separate Vercel projects**:
1. Backend project (root = `.`, deploys Python functions from `/api`)
2. Frontend project (root = `frontend`, deploys Next.js from `/frontend` subdirectory)

This approach was based on the assumption that Vercel's monorepo support required separate projects for subdirectory deployments.

## Research Findings

Investigation into Vercel's current capabilities (March 2026) revealed:

1. **Vercel's "monorepo support"** means multiple separate projects from one Git repo, NOT multiple frameworks in a single project
2. **For Next.js in subdirectory + Python `/api`**: Still requires 2 separate Vercel projects
3. **For Next.js at root + Python `/api`**: Works as **1 single project** ✅

**Key Documentation**:
- Vercel docs: "All functions (JS and Python) should be placed into a `/api` folder at the root"
- Native ASGI support for Python serverless functions (no Mangum adapter needed)
- Next.js at root + `/api` functions is officially supported pattern

## Decision

**Restructure repository to enable single-project deployment:**

### Changes Made

**Repository Structure**:
```
Before (planned):                After (implemented):
lmaig-langgraph/                lmaig-langgraph/
├── api/                        ├── api/              # Same
├── app/                        ├── app/              # Same
├── frontend/                   ├── src/              # Moved from frontend/src
│   ├── src/                    ├── public/           # Moved from frontend/public
│   ├── public/                 ├── next.config.js    # Moved from frontend/
│   ├── next.config.js          ├── package.json      # Merged
│   └── package.json            └── ...
└── package.json
```

**Files Modified**:
- `package.json`: Merged root and frontend package.json files
- `.env.production`: Updated to reflect same-origin architecture
- `README.md`: Updated quickstart and deployment sections
- `vercel.json`: Already configured for root deployment
- Created `CLAUDE.md`: Documented architecture decision

**Files Archived**:
- `_archived/frontend-old/`: Old frontend directory preserved

## Benefits

### Single-Project Approach
✅ **Simpler deployment**: One Vercel project instead of two
✅ **Same-origin architecture**: No CORS configuration needed
✅ **Single domain**: `https://mapig.vercel.app` serves both frontend and `/api/*` backend
✅ **Easier env vars**: One set of environment variables
✅ **Better DX**: Preview deployments automatically link frontend to backend
✅ **Cost savings**: One project vs two (matters for team/enterprise plans)

### Trade-offs
⚠️ **Restructuring required**: One-time migration effort (completed)
⚠️ **Different from original plan**: 05-01, 05-02, 05-03 plans reference two-project setup

## Implementation Status

- [x] Move Next.js to root (`src/`, `public/`, configs)
- [x] Merge `package.json` files
- [x] Update `.env.production` for same-origin
- [x] Update `README.md` deployment section
- [x] Create `CLAUDE.md` with architecture documentation
- [x] Archive old `frontend/` directory
- [x] Document decision in this file

## Next Steps (05-03 Execution)

The 05-03-PLAN.md references the old two-project architecture. When executing 05-03:

**Adapt the deployment steps**:
1. ~~Create backend project~~ → Single project import from GitHub
2. ~~Create frontend project~~ → N/A (included in step 1)
3. Configure environment variables once (not twice)
4. Deploy to single URL
5. Verify both frontend and `/api/*` endpoints work

**Environment Variables** (Vercel Dashboard, single project):
```
CLAUDE_API_KEY=<anthropic-key>
OPENAI_API_KEY=<openai-key>
APP_MODE=claude
SEARCH_PROVIDER=perplexity
PERPLEXITY_API_KEY=<perplexity-key>
PERPLEXITY_DOMAIN_FILTER=doi.org,psycnet.apa.org,...
NEXT_PUBLIC_API_URL=https://your-project.vercel.app
```

**Verification**:
- Frontend: `https://your-project.vercel.app/`
- Backend health: `https://your-project.vercel.app/api/healthz`
- Generate endpoint: `https://your-project.vercel.app/api/v1/generate-items-stream`

## References

- [Vercel Monorepo Documentation](https://vercel.com/docs/monorepos)
- [Vercel Python Serverless Functions](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- Original research: `.planning/phases/05-vercel-deployment/05-RESEARCH.md`
- User discussion: Session 2026-03-09 (this session)

---

**Decision Made By**: User (Psynalytics team)
**Implemented By**: Claude Code
**Documented**: 2026-03-09
