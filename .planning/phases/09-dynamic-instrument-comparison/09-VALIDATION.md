---
phase: 9
slug: dynamic-instrument-comparison
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ (backend) + Vitest 3.0+ (frontend) |
| **Config file** | pytest.ini (backend), vitest.config.ts (frontend) |
| **Quick run command** | `pytest tests/test_instrument_searcher.py tests/test_plagiarism_detector.py -x` |
| **Full suite command** | `pytest tests/ --cov=backend` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_instrument_searcher.py tests/test_plagiarism_detector.py -x`
- **After every plan wave:** Run `pytest tests/ --cov=backend/agents/instrument_searcher.py --cov=backend/analytics/similarity_calculator.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|--------|----------|-----------|-------------------|-------------|--------|
| INST-01 | Perplexity instrument search with domain filter | integration | `pytest tests/test_instrument_searcher.py::test_search_convergent_instrument -x` | Yes (W0) | ⬜ pending |
| INST-02 | Hardcoded defaults by domain (personality, clinical, org, social, cognitive) | unit | `pytest tests/test_instrument_searcher.py::test_hardcoded_defaults_coverage -x` | Yes (W0) | ⬜ pending |
| INST-03 | Hybrid search-first with fallback to defaults | integration | `pytest tests/test_instrument_searcher.py::test_search_fallback_on_failure -x` | Yes (W0) | ⬜ pending |
| INST-04 | Dual-direction convergent validity scoring | unit | `pytest tests/test_validity_scorer.py::test_dual_direction_averaging -x` | Yes (W0) | ⬜ pending |
| INST-05 | Publisher blocklist filters results | unit | `pytest tests/test_instrument_searcher.py::test_publisher_blocklist -x` | Yes (W0) | ⬜ pending |
| INST-06 | Cosine similarity plagiarism detection (> 0.85) | unit | `pytest tests/test_plagiarism_detector.py::test_similarity_threshold -x` | Yes (W0) | ⬜ pending |
| XCON-01 | Discriminant instrument search (related-but-distinct) | integration | `pytest tests/test_instrument_searcher.py::test_search_discriminant_instrument -x` | Yes (W0) | ⬜ pending |
| XCON-02 | Dual-direction discriminant validity scoring | unit | `pytest tests/test_validity_scorer.py::test_discriminant_dual_direction -x` | Yes (W0) | ⬜ pending |
| XCON-03 | High overlap warning (r > 0.85) | unit | `pytest tests/test_validity_scorer.py::test_high_overlap_flag -x` | Yes (W0) | ⬜ pending |
| XCON-04 | Related construct identification from Perplexity | integration | `pytest tests/test_instrument_searcher.py::test_related_construct_discovery -x` | Yes (W0) | ⬜ pending |
| UI-02 | ComparisonPanel renders with instruments | component | `npm test -- ComparisonPanel.test.tsx` | Yes (W0) | ⬜ pending |
| UI-03 | InstrumentCard displays metadata and citation | component | `npm test -- InstrumentCard.test.tsx` | Yes (W0) | ⬜ pending |
| UI-04 | Cross-construct table shows discriminant pairs | component | `npm test -- ComparisonPanel.test.tsx::discriminant_section` | Yes (W0) | ⬜ pending |
| UI-05 | Comparison data included in JSON export | verification | `npm run type-check && npm run build` | N/A (export.ts) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_instrument_searcher.py` — stubs for INST-01, INST-02, INST-03, INST-05, XCON-01, XCON-04
- [x] `tests/test_validity_scorer.py` — stubs for INST-04, XCON-02, XCON-03
- [x] `tests/test_plagiarism_detector.py` — stubs for INST-06
- [x] `src/components/__tests__/ComparisonPanel.test.tsx` — stubs for UI-02, UI-04
- [x] `src/components/__tests__/InstrumentCard.test.tsx` — stubs for UI-03
- [x] Framework install: `pip install pytest-asyncio pytest-mock sentence-transformers scikit-learn` — if not already installed

**Wave 0 created by:** Plan 01, Task 0 (creates all stubs before TDD tasks begin)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Perplexity Academic retrieval quality | INST-01 | Depends on live API and search result variability | Test with 5+ known constructs, verify instrument metadata quality |
| UI visual consistency | UI-02, UI-03, UI-04 | Component tests verify rendering, not visual fidelity | Visual inspection of comparison card layout and styling |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready
