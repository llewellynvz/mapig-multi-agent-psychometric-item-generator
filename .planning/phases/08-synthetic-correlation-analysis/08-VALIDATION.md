---
phase: 8
slug: synthetic-correlation-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | none — pytest auto-discovery in tests/ directory |
| **Quick run command** | `pytest tests/test_correlation_estimation.py tests/test_omega_calculator.py -x` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds (unit), ~60 seconds (integration with LLM calls) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_correlation_estimation.py tests/test_omega_calculator.py -x`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green + manual heatmap visual QA
- **Max feedback latency:** 15 seconds (unit tests), 60 seconds (integration)

---

## Per-Task Verification Map

| Req ID | Requirement | Test Type | Automated Command | File Exists | Status |
|--------|-------------|-----------|-------------------|-------------|--------|
| CORR-01 | GPT-5.2 generates pairwise correlation matrix from item texts | integration | `pytest tests/test_correlation_estimation.py::test_estimate_correlations -x` | ❌ W0 | ⬜ pending |
| CORR-02 | reliabiliPy calculates omega_total from correlation matrix with ω ≥ 0.70 threshold | unit | `pytest tests/test_omega_calculator.py::test_calculate_omega -x` | ❌ W0 | ⬜ pending |
| CORR-03 | Each CorrelationCell includes ci_low and ci_high fields | unit | `pytest tests/test_schemas.py::test_correlation_cell_ci -x` | ❌ W0 | ⬜ pending |
| CORR-04 | Benchmark validation: LLM-estimated vs published matrices achieve r > 0.6 | integration | `pytest tests/test_correlation_calibration.py::test_benchmark_agreement -x` | ❌ W0 | ⬜ pending |
| CORR-05 | CorrelationMatrix.disclaimer field populated with default text | unit | `pytest tests/test_schemas.py::test_correlation_disclaimer -x` | ❌ W0 | ⬜ pending |
| CORR-06 | Internal consistency flag computed from mean inter-item r (0.15-0.50 range) | unit | `pytest tests/test_omega_calculator.py::test_internal_consistency_flag -x` | ❌ W0 | ⬜ pending |
| UI-01 | Visx heatmap renders with Psynalytics brand colors | manual-only | N/A — requires visual inspection | Manual QA | ⬜ pending |
| UI-05 | Correlation matrix CSV export produces square matrix with truncated headers | unit | `pytest tests/test_export_correlation.py::test_csv_matrix_export -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_correlation_estimation.py` — covers CORR-01 (GPT-5.2 pairwise estimation)
- [ ] `tests/test_omega_calculator.py` — covers CORR-02, CORR-06 (omega calculation, consistency flags)
- [ ] `tests/test_correlation_calibration.py` — covers CORR-04 (benchmark validation)
- [ ] `tests/test_export_correlation.py` — covers UI-05 (CSV export)
- [ ] Extend `tests/test_schemas.py` — add CORR-03, CORR-05 test cases for CorrelationCell/CorrelationMatrix
- [ ] Framework already installed (pytest 9.0.2) — no installation needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visx heatmap renders with Psynalytics brand gradient | UI-01 | Requires visual inspection of color gradient in browser | Open results page, expand correlation panel, verify teal-white-lime gradient matches brand palette |
| Heatmap hover tooltips display correctly | UI-01 | Interaction testing requires browser | Hover over cells, verify tooltip shows correlation value, CI range, and item pair text |
| Heatmap click popover shows reasoning | UI-01 | Interaction testing requires browser | Click cell, verify detail popover opens with full reasoning text |
| Dark mode heatmap rendering | UI-01 | CSS-dependent visual testing | Toggle dark mode, verify heatmap maintains readability and contrast |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
