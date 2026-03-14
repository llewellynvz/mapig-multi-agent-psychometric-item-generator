---
status: testing
phase: 05-vercel-deployment
source: 05-00-SUMMARY.md, 05-01-SUMMARY.md, 05-02-SUMMARY.md
started: 2026-03-09T15:30:00Z
updated: 2026-03-09T15:30:00Z
---

## Current Test

number: 1
name: Cold Start Smoke Test
expected: |
  Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
result: [pending]

### 2. Backend Health Check Endpoint
expected: Start backend server. Access /healthz endpoint. Returns JSON response {"status":"ok","mode":"claude"} (or "mock"/"openai" depending on APP_MODE). No errors in server logs.
result: [pending]

### 3. Item Generation with Ephemeral Checkpoints
expected: Submit item generation request via API (e.g., 3 items for a construct). Generation completes successfully and returns items with all expected fields. Server logs show MemorySaver checkpointing active during run. No AsyncSqliteSaver errors.
result: [pending]

### 4. Evidence Retrieval from Approved Sources
expected: During item generation, evidence retrieval agent accesses data/approved_sources directory successfully. Generated items include citations from approved sources (e.g., workplace_belonging.md). No file path errors in logs.
result: [pending]

### 5. Frontend Production Build
expected: Run `npm run build` in frontend directory (or root if restructured). Build completes without TypeScript errors, linting errors, or Next.js compilation errors. Output shows standalone mode enabled and build traces collected.
result: [pending]

### 6. Environment Variable Template
expected: Check that .env.production exists in frontend directory (or root) with NEXT_PUBLIC_API_URL template. File includes comments explaining Vercel dashboard configuration. File is tracked in git (not ignored).
result: [pending]

### 7. Vercel Deployment Documentation
expected: README.md contains comprehensive Vercel deployment section with prerequisites, architecture overview, backend setup steps, frontend setup steps, environment variable list, verification steps, known limitations, and troubleshooting guidance.
result: [pending]

## Summary

total: 7
passed: 0
issues: 0
pending: 7
skipped: 0

## Gaps

[none yet]
