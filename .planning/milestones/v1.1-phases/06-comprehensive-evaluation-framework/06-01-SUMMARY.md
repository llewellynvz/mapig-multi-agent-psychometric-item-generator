---
phase: 06-comprehensive-evaluation-framework
plan: 01
subsystem: evaluation
tags: [llm-as-judge, benchmark-comparison, position-bias-mitigation, tdd]
dependency_graph:
  requires: []
  provides: [evaluation-schemas, comparison-logic]
  affects: [future-benchmark-evaluation]
tech_stack:
  added: [backend/evaluation module, item_comparator.md prompt]
  patterns: [LLM-as-judge, structured-output, dual-direction-evaluation]
key_files:
  created:
    - backend/evaluation/__init__.py
    - backend/evaluation/schemas.py
    - backend/evaluation/item_comparison.py
    - backend/prompts/item_comparator.md
    - tests/test_item_comparison.py
  modified: []
decisions:
  - choice: Use dual-direction evaluation (forward + reverse) and average scores
    rationale: Mitigates position bias documented in LLM-as-judge research
  - choice: Reuse validator.py structured output pattern with null handling
    rationale: Proven pattern for LangChain structured output reliability
  - choice: Use get_chat_model_for_agent("validator") for Opus allocation
    rationale: Comparison is critical evaluation task requiring highest accuracy model
  - choice: Mock mode returns deterministic 7.5 average score
    rationale: Enables fast testing without API calls, reasonable mid-range score
metrics:
  duration_minutes: 4.2
  task_count: 2
  file_count: 5
  test_count: 6
  completed_date: "2026-03-09"
---

# Phase 06 Plan 01: Evaluation Infrastructure Summary

**One-liner**: LLM-as-judge comparison logic with 4-criteria scoring (quality, construct, style, psychometric) and position bias mitigation via dual-direction evaluation

## Overview

Created backend evaluation infrastructure with LLM-as-judge item comparison that scores generated items against published scale items across 4 psychometric dimensions. Implemented position bias mitigation by evaluating both item orderings and averaging scores. Foundation for automated benchmarking of MAPIG-generated items against gold-standard published scales.

## Implementation Details

### Task 1: Evaluation Schemas (TDD)

**RED Phase**:
- Created failing tests for ComparisonDimension, ComparisonResult, BenchmarkScale
- Tests verified: score range (1-10), non-empty reasoning, overall score averaging

**GREEN Phase**:
- Implemented ComparisonDimension: score (1-10 float), reasoning (min 10 chars), dimension name
- Implemented ComparisonResult: 4 dimensions + overall_score with Pydantic validator
- Implemented BenchmarkScale: metadata (name, author, year, domain) + items list
- Pydantic validators enforce score ranges and overall score = average of 4 dimensions

**Files**:
- backend/evaluation/schemas.py (78 lines)
- tests/test_item_comparison.py (initial tests)

**Commit**: 3e2b866

### Task 2: LLM-as-Judge Comparison (TDD)

**RED Phase**:
- Created failing tests for compare_to_published_item() function
- Tests verified: mock mode deterministic results, function signature, structured output

**GREEN Phase**:
- Created backend/prompts/item_comparator.md with 4-dimension evaluation criteria
- Implemented compare_to_published_item() with dual-direction evaluation:
  - Forward: generated → published (candidate vs reference)
  - Reverse: published → generated (candidate vs reference)
  - Average scores from both directions to mitigate position bias
- Implemented _compare_single_direction() with structured output and null handling
- Implemented _average_comparison_results() to combine forward/reverse scores
- Mock mode support: returns deterministic 7.5 average score with all 4 dimensions
- Null handling: raises RuntimeError if LLM returns None (matches validator.py pattern)

**Files**:
- backend/evaluation/item_comparison.py (149 lines)
- backend/prompts/item_comparator.md (38 lines)
- tests/test_item_comparison.py (101 lines total, 6 tests)

**Commits**: 5c660b0 (RED), 1f08ef6 (GREEN)

## Technical Decisions

### 1. Position Bias Mitigation Strategy

**Decision**: Evaluate both (generated→published) and (published→generated) orderings, then average scores.

**Rationale**:
- LLM-as-judge research shows position bias: models favor first-presented items
- Dual-direction evaluation neutralizes this by treating both items as "candidate" and "reference"
- Averaging produces unbiased final score

**Trade-offs**:
- ✅ Eliminates position bias
- ✅ More reliable scoring
- ❌ 2x API calls per comparison (acceptable for Opus quality)

### 2. Structured Output Pattern Reuse

**Decision**: Use exact pattern from validator.py: with_structured_output(..., strict=False, include_raw=True) with null handling.

**Rationale**:
- Proven pattern used in production validation agent
- Handles LangChain structured output quirks (parsed response vs raw)
- Null handling prevents silent failures

### 3. Model Allocation

**Decision**: Use get_chat_model_for_agent("validator") to allocate Claude Opus.

**Rationale**:
- Item comparison is a critical evaluation task requiring highest accuracy
- Reuses smart allocation pattern from Phase 03
- Consistent with validation agent model selection

### 4. Mock Mode Design

**Decision**: Return deterministic 7.5 average score (8.0, 7.5, 7.0, 7.5 for dimensions).

**Rationale**:
- Mid-range score (neither perfect nor failing)
- Reasonable psychometric scores for testing
- Enables fast test execution without API calls
- All reasoning strings are ≥10 characters (passes validation)

## Test Coverage

**6 tests total** in tests/test_item_comparison.py:

1. test_comparison_dimension_validates_score_range: Score must be 1-10 (rejects 0.5, 11.0)
2. test_comparison_dimension_requires_reasoning: Reasoning must be non-empty
3. test_benchmark_scale_validates_items: Items list must have ≥1 item
4. test_comparison_result_structure: ComparisonResult has all 4 dimensions + overall score
5. test_mock_mode_comparison_deterministic: Mock mode returns valid ComparisonResult
6. test_comparison_function_signature: Function has expected parameters

**All tests pass** ✅

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

**Created files**:
- ✅ backend/evaluation/__init__.py (5 lines)
- ✅ backend/evaluation/schemas.py (78 lines)
- ✅ backend/evaluation/item_comparison.py (149 lines)
- ✅ backend/prompts/item_comparator.md (38 lines)
- ✅ tests/test_item_comparison.py (101 lines)

**Commits**:
- ✅ 3e2b866: test(06-01): add failing tests for evaluation schemas
- ✅ 5c660b0: test(06-01): add failing tests for LLM-as-judge comparison
- ✅ 1f08ef6: feat(06-01): implement LLM-as-judge comparison with bias mitigation

All files exist, all commits present, all exports available. ✅

---

**Duration**: 4.2 minutes | **Tasks**: 2/2 complete | **Files**: 5 created | **Tests**: 6 passing | **Completed**: 2026-03-09
