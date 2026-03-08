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
| 01-05-01 | 05 | 5 | VAL-08,09 | integration | `pytest tests/test_api.py::test_validation_in_response -x` | ✅ W0 | ⬜ pending |
| 01-05-02 | 05 | 5 | VAL-08 | component | `cd frontend && npm run type-check` | ✅ | ⬜ pending |
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

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-08
