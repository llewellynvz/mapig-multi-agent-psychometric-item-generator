---
phase: 06
slug: comprehensive-evaluation-framework
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-09
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml (lines 49-50) |
| **Quick run command** | `pytest tests/test_eval_suite.py -x` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds (quick), ~60 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_eval_suite.py -x`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green + manual dashboard verification
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | EVAL-05 | unit | `pytest tests/test_item_comparison.py::test_comparison_dimension_validates_score_range -x` | ✅ Task creates | ⬜ pending |
| 06-01-02 | 01 | 1 | EVAL-06 | integration | `pytest tests/test_item_comparison.py::test_mock_mode_comparison_deterministic -x` | ✅ Task creates | ⬜ pending |
| 06-03-01 | 03 | 2 | EVAL-02 | unit | `pytest tests/test_eval_suite.py::test_aggregate_25_comparisons -x` | ✅ Task creates | ⬜ pending |
| 06-03-02 | 03 | 2 | EVAL-01 | integration | `pytest tests/test_eval_suite.py::test_eval_suite_runs_in_mock_mode -x` | ✅ Task creates | ⬜ pending |
| 06-03-03 | 03 | 2 | EVAL-07, EVAL-08 | unit | `pytest tests/test_eval_suite.py::test_baseline_comparison_documents_success_criteria -x` | ✅ Task creates | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Note:** All tasks follow TDD pattern (test creation within task action). Tests are created incrementally as part of implementation, not in separate Wave 0. Each task marked `tdd="true"` includes RED-GREEN-REFACTOR cycle.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard UI displays results | EVAL-02 | Visual validation | 1. Run `/v1/run-evaluation`<br>2. Open `/evaluation` route<br>3. Verify 4 dimension cards render with scores |
| Aggregated metrics calculation | EVAL-02 | Verify correct formulas | 1. Check dashboard shows overall system quality score<br>2. Verify equal weighting (25% per dimension)<br>3. Compare to manual calculation |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or explicit TDD creation
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] TDD tasks create tests as part of implementation (no separate Wave 0 needed)
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** Compliant (tests created incrementally via TDD pattern)
