---
phase: 02-agent-architecture-optimization
plan: 01
subsystem: testing
tags: [test-scaffolds, tdd, psychometric-principles, adaptive-thresholds, bias-detection]
dependency_graph:
  requires: []
  provides:
    - test_prompts.py (AGT-01 through AGT-09 validation)
    - test_critic.py (AGT-10 adaptive threshold tests)
    - test_bias_reviewer.py (AGT-08 structured checklist test)
  affects:
    - Phase 2 Wave 1 plans (02-02, 02-03, 02-04, 02-05)
tech_stack:
  added: []
  patterns:
    - pytest.skip() for pre-implementation test scaffolds
    - Comprehensive docstrings linking to requirement IDs
    - File-based prompt content validation
key_files:
  created:
    - tests/test_prompts.py: 8 test scaffolds for prompt content validation
    - tests/test_critic.py: 4 test scaffolds for adaptive threshold logic
    - tests/test_bias_reviewer.py: 1 test scaffold for structured checklist
  modified: []
decisions: []
metrics:
  duration_minutes: 6.85
  completed_date: "2026-03-08"
  tasks_completed: 3
  tests_created: 13
  files_created: 3
---

# Phase 2 Plan 01: Test Scaffolds for Agent Prompt Optimizations Summary

Test scaffolds created for all 10 Phase 2 agent architecture requirements (AGT-01 through AGT-10), enabling TDD workflow for prompt optimization.

## What Was Built

Created comprehensive test scaffolds for validating agent prompt optimizations across three test files:

**tests/test_prompts.py (8 tests)**
- AGT-01: Item Writer 10 psychometric principles validation
- AGT-02: Semantic diversity examples in Section B
- AGT-03: Reading level targets (6th-8th, 5th-6th, 10th-12th grade)
- AGT-04: Positive keying requirement (no reverse items)
- AGT-05: Content Reviewer construct correspondence criteria
- AGT-06: Linguistic Reviewer vague quantifier rules (3 categories)
- AGT-07: Bias Reviewer 7-type bias taxonomy
- AGT-09: Meta Editor facet balancing rules (≥20%, 2:1 ratio)

**tests/test_critic.py (4 tests)**
- AGT-10: Early iteration thresholds (strict: bias_blocker=4, accept_max_severity=2)
- AGT-10: Mid iteration thresholds (standard: accept_max_severity=3)
- AGT-10: Late iteration thresholds (relaxed: bias_blocker=5, accept_max_severity=4)
- AGT-10: Threshold mode transparency in decision reasons

**tests/test_bias_reviewer.py (1 test)**
- AGT-08: Structured checklist format validation (single comprehensive pass vs. multi-pass)

## Technical Implementation

### Test Structure Pattern

All tests follow Phase 1 established pattern:
- `@pytest.mark.skip()` decorator with plan reference
- Comprehensive docstrings linking to requirement IDs
- Expected behavior documentation
- File-based validation (reading prompt markdown files)
- Clear assertion messages

### Coverage Mapping

| Requirement | Test Function | File | Plan |
|-------------|---------------|------|------|
| AGT-01 | test_item_writer_10_principles | test_prompts.py | 02-02 |
| AGT-02 | test_item_writer_semantic_diversity | test_prompts.py | 02-02 |
| AGT-03 | test_item_writer_reading_levels | test_prompts.py | 02-02 |
| AGT-04 | test_item_writer_positive_keying | test_prompts.py | 02-02 |
| AGT-05 | test_content_reviewer_criteria | test_prompts.py | 02-04 |
| AGT-06 | test_linguistic_reviewer_quantifiers | test_prompts.py | 02-04 |
| AGT-07 | test_bias_reviewer_7_types | test_prompts.py | 02-03 |
| AGT-08 | test_structured_checklist | test_bias_reviewer.py | 02-03 |
| AGT-09 | test_meta_editor_facet_balance | test_prompts.py | 02-04 |
| AGT-10 | 4 adaptive threshold tests | test_critic.py | 02-05 |

### Verification

All tests collect successfully:
```bash
$ pytest tests/test_prompts.py tests/test_critic.py tests/test_bias_reviewer.py --collect-only
========================= 13 tests collected in 0.02s =========================
```

No tests execute (all skipped) - implementation comes in Wave 1 plans.

## Deviations from Plan

None - plan executed exactly as written.

## Dependencies

**Downstream Consumers:**
- Plan 02-02: Item Writer optimization (will unskip AGT-01, AGT-02, AGT-03, AGT-04 tests)
- Plan 02-03: Bias Reviewer optimization (will unskip AGT-07, AGT-08 tests)
- Plan 02-04: Content/Linguistic Reviewer optimization (will unskip AGT-05, AGT-06, AGT-09 tests)
- Plan 02-05: Critic adaptive thresholds (will unskip AGT-10 tests)

**No Blockers:** Test scaffolds are standalone - no external dependencies.

## Next Steps

Wave 1 implementation plans (02-02 through 02-05) will:
1. Implement prompt/logic changes to satisfy test requirements
2. Remove `@pytest.mark.skip()` decorators
3. Run tests to verify implementation
4. Add additional implementation-specific tests as needed

## Validation

✅ tests/test_prompts.py exists with 8 test functions
✅ tests/test_critic.py exists with 4 test functions
✅ tests/test_bias_reviewer.py exists with 1 test function
✅ All 13 tests collect successfully via pytest
✅ Each test has clear docstring linking to requirement ID
✅ No tests execute (all properly marked as skipped)

## Self-Check: PASSED

**Created files verification:**
- ✅ tests/test_prompts.py: exists (297 lines)
- ✅ tests/test_critic.py: exists (185 lines)
- ✅ tests/test_bias_reviewer.py: exists (48 lines)

**Commit verification:**
- ✅ 3b75050: test(02-01): create test scaffolds for agent prompt optimizations

All claimed artifacts exist and are committed.
