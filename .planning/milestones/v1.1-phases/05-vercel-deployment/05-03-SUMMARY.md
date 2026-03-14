---
phase: 05-vercel-deployment
plan: 03
subsystem: deployment
tags:
  - vercel
  - production
  - deployment
  - monorepo
  - single-project
dependency_graph:
  requires:
    - 05-01-PLAN.md (Backend serverless conversion)
    - 05-02-PLAN.md (Frontend production configuration)
  provides:
    - Production deployment at https://lmaig-langgraph.vercel.app/
    - Single Vercel project (monorepo pattern)
    - Environment variables configured
    - End-to-end verified production system
  affects:
    - All production users
    - Deployment workflows
tech_stack:
  added:
    - Vercel single-project deployment
  patterns:
    - Monorepo serverless pattern (Next.js + Python in one project)
    - Same-origin architecture (no CORS needed)
key_files:
  created:
    - (Vercel project configuration via dashboard)
  modified:
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - CLAUDE.md (updated with production URL)
deployment:
  production_url: https://lmaig-langgraph.vercel.app/
  deployment_type: single-project-monorepo
  platform: Vercel
  date: 2026-03-09
---

## What Was Built

Successfully deployed MAPIG to Vercel production using a **single-project monorepo pattern** instead of the originally planned two-project setup.

**Key Achievement**: Simplified architecture with Next.js and Python serverless functions in one Vercel project, accessible at a single domain with no CORS complexity.

## Implementation Details

### Architecture Decision: Single Project vs. Two Projects

**Original Plan**: Deploy as two separate Vercel projects (frontend + backend)

**Actual Implementation**: Deployed as single Vercel project with:
- Next.js at repository root (`/src`, `/public`)
- Python serverless functions in `/api`
- Single domain, same-origin architecture

**Rationale**:
- Vercel natively supports this pattern (documented in CLAUDE.md)
- No CORS configuration needed (same origin)
- Simpler environment variable management
- Single deployment, single domain
- Better developer experience

### Deployment Configuration

**Project Structure**:
```
lmaig-langgraph.vercel.app/
├── / (root)           → Next.js frontend
├── /api/*             → Python FastAPI serverless functions
└── (same domain)      → No CORS issues
```

**Environment Variables** (configured in Vercel dashboard):
- `CLAUDE_API_KEY` — Anthropic API access
- `OPENAI_API_KEY` — OpenAI API access (optional)
- `APP_MODE` — Set to 'claude'
- `NEXT_PUBLIC_API_URL` — Backend API URL (same domain, `/api`)
- `SEARCH_PROVIDER` — Perplexity web search
- `PERPLEXITY_API_KEY` — Perplexity API access

### Verification Status

**Production URL**: https://lmaig-langgraph.vercel.app/

✅ **Backend Health**: `/api/healthz` returns healthy status
✅ **Frontend Load**: Setup form renders correctly
✅ **SSE Streaming**: Real-time agent progress updates work
✅ **Environment Config**: All API keys configured and accessible
✅ **End-to-End Flow**: Item generation completes successfully

### DEP-08 Cold Start Performance

**Status**: Deferred to v2 per user decision

**Baseline**: Not formally measured, but typical Python serverless cold starts (3-8s) accepted for v1 deployment.

**Documentation**: See `.planning/phases/05-vercel-deployment/05-CONTEXT.md` for deferral rationale.

## Changes from Original Plan

### Simplified Deployment Pattern

**Plan 05-03 specified**:
- Create backend Vercel project
- Create frontend Vercel project (Root Directory: `frontend`)
- Configure NEXT_PUBLIC_API_URL to point to backend project

**Actual implementation**:
- Single Vercel project import
- Next.js at root, Python in `/api`
- NEXT_PUBLIC_API_URL points to same domain (`/api`)

**Benefits**:
- ✅ One deployment instead of two
- ✅ No CORS middleware needed
- ✅ Single environment variable configuration
- ✅ Simpler preview deployments

### Files Not Created

The plan specified creating:
- `DEPLOYMENT-GUIDE.md` — Not needed (user completed deployment manually)
- `COLD-START-BASELINE.md` — Not needed (DEP-08 deferred, no formal measurements)

These were documentation artifacts for guided deployment. Since user completed deployment independently with successful results, documentation was unnecessary.

## Requirements Satisfied

✅ **DEP-05**: Vercel backend serverless deployment
✅ **DEP-06**: Vercel frontend deployment
✅ **DEP-07**: Environment variables configured
✅ **DEP-08**: Deferred to v2 (documented in 05-CONTEXT.md)

## Testing & Verification

**Manual Testing**:
- Production URL accessible: https://lmaig-langgraph.vercel.app/
- Health check endpoint verified
- Frontend UI loads correctly
- Item generation workflow tested end-to-end
- No deployment issues reported

**Production Status**: ✅ Live and operational

## Phase 5 Completion

All plans in Phase 5 (Vercel Deployment) are now complete:
- ✅ 05-00: Test scaffolds
- ✅ 05-01: Backend serverless conversion
- ✅ 05-02: Frontend production configuration
- ✅ 05-03: Production deployment (this plan)

**Phase 5 Status**: Complete
**Milestone v1.1**: Phase 5/6 complete

## What's Next

Phase 6: Comprehensive Evaluation Framework
- Automated evaluation suite
- Benchmark construct testing
- Expert comparison to published scales
- Performance metrics validation

---

*Completed: 2026-03-09*
*Production URL: https://lmaig-langgraph.vercel.app/*
*Deployment Pattern: Single-project monorepo (Vercel)*
