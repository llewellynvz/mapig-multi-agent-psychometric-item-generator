# MAPIG Vercel Deployment Guide

**Date:** 2026-03-09
**Phase:** 05-vercel-deployment
**Status:** Ready for deployment

## Overview

This guide walks through deploying MAPIG to Vercel serverless infrastructure with:
- Backend: Python FastAPI serverless function
- Frontend: Next.js standalone application
- Checkpointing: In-memory (ephemeral, no cross-request persistence)
- SSE Streaming: Supported (300s timeout on Pro plan)

## Prerequisites

- [ ] Vercel account (free or Pro plan)
- [ ] Git repository pushed to GitHub/GitLab/Bitbucket
- [ ] Anthropic API key (for Claude models)
- [ ] OpenAI API key (optional, for OpenAI models)
- [ ] Perplexity API key (optional, for web search)

**Recommended:** Vercel Pro plan for 300s execution timeout (Hobby plan has 60s limit which may be insufficient)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Vercel Platform                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (Next.js)              Backend (FastAPI)           │
│  ┌──────────────────┐            ┌──────────────────┐        │
│  │ UI Components    │────────────>│ api/index.py     │        │
│  │ - Setup Form     │ HTTPS/SSE  │ - ASGI app       │        │
│  │ - Progress UI    │<───────────│ - LangGraph      │        │
│  │ - Results Table  │            │ - Agents         │        │
│  └──────────────────┘            └──────────────────┘        │
│                                                               │
│  Environment:                    Environment:                │
│  NEXT_PUBLIC_API_URL             CLAUDE_API_KEY              │
│                                  OPENAI_API_KEY              │
│                                  APP_MODE                    │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### Step 1: Deploy Backend

1. **Log in to Vercel Dashboard**: https://vercel.com/dashboard

2. **Create New Project**:
   - Click "Add New..." → "Project"
   - Select your Git provider (GitHub/GitLab/Bitbucket)
   - Import MAPIG repository

3. **Configure Backend Project**:
   - **Project Name**: `mapig-backend` (or your preference)
   - **Framework Preset**: Other
   - **Root Directory**: Leave as `.` (monorepo root)
   - **Build Command**: Leave empty or `echo 'No build needed'`
   - **Output Directory**: Leave empty
   - **Install Command**: `pip install -r requirements.txt` or `poetry install` (Vercel auto-detects)

4. **Configure Environment Variables** (Backend Project → Settings → Environment Variables):

   Required:
   - `CLAUDE_API_KEY`: Your Anthropic API key
   - `APP_MODE`: `claude` (or `openai` if using OpenAI)

   Optional:
   - `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI models)
   - `SEARCH_PROVIDER`: `perplexity` (for web search)
   - `PERPLEXITY_API_KEY`: Your Perplexity API key
   - `PERPLEXITY_DOMAIN_FILTER`: Comma-separated domains (e.g., `apa.org,jstor.org`)

   All environments: Production, Preview, Development

5. **Deploy Backend**:
   - Click "Deploy"
   - Wait for deployment to complete (typically 1-3 minutes)
   - Note the production URL (e.g., `https://mapig-backend.vercel.app`)

6. **Verify Backend Deployment**:
   ```bash
   curl https://mapig-backend.vercel.app/healthz
   ```
   Expected response: `{"status": "healthy"}`

### Step 2: Deploy Frontend

1. **Create New Project** (separate from backend):
   - Click "Add New..." → "Project"
   - Import same repository (or use monorepo detection)

2. **Configure Frontend Project**:
   - **Project Name**: `mapig-frontend` (or your preference)
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `.next` (auto-detected)
   - **Install Command**: `npm install` (auto-detected)

3. **Configure Environment Variables** (Frontend Project → Settings → Environment Variables):

   Required:
   - `NEXT_PUBLIC_API_URL`: Backend production URL from Step 1.6 (e.g., `https://mapig-backend.vercel.app`)

   All environments: Production, Preview, Development

4. **Deploy Frontend**:
   - Click "Deploy"
   - Wait for deployment to complete (typically 2-4 minutes)
   - Note the production URL (e.g., `https://mapig-frontend.vercel.app`)

5. **Verify Frontend Deployment**:
   - Visit frontend URL in browser
   - Setup form should load
   - No CORS errors in console

### Step 3: End-to-End Verification

1. **Test Health Check**:
   ```bash
   curl https://mapig-backend.vercel.app/healthz
   ```
   Expected: `{"status": "healthy"}`

2. **Test Frontend Load**:
   - Visit `https://mapig-frontend.vercel.app`
   - Verify setup form renders
   - Open browser DevTools Console
   - No CORS errors should appear

3. **Test Item Generation** (manual - requires valid API keys):
   - Fill out setup form:
     - Construct name: "Conscientiousness"
     - Definition: "The tendency to be organized, responsible, and hardworking"
     - Model provider: Claude (or OpenAI if configured)
     - Item count: 5
   - Click "Generate Items"
   - Verify:
     - Progress indicator shows agent steps
     - SSE events stream in real-time
     - Generation completes within 60s
     - Results table displays items
     - No timeout errors

4. **Verify SSE Streaming**:
   - During generation, open Network tab
   - Find `/v1/generate-items-stream` request
   - Verify EventStream content-type
   - Events should stream incrementally (not all at once)

5. **Test Export Functionality**:
   - After generation completes
   - Click "Download" button
   - Select format (CSV/JSON/Markdown)
   - Verify file downloads with correct content

## Verification Checklist

- [ ] Backend deployed to Vercel
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured (CLAUDE_API_KEY, NEXT_PUBLIC_API_URL)
- [ ] /healthz endpoint returns healthy
- [ ] Frontend loads without errors
- [ ] Setup form renders correctly
- [ ] Item generation completes successfully
- [ ] SSE streaming works (progress updates visible)
- [ ] Results display with validation scores
- [ ] Export downloads work (all formats)
- [ ] No CORS errors in browser console
- [ ] No timeout errors (<300s execution time)

## Troubleshooting

### Backend Issues

**Problem**: 500 error on /healthz
- **Cause**: Environment variables missing or app failed to initialize
- **Fix**: Check Vercel logs (Backend Project → Deployments → Latest → View Function Logs)
- **Verify**: Environment variables are set correctly (exact spelling)

**Problem**: "Module not found" errors in logs
- **Cause**: Dependencies not installed
- **Fix**: Verify pyproject.toml or requirements.txt is in repository root
- **Verify**: Vercel build logs show "Installing dependencies"

**Problem**: "Approved sources directory not found"
- **Cause**: data/approved_sources not in repository or excluded by .vercelignore
- **Fix**: Verify data/ directory is committed and not in .vercelignore

### Frontend Issues

**Problem**: CORS error when calling backend
- **Cause**: NEXT_PUBLIC_API_URL incorrect or CORS not configured
- **Fix**: Verify NEXT_PUBLIC_API_URL matches backend URL exactly (no trailing slash)
- **Verify**: Backend CORS middleware allows *.vercel.app pattern

**Problem**: "Failed to fetch" errors
- **Cause**: Backend URL incorrect or backend not deployed
- **Fix**: Check NEXT_PUBLIC_API_URL in Vercel dashboard
- **Verify**: Backend /healthz endpoint accessible

**Problem**: Blank page or build errors
- **Cause**: Frontend build failed
- **Fix**: Check Vercel build logs (Frontend Project → Deployments → Latest → View Build Logs)
- **Verify**: npm run build succeeds locally

### Generation Issues

**Problem**: Timeout after 60s
- **Cause**: Function timeout too low (Hobby plan default)
- **Fix**: Upgrade to Pro plan or reduce ITEM_COUNT
- **Verify**: Check Vercel plan limits (Settings → Usage)

**Problem**: "API key not configured" error
- **Cause**: CLAUDE_API_KEY or OPENAI_API_KEY missing in backend environment
- **Fix**: Add environment variable in Vercel dashboard, redeploy
- **Verify**: Variable appears in Settings → Environment Variables

**Problem**: Generation starts but doesn't complete
- **Cause**: SSE connection dropped or function timeout
- **Fix**: Check Vercel function logs for errors
- **Verify**: Request completes within timeout limit

## Known Limitations (v1)

1. **Session Resumption**: Not available after cold start
   - Checkpoints stored in-memory only
   - Browser refresh loses in-progress generation
   - Acceptable trade-off for v1 (avoids external database)

2. **Cold Start Latency**: 3-8 seconds on first request
   - Python serverless cold start
   - Subsequent requests are fast (warm function)
   - See COLD-START-BASELINE.md for measurements
   - Optimization deferred to v2 (DEP-08)

3. **Execution Timeout**: 300s maximum (Pro plan)
   - Most runs complete in 20-40s
   - Complex constructs may take longer
   - Can configure up to 800s with Fluid Compute if needed

## Post-Deployment

### Custom Domain (Optional)

1. Backend Project → Settings → Domains
2. Add custom domain (e.g., `api.mapig.com`)
3. Follow DNS configuration instructions
4. Update frontend NEXT_PUBLIC_API_URL to custom domain

### Monitoring

- Vercel Analytics: Automatically enabled (page views, performance)
- Function Logs: Available in Deployments → View Function Logs
- Error Tracking: Check logs for exceptions

### Next Steps

After successful deployment:
- [ ] Update STATE.md with production URL
- [ ] Share production URL with stakeholders
- [ ] Monitor Vercel usage and function execution times
- [ ] Consider Phase 6: Comprehensive Evaluation Framework

## Support

- Vercel Documentation: https://vercel.com/docs
- MAPIG Issues: https://github.com/your-repo/issues
- Vercel Support: support@vercel.com (Pro plan only)

---

*Deployment guide created: 2026-03-09*
*Phase: 05-vercel-deployment*
