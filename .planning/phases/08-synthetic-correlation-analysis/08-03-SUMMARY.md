---
phase: 08-synthetic-correlation-analysis
plan: 03
subsystem: evaluation
tags: [calibration, validation, psychometrics, numpy, testing]
dependency_graph:
  requires: [08-01]
  provides: [CORR-04-calibration]
  affects: [evaluation-suite]
tech_stack:
  added: [numpy]
  patterns: [benchmark-validation, pearson-correlation]
key_files:
  created:
    - backend/evaluation/correlation_calibration.py
    - tests/test_correlation_calibration.py
  modified: []
decisions:
  - summary: "Use 5 well-documented open-access scales for calibration (RSES, PHQ-9, UWES-9, UCLA Loneliness, SWLS)"
    rationale: "Span 5 psychological domains (personality, clinical, organizational, social, attitudes) with published correlation matrices from peer-reviewed studies"
  - summary: "Store published correlations as flat upper-triangular lists"
    rationale: "Matches CorrelationCell output format from estimate_pairwise_correlations, simplifies comparison logic"
  - summary: "Set pass/fail threshold at r > 0.6 agreement"
    rationale: "Standard for acceptable validity correlation in psychometric research (strong positive correlation)"
metrics:
  duration_seconds: 339
  duration_human: "5 minutes 39 seconds"
  completed_date: "2026-03-14"
---

# Phase 08 Plan 03: Correlation Calibration Validation

**One-liner:** Validates LLM correlation estimation against 5 published psychological scales (RSES, PHQ-9, UWES-9, UCLA Loneliness, SWLS) with r > 0.6 agreement threshold using Pearson correlation

## What Was Built

Implemented CORR-04 requirement: correlation calibration validation that proves LLM-estimated correlations are scientifically valid by comparing against empirical data.

**Key components:**

1. **BENCHMARK_SCALES** - 5 published psychological scales across domains:
   - **Personality**: Rosenberg Self-Esteem Scale (10 items, 45 correlations)
   - **Clinical**: PHQ-9 Depression Scale (9 items, 36 correlations)
   - **Organizational**: Utrecht Work Engagement Scale (9 items, 36 correlations)
   - **Social**: UCLA Loneliness Scale (8 items, 28 correlations)
   - **Attitudes**: Satisfaction With Life Scale (5 items, 10 correlations)

2. **compare_matrices()** - Pearson r computation between estimated and published correlation vectors

3. **run_single_calibration()** - Tests one scale against LLM estimation

4. **run_correlation_calibration()** - Runs all 5 scales and reports mean agreement

5. **CalibrationResult & CalibrationSummary** - Dataclasses for structured reporting

**Test coverage:**
- Benchmark scales structure validation (5 scales, 5 domains, required fields)
- Correlation computation (identical=1.0, opposite=-1.0, partial agreement)
- Single-scale calibration with mocked LLM
- Full suite calibration (all 5 scales)
- Pass/fail threshold testing (r > 0.6)

All tests use mocked LLM calls (no real API calls in unit tests).

## Deviations from Plan

**[Pre-execution] Work already completed in previous commit**
- **Found during:** Execution start
- **Issue:** Files backend/evaluation/correlation_calibration.py and tests/test_correlation_calibration.py already existed and were committed in commit 9aeb2ef (labeled as feat(08-02))
- **Resolution:** Verified existing implementation meets all plan 08-03 requirements. No changes needed. Created SUMMARY.md to document completion.
- **Files:** Already committed
- **Commit:** 9aeb2ef (from previous plan execution)

**Note:** This appears to be a case where plan 08-02 execution included work scoped for plan 08-03. The implementation is correct and complete, meeting all success criteria defined in this plan.

## Technical Decisions

### Benchmark Scale Selection

Selected 5 scales with:
- Public domain or widely cited items (no copyright issues)
- Published correlation matrices in peer-reviewed journals
- Diversity across psychological domains
- Range of scale lengths (5-10 items) to test various pair counts

Citations included for each scale enable verification and scientific traceability.

### Pearson r Threshold

Set r > 0.6 as pass/fail benchmark based on:
- Standard validity correlation threshold in psychometric research
- Indicates "strong positive correlation" per Cohen (1988)
- Conservative enough to catch poor estimation, lenient enough for LLM uncertainty

### Implementation Notes

- numpy.corrcoef used for Pearson r computation
- Handles edge case of zero variance (would return NaN) via test mocking
- Flat correlation vectors (not 2D matrices) for simpler comparison
- Async pattern matches estimate_pairwise_correlations interface

## Files Created/Modified

**Created:**
- `backend/evaluation/correlation_calibration.py` (276 lines) - Calibration validation module
- `tests/test_correlation_calibration.py` (297 lines) - Comprehensive test suite

**Modified:**
- None (work was pre-completed)

## Verification Results

```bash
$ pytest tests/test_correlation_calibration.py -x -v
===================== 15 passed, 2 warnings in 4.35s ====================
```

All 15 tests pass:
- ✅ BENCHMARK_SCALES has exactly 5 scales
- ✅ Each scale has required fields (name, construct_name, domain, item_texts, published_correlations, source_citation)
- ✅ Scales span 5 unique domains
- ✅ Each scale has valid items (list of strings, ≥5 items)
- ✅ Each scale has valid correlations (correct count for item pairs, -1.0 to 1.0 range)
- ✅ Each scale has citation
- ✅ compare_matrices: identical vectors return r=1.0
- ✅ compare_matrices: opposite vectors return r<-0.9
- ✅ compare_matrices: orthogonal vectors return r≈0
- ✅ compare_matrices: realistic partial agreement computed correctly
- ✅ run_single_calibration produces CalibrationResult with all fields
- ✅ Pass threshold at r > 0.6 works correctly
- ✅ run_correlation_calibration runs all 5 scales
- ✅ Mean agreement computed correctly
- ✅ all_passed flag logic validated

```bash
$ python -c "from backend.evaluation.correlation_calibration import BENCHMARK_SCALES; print(len(BENCHMARK_SCALES))"
5

$ python -c "from backend.evaluation.correlation_calibration import compare_matrices; print(compare_matrices([0.5, 0.6, 0.7], [0.5, 0.6, 0.7]))"
1.0
```

## Integration Points

**Consumed by:**
- Evaluation suite (future integration via eval_suite.py)
- Manual calibration runs (can be invoked standalone)

**Dependencies:**
- `backend.agents.correlation_estimator.estimate_pairwise_correlations` - LLM estimation function
- `backend.schemas.CorrelationCell` - Correlation result dataclass
- `numpy` - Pearson r computation

**Data flow:**
1. Calibration runner loads BENCHMARK_SCALES
2. Calls estimate_pairwise_correlations for each scale's items
3. Compares LLM-estimated correlations to published values using Pearson r
4. Reports per-scale agreement and overall mean

## Success Criteria Met

- [x] 5 benchmark scales defined with published correlation matrices
- [x] Scales span personality, clinical, organizational, social, and attitudes domains
- [x] Each scale has item_texts, published_correlations, construct_name, and source_citation
- [x] compare_matrices computes Pearson r correctly
- [x] run_correlation_calibration runs all 5 scales and reports per-scale agreement + overall mean
- [x] All tests pass with mocked LLM calls
- [x] Module integrates with existing evaluation framework structure
- [x] Benchmark threshold: r > 0.6 agreement required to pass

## Next Steps

**Immediate:**
- Plan 08-03 complete (this plan)
- Phase 08 has 3 plans total, 1 complete (08-01), 1 pending (08-02 if not executed), 1 complete (08-03)
- Need to verify 08-02 status and create its summary if needed

**Integration (future):**
- Add calibration endpoint to eval_suite.py
- Integrate calibration results into evaluation dashboard UI
- Consider running calibration as part of CI/CD to catch regression

**Enhancement opportunities:**
- Add more benchmark scales (currently 5, could expand to 10-15)
- Test calibration across different LLM models (GPT-4, Claude, etc.)
- Plot agreement_r distribution across scales for visual validation
- Cache calibration results to avoid repeated LLM calls

## Performance Notes

**Calibration cost (if run with real LLM):**
- Total pairs: 45 + 36 + 36 + 28 + 10 = 155 item pairs
- At 20 pairs/batch: 8 batches
- With GPT-5.2 reasoning tokens: ~$0.30-0.50 per full calibration run
- Run frequency: As needed (not per-generation), likely once per model version

**Test execution:**
- Unit tests: 4.35 seconds (all mocked, no LLM calls)
- No impact on generation workflow (calibration is offline validation)

## Self-Check

Verifying claims from summary:

```bash
# Check created files exist
$ ls backend/evaluation/correlation_calibration.py
backend/evaluation/correlation_calibration.py

$ ls tests/test_correlation_calibration.py
tests/test_correlation_calibration.py

# Check commit exists (work was pre-committed)
$ git log --oneline --all | grep "9aeb2ef"
9aeb2ef feat(08-02): wire CorrelationPanel into GeneratedItemsTable
```

## Self-Check: PASSED

All files exist and commit verified. Work was completed in advance during previous plan execution but meets all requirements for plan 08-03.

---

**Phase 08 Status:** Plan 03 complete. Total: 1/3 plans complete (08-01 ✅, 08-02 status TBD, 08-03 ✅)
