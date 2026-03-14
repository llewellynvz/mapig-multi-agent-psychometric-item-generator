---
phase: 03
slug: claude-api-migration
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-09
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Backend Framework** | pytest 9.0.2 |
| **Frontend Framework** | vitest 4.0.18 + @testing-library/react 16.3.2 |
| **Backend Config** | pyproject.toml |
| **Frontend Config** | frontend/vitest.config.ts |
| **Backend Quick Run** | `pytest tests/test_schemas.py tests/test_llm_factory.py tests/test_graph.py -xvs` |
| **Frontend Quick Run** | `cd frontend && npm run test -- src/components/__tests__` |
| **Full Suite** | `pytest tests/ -xvs && cd frontend && npm run test` |
| **Estimated Runtime** | ~7 seconds (4s backend + 3s frontend) |

---

## Sampling Rate

- **After every task commit:** Run backend quick run for backend tasks, frontend quick run for frontend tasks
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 7 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | API-01 | unit | `pytest tests/test_schemas.py::test_user_request_model_provider_defaults_to_claude -xvs` | ✅ | ✅ green |
| 03-01-01 | 01 | 1 | API-01 | unit | `pytest tests/test_schemas.py::test_user_request_validates_model_provider_enum -xvs` | ✅ | ✅ green |
| 03-01-01 | 01 | 1 | API-01 | unit | `pytest tests/test_schemas.py::test_user_request_accepts_openai_provider -xvs` | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | API-02 | unit | `pytest tests/test_llm_factory.py::test_smart_allocation_validator_uses_opus -xvs` | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | API-02 | unit | `pytest tests/test_llm_factory.py::test_smart_allocation_other_agents_use_sonnet -xvs` | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | API-03 | unit | `pytest tests/test_llm_factory.py::test_openai_provider_returns_openai_model -xvs` | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | API-03 | unit | `pytest tests/test_llm_factory.py::test_missing_claude_key_raises_error -xvs` | ✅ | ✅ green |
| 03-02-01 | 02 | 1 | API-06 | integration | `cd frontend && npm run test -- src/components/__tests__/InstrumentSetupForm.test.tsx` | ✅ | ✅ green |
| 03-02-03 | 02 | 1 | API-07 | integration | `cd frontend && npm run test -- src/components/__tests__/EvidenceAuditPanel.test.tsx` | ✅ | ✅ green |
| 03-03-01 | 03 | 1 | API-04 | integration | `pytest tests/test_graph.py::test_claude_end_to_end_workflow -xvs` | ✅ | ✅ green |
| 03-03-03 | 03 | 1 | API-05 | integration | `pytest tests/test_graph.py::test_missing_claude_key_raises_error -xvs` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Coverage Summary

**Total Requirements:** 7 (API-01 through API-07)
**Automated Tests:** 13 tests across 4 test files
- Backend: 9 tests (7 existing from Plan 03-01, 2 added by gsd-nyquist-auditor)
- Frontend: 11 tests (11 added by gsd-nyquist-auditor)

**Coverage:** 100% (7/7 requirements have automated verification)

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No Wave 0 setup needed.

Test files created by gsd-nyquist-auditor:
- ✅ `frontend/src/components/__tests__/InstrumentSetupForm.test.tsx` — 5 tests for API-06
- ✅ `frontend/src/components/__tests__/EvidenceAuditPanel.test.tsx` — 6 tests for API-07
- ✅ `tests/test_graph.py` (extended) — 2 tests for API-04, API-05

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (N/A - no Wave 0 needed)
- [x] No watch-mode flags
- [x] Feedback latency < 7s ✓
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-09
