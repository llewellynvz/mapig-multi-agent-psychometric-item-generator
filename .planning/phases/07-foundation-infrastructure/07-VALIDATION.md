---
phase: 7
slug: foundation-infrastructure
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | none — uses pytest defaults (autodiscovery from tests/ directory) |
| **Quick run command** | `pytest tests/test_schemas.py tests/test_graph.py tests/test_llm_factory.py -x` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_schemas.py tests/test_graph.py tests/test_llm_factory.py -x`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 0 | INFRA-01 | unit | `pytest tests/test_schemas.py::test_correlation_matrix_validation -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 0 | INFRA-02 | unit | `pytest tests/test_schemas.py::test_finaloutput_analytics_backward_compat -x` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 0 | INFRA-02 | unit | `pytest tests/test_schemas.py::test_finaloutput_analytics_populated -x` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 0 | INFRA-01 | unit | `pytest tests/test_graph.py::test_graphstate_analytics_fields -x` | ❌ W0 | ⬜ pending |
| 07-01-05 | 01 | 0 | INFRA-05 | unit | `pytest tests/test_graph.py::test_accumulate_tokens_gpt52 -x` | ❌ W0 | ⬜ pending |
| 07-01-06 | 01 | 0 | ALL | integration | `pytest tests/test_graph.py::test_analytics_placeholders_no_op -x` | ❌ W0 | ⬜ pending |
| 07-01-07 | 01 | 0 | INFRA-05 | unit | `pytest tests/test_llm_factory.py::test_gpt52_analytics_model_config -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | ALL | regression | `pytest tests/ -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_schemas.py` — add test_correlation_matrix_validation, test_finaloutput_analytics_backward_compat, test_finaloutput_analytics_populated stubs for INFRA-01, INFRA-02
- [ ] `tests/test_graph.py` — add test_graphstate_analytics_fields, test_accumulate_tokens_gpt52, test_analytics_placeholders_no_op stubs for INFRA-01, INFRA-05, ALL
- [ ] `tests/test_llm_factory.py` — add test_gpt52_analytics_model_config stub for INFRA-05

*Framework already installed (pytest 9.0.2 in pyproject.toml).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SSE events emit for analytics placeholder nodes | ALL | Requires running full backend with SSE client | Start backend, trigger generation, verify node_start/complete events in browser DevTools Network tab |
| Frontend renders without errors when analytics fields are None | INFRA-02 | Requires visual verification | Load generation results page, confirm no JS errors in console |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
