---
phase: 1
slug: llm-as-judge-validation-gate
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml (already configured) |
| **Quick run command** | `pytest tests/ -x --tb=short` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x --tb=short`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | VAL-02,03,04,05,07 | scaffold | `pytest tests/test_validator.py -v --collect-only` | ✅ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | VAL-01,06,07,09 | scaffold | `pytest tests/test_graph.py tests/test_llm_factory.py tests/test_schemas.py -v --collect-only` | ✅ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | VAL-02,04,09 | unit | `pytest tests/test_schemas.py::test_dimension_score_schema tests/test_schemas.py::test_validation_export -x` | ✅ W1 | ⬜ pending |
| 01-02-02 | 02 | 2 | VAL-07 | integration | `python -c "from app.settings import settings; assert hasattr(settings, 'CLAUDE_API_KEY')"` | ✅ | ⬜ pending |
| 01-02-03 | 02 | 2 | VAL-07 | unit | `pytest tests/test_llm_factory.py::test_validator_uses_opus tests/test_llm_factory.py::test_claude_api_key_required -x` | ✅ | ⬜ pending |
| 01-03-01 | 03 | 3 | VAL-03,04 | unit | `test -f app/prompts/validator.md && wc -l app/prompts/validator.md` | ✅ | ⬜ pending |
| 01-03-02 | 03 | 3 | VAL-02,03,05,07 | unit | `pytest tests/test_validator.py -x` | ✅ | ⬜ pending |
| 01-04-01 | 04 | 4 | VAL-01,06 | integration | `pytest tests/test_graph.py::test_validation_placement tests/test_graph.py::test_retry_limit -x` | ✅ | ⬜ pending |
| 01-05-01 | 05 | 5 | VAL-08,09 | integration | `pytest tests/test_api.py::test_validation_in_response -x` | ✅ W0 | ✅ green |
| 01-05-02 | 05 | 5 | VAL-08 | component | `cd frontend && npm run type-check` | ✅ | ✅ green |
| 01-05-03 | 05 | 5 | VAL-08 | integration | `grep -q "validation_node" app/main.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_validator.py` — scaffolds for VAL-02, VAL-03, VAL-04, VAL-05 (Plan 01, Task 1)
- [x] `tests/test_graph.py` — scaffolds for VAL-01, VAL-06 (Plan 01, Task 2)
- [x] `tests/test_llm_factory.py` — scaffolds for VAL-07 (Plan 01, Task 2)
- [x] `tests/test_schemas.py` — scaffolds for VAL-09 (Plan 01, Task 2)
- [x] `tests/test_api.py` — scaffold for VAL-08 (Plan 01, Task 2)

*All Wave 0 scaffolds created in Plan 01.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Validation scores display correctly in UI | VAL-08 | Visual verification of React component rendering | 1. Start backend: `uvicorn app.main:app --reload`<br/>2. Start frontend: `cd frontend && npm run dev`<br/>3. Generate items with mock mode<br/>4. Verify results UI shows validation scores, reasoning (expandable), accept/reject status |
| SSE events show validation progress | VAL-08 | Real-time streaming verification | During generation, observe browser console for SSE events containing "Validating item quality" and "Regenerating low-scoring items" messages |

*Note: Frontend component automated testing with vitest or jest can be added in future phase if desired.*

---

## Validation Audit 2026-03-08

**Audit Type:** Retroactive Nyquist validation via `/gsd:validate-phase`

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 2 |
| Escalated | 0 |

**Gaps Resolved:**

1. **Task 01-05-02** (VAL-08): Added `type-check` script to frontend/package.json
   - **Issue:** VALIDATION.md referenced `npm run type-check` but script didn't exist
   - **Fix:** Added `"type-check": "tsc --noEmit"` to package.json scripts
   - **Status:** ✅ GREEN

2. **Task 01-05-01** (VAL-08, VAL-09): Implemented `test_api.py::test_validation_in_response`
   - **Issue:** Test scaffold existed but was explicitly skipped with reason "Awaiting API validation integration"
   - **Fix:** Implemented schema-based test verifying validation results in API response
   - **Coverage:** All 4 dimension scores, weighted scores, accept/reject status, audit metadata
   - **Status:** ✅ GREEN

**Test Suite Status After Audit:**
- **31/31 tests passing** (100% pass rate, excluding external API smoke test)
- **0 skipped** (all validation-related tests now implemented)
- **All VALIDATION.md commands verified working**

---

## Validation Audit 2026-03-09

**Audit Type:** Retroactive Nyquist validation via `/gsd:validate-phase`

| Metric | Count |
|--------|-------|
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

**Gaps Resolved:**

1. **Task 01-04-01** (VAL-01, VAL-06): Fixed LangGraph Command pattern incompatibility in validation routing
   - **Issue:** `route_after_validation` returned `Command` objects but was called via `add_conditional_edges`, which expects string returns. This caused validation routing to fail with warning: `"Task validation_node wrote to unknown channel branch:to:Command(...), ignoring it"`. Smoke test failed because graph execution stopped after validation_node without creating `final_output`.
   - **Root Cause:** Mixed incompatible LangGraph patterns - Command return type (LangGraph 1.0) with add_conditional_edges (expects strings)
   - **Fix:** Merged routing logic into `validation_node` to return Command directly (LangGraph 1.0 best practice). Removed separate `route_after_validation` function and `add_conditional_edges` call. Updated tests to test validation_node directly.
   - **Files Modified:**
     - `app/graph.py`: Merged routing into validation_node, removed route_after_validation function, removed add_conditional_edges call
     - `tests/test_graph.py`: Updated test_retry_limit to test validation_node instead of route_after_validation
   - **Status:** ✅ GREEN

**Test Suite Status After Audit:**
- **52/52 tests passing** (100% pass rate, 4 skipped unrelated tests)
- **Smoke test now passing** (test_graph_smoke validates end-to-end workflow)
- **No LangGraph routing warnings**
- **All VALIDATION.md commands verified working**

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-08
