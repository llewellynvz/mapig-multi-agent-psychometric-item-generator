---
phase: 02-agent-architecture-optimization
plan: 03
subsystem: agents/bias-detection
tags: [bias-detection, psychometric-validity, prompt-engineering, research-backed]

dependency_graph:
  requires: [02-01, 02-RESEARCH]
  provides: [7-type-bias-taxonomy, structured-bias-checklist, intersectional-bias-detection]
  affects: [app/agents/bias_reviewer.py]

tech_stack:
  added: []
  patterns: [structured-checklist-evaluation, severity-escalation-rules, single-pass-comprehensive-evaluation]

key_files:
  created:
    - tests/test_bias_reviewer.py
  modified:
    - app/prompts/bias_reviewer.md
    - tests/test_prompts.py

decisions:
  - title: 7-type bias taxonomy
    choice: Implemented all 7 bias types from Russell & Kaplan 2021 research
    rationale: Comprehensive bias detection requires systematic coverage of construct, linguistic, cultural reference, socioeconomic, context access, protected attribute, and intersectional bias
    alternatives_considered:
      - Simpler 3-type taxonomy (inadequate coverage)
      - Multi-pass evaluation (higher latency/cost)

  - title: Single-pass evaluation with structured checklist
    choice: 4-step structured checklist enables comprehensive evaluation in one pass
    rationale: Research shows single comprehensive pass is more cost-effective and consistent than multiple passes, while structured format ensures all bias types are systematically evaluated
    alternatives_considered:
      - Multi-pass evaluation (higher cost, latency)
      - Unstructured evaluation (inconsistent coverage)

  - title: Intersectional bias as Step 2
    choice: Separate intersectional bias check after evaluating 7 individual types
    rationale: Intersectional effects only emerge when ≥2 bias types compound for specific identity combinations; separate step ensures systematic detection
    alternatives_considered:
      - Embed in individual type checks (compounds easily missed)
      - Omit intersectional detection (research shows 4-8x sensitivity increase)

  - title: Severity escalation rule for intersectional bias
    choice: Intersectional bias automatically escalates to "high" severity (≥4 on 1-5 scale)
    rationale: Research shows intersectional bias has 4-8x more sensitive effects; automatic escalation ensures appropriate prioritization
    alternatives_considered:
      - Same severity as individual types (underestimates impact)
      - Manual severity assessment (inconsistent application)

metrics:
  duration_minutes: 6.8
  tasks_completed: 1
  tests_added: 2
  tests_passing: 2
  commits: 1
  files_modified: 3
  lines_added: 124
  lines_removed: 21
  requirements_met: [AGT-07, AGT-08]
  completed_date: 2026-03-08
---

# Phase 2 Plan 3: Bias Reviewer 7-Type Taxonomy & Structured Checklist Summary

**One-liner:** Enhanced Bias Reviewer with research-backed 7-type bias taxonomy and structured 4-step checklist for comprehensive single-pass evaluation with automatic intersectional bias detection and severity escalation.

## What Was Built

Enhanced the Bias Reviewer prompt (`app/prompts/bias_reviewer.md`) with:

1. **7 Bias Types Taxonomy** - Comprehensive bias detection framework covering:
   - Construct bias (culture-bound meanings)
   - Linguistic bias (idioms, complex vocabulary)
   - Cultural reference bias (culture-specific knowledge)
   - Socioeconomic bias (resource assumptions)
   - Context access bias (work arrangement assumptions)
   - Protected attribute bias (stereotypes)
   - Intersectional bias (compounding effects)

2. **Structured 4-Step Evaluation Process**:
   - Step 1: Evaluate 6 individual bias types with [✓/✗] checklist
   - Step 2: Intersectional bias check (if ≥2 types flagged)
   - Step 3: Generate ReviewComment with severity escalation rule
   - Step 4: Return results

3. **Severity Escalation Rule**: Intersectional bias automatically escalates to "high" severity (≥4 on 1-5 scale) based on research showing 4-8x sensitivity increase

4. **Reasoning Requirements**: Chain-of-thought documentation for each ReviewComment explaining detected types, affected groups, and fix rationale

## Test Coverage

**Added:**
- `tests/test_bias_reviewer.py` - New test module for Bias Reviewer prompt structure
  - `test_structured_checklist()` - Verifies 4-step evaluation process (AGT-08)

**Modified:**
- `tests/test_prompts.py` - Unskipped existing test
  - `test_bias_reviewer_7_types()` - Verifies all 7 bias types defined (AGT-07)

**Results:** 2/2 tests passing

## Deviations from Plan

None - plan executed exactly as written.

## Requirements Met

- **AGT-07**: Bias Reviewer prompt defines all 7 bias types with clear descriptions
  - All 7 types explicitly named with definitions and examples
  - Taxonomy section provides systematic framework
  - Research citation (Russell & Kaplan 2021) anchors approach

- **AGT-08**: Structured checklist enables comprehensive single-pass evaluation
  - 4-step evaluation process with explicit checklist format
  - Intersectional bias check as separate step
  - Severity escalation rule (≥4) specified
  - Single-pass approach optimizes cost and latency vs multi-pass

## Technical Highlights

1. **Research-Backed Approach**: All 7 bias types sourced from Russell & Kaplan 2021 psychometric research on differential item functioning

2. **Intersectional Bias Detection**: Systematic detection of compounding effects when multiple bias types interact for specific identity combinations

3. **Single-Pass Optimization**: Structured checklist enables comprehensive evaluation in one LLM call, reducing latency and cost compared to multi-pass approaches

4. **Severity Escalation**: Automatic escalation for intersectional bias ensures appropriate prioritization based on research showing 4-8x sensitivity increase

5. **Actionable Format**: Checklist format ([✓/✗] per type) provides clear, systematic evaluation structure for LLM agent

## Files Changed

```
app/prompts/bias_reviewer.md          | 103 lines added, 21 removed (107 total)
tests/test_prompts.py                 | 1 line removed (skip marker)
tests/test_bias_reviewer.py           | 48 lines added (new file)
```

## Commit

```
1bf117e feat(02-03): enhance bias reviewer with 7-type taxonomy and structured checklist
```

## Next Steps

Plan 02-03 complete. Ready for plan 02-04 (Content Reviewer optimization with construct correspondence framework).

---

**Duration:** 6.8 minutes
**Completed:** 2026-03-08
**Status:** ✓ Complete

## Self-Check: PASSED

All claims verified:
- ✓ Created file exists: tests/test_bias_reviewer.py
- ✓ Modified files exist: app/prompts/bias_reviewer.md, tests/test_prompts.py
- ✓ Commit exists: 1bf117e
- ✓ Tests pass: 2/2 passing (test_bias_reviewer_7_types, test_structured_checklist)
