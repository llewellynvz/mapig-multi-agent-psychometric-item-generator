---
phase: 06
slug: comprehensive-evaluation-framework
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 06-01-01 | 01 | 0 | EVAL-01 | integration | `pytest tests/test_eval_suite.py::test_eval_suite_runs_on_demand -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 0 | EVAL-02 | unit | `pytest tests/test_eval_suite.py::test_reports_four_dimensions -x` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 0 | EVAL-03 | unit | `pytest tests/test_eval_suite.py::test_loads_five_benchmarks -x` | ❌ W0 | ⬜ pending |
| 06-01-04 | 01 | 0 | EVAL-04 | unit | `pytest tests/test_eval_suite.py::test_25_test_cases -x` | ❌ W0 | ⬜ pending |
| 06-01-05 | 01 | 0 | EVAL-05 | unit | `pytest tests/test_eval_suite.py::test_llm_comparison_structured_output -x` | ❌ W0 | ⬜ pending |
| 06-01-06 | 01 | 0 | EVAL-06 | integration | `pytest tests/test_eval_suite.py::test_comparison_results_persisted -x` | ❌ W0 | ⬜ pending |
| 06-01-07 | 01 | 0 | EVAL-07 | unit | `pytest tests/test_eval_suite.py::test_baseline_comparison_15_percent -x` | ❌ W0 | ⬜ pending |
| 06-01-08 | 01 | 0 | EVAL-08 | unit | `pytest tests/test_eval_suite.py::test_success_criteria_in_output -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_eval_suite.py` — stubs for EVAL-01 through EVAL-08
- [ ] `tests/test_benchmark_loader.py` — benchmark scale loading and validation
- [ ] `tests/test_item_comparison.py` — LLM-as-judge comparison logic
- [ ] `backend/evaluation/__init__.py` — module initialization
- [ ] `data/benchmarks/` — directory for published scale metadata

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard UI displays results | EVAL-02 | Visual validation | 1. Run `/v1/run-evaluation`<br>2. Open `/evaluation` route<br>3. Verify 4 dimension cards render with scores |
| Aggregated metrics calculation | EVAL-02 | Verify correct formulas | 1. Check dashboard shows overall system quality score<br>2. Verify equal weighting (25% per dimension)<br>3. Compare to manual calculation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
