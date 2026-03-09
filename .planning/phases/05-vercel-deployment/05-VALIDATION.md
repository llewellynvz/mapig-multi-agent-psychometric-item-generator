---
phase: 5
slug: vercel-deployment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (backend) + manual deployment verification |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/ -k "not integration" --tb=short` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds (unit tests only, deployment verification is manual) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -k "not integration" --tb=short`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green + manual deployment verification
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | DEP-01 | unit | `pytest tests/test_vercel_entry.py` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DEP-02 | unit | `pytest tests/test_checkpointer.py -k memory` | ✅ | ⬜ pending |
| TBD | TBD | TBD | DEP-03 | unit | `pytest tests/test_checkpointer.py -k memory` | ✅ | ⬜ pending |
| TBD | TBD | TBD | DEP-04 | manual | See Manual-Only Verifications | N/A | ⬜ pending |
| TBD | TBD | TBD | DEP-05 | manual | See Manual-Only Verifications | N/A | ⬜ pending |
| TBD | TBD | TBD | DEP-06 | manual | See Manual-Only Verifications | N/A | ⬜ pending |
| TBD | TBD | TBD | DEP-07 | manual | See Manual-Only Verifications | N/A | ⬜ pending |
| TBD | TBD | TBD | DEP-08 | manual | See Manual-Only Verifications | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_vercel_entry.py` — unit tests for ASGI entry point structure
- [ ] Update existing `tests/test_checkpointer.py` — add MemorySaver swap tests
- [ ] `tests/test_cors_config.py` — verify CORS allows Vercel production domain

*Backend unit tests for local verification; deployment verification is manual.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Production URL accessible | DEP-06 | Requires actual Vercel deployment | Visit production URL, verify 200 response |
| End-to-end generation works | DEP-01, DEP-06 | Requires deployed environment | Submit setup form, run generation, verify results display |
| SSE streaming in production | DEP-07 | Requires deployed serverless environment | Monitor ProgressIndicator during generation, verify real-time updates |
| Environment variables accessible | DEP-05 | Requires Vercel dashboard configuration | Check /health endpoint shows API keys configured (masked) |
| Cold start performance | DEP-08 | Deferred to v2 per user decision | N/A for Phase 5 |
| Frontend deployment | DEP-04 | Requires Vercel deployment | Visit frontend URL, verify page loads |
| Checkpoint behavior in serverless | DEP-03 | Requires deployed environment | Run generation, verify checkpoints work during single run |

*Deployment verification requires actual Vercel environment — cannot be fully automated in CI/CD for v1.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
