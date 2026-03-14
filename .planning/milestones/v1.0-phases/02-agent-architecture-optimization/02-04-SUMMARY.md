---
phase: 02-agent-architecture-optimization
plan: 04
subsystem: reviewer-agents
tags: [prompts, psychometrics, validation, research-backed]
dependency_graph:
  requires: [02-RESEARCH, 02-02-test-scaffolds]
  provides: [enhanced-content-reviewer, enhanced-linguistic-reviewer]
  affects: [content-validation, linguistic-validation]
tech_stack:
  added: []
  patterns: [research-backed-prompts, structured-evaluation-frameworks]
key_files:
  created: []
  modified:
    - app/prompts/content_reviewer.md
    - app/prompts/linguistic_reviewer.md
    - tests/test_prompts.py
decisions:
  - Enhanced Content Reviewer with 3-step correspondence framework (definition anchoring, competitor specification, facet coverage tracking)
  - Enhanced Linguistic Reviewer with 3-category vague quantifier detection system
  - Used research findings from 02-RESEARCH.md to inform evaluation criteria
  - Maintained existing prompt structure while adding evaluation frameworks
metrics:
  duration_minutes: 7.35
  completed_date: 2026-03-08
  tasks_completed: 2
  tests_added: 0
  tests_unskipped: 2
  files_modified: 3
  commits: 2
---

# Phase 2 Plan 4: Optimize Content and Linguistic Reviewer Prompts Summary

**One-liner:** Enhanced Content and Linguistic Reviewer prompts with research-backed evaluation frameworks for construct correspondence and vague quantifier detection.

## Overview

Successfully optimized Content Reviewer and Linguistic Reviewer prompts by adding explicit, research-backed evaluation criteria. Content Reviewer now includes a 3-step correspondence framework (definition anchoring, competitor specification, facet coverage tracking). Linguistic Reviewer now includes detailed vague quantifier detection rules across 3 categories with repair guidance.

## Tasks Completed

| Task | Description | Status | Commit |
|------|-------------|--------|--------|
| 1 | Enhance Content Reviewer with correspondence criteria | ✅ Complete | 0a49017 |
| 2 | Enhance Linguistic Reviewer with vague quantifier rules | ✅ Complete | d70c8f3 |

## Key Changes

### Content Reviewer Enhancements (AGT-05)

**Added 3-step Evaluation Framework:**

1. **Construct Definition Anchoring**: Extract 3-5 key elements from construct definition; rate item correspondence based on element coverage (≤3 poor, 4-5 moderate, 6-7 good)

2. **Competitor Construct Specification**: Identify close neighbors; assess distinctiveness risk (≤4 measures wrong construct, 5-6 some ambiguity, 7 unambiguous)

3. **Facet Coverage Tracking**: Maintain running count of facets; flag imbalance >2:1 ratio when facet undercovered (<20%)

**Files Modified:**
- `app/prompts/content_reviewer.md` (+39 lines)
- Added "Evaluation Framework" section with structured guidance
- Added facet balance summary note to Output contract

### Linguistic Reviewer Enhancements (AGT-06)

**Added Vague Quantifier Detection and Repair Section:**

1. **Category 1 - Requires time anchoring**: "often", "sometimes", "rarely", "usually", "frequently", "occasionally"
   - Fix: Add time window OR remove quantifier
   - Severity: 4 (medium-high)

2. **Category 2 - Avoid entirely**: "never", "always", "all the time", "constantly"
   - Fix: Replace with bounded frequency or remove
   - Severity: 4 (medium-high)

3. **Category 3 - Context-dependent**: "typically", "generally", "usually"
   - Acceptable for dispositional constructs
   - Problematic for situation-specific constructs
   - Severity: 4 if misused, 2 if appropriate

**Files Modified:**
- `app/prompts/linguistic_reviewer.md` (+58 lines)
- Added "Vague Quantifier Detection and Repair" section
- Updated "What to check" to reference detailed rules
- Included detection patterns, examples, and scoring rules

### Test Updates

**Unskipped Tests:**
- `test_content_reviewer_criteria` (AGT-05)
- `test_linguistic_reviewer_quantifiers` (AGT-06)

Both tests now pass, verifying that prompts contain required research-backed evaluation criteria.

## Technical Decisions

1. **Maintained existing prompt structure**: Added evaluation frameworks as new sections rather than restructuring entire prompts to minimize disruption to existing agent behavior

2. **Research-driven criteria**: Used findings from 02-RESEARCH.md to inform evaluation frameworks rather than relying on intuition

3. **Actionable guidance**: Provided specific scoring thresholds, detection patterns, and repair examples for clarity and consistency

## Verification Results

All verification commands passed:

```bash
# All reviewer tests pass
pytest tests/test_prompts.py -k "content_reviewer or linguistic_reviewer" -v
# ✅ 2 passed

# Prompt files updated
wc -l app/prompts/content_reviewer.md app/prompts/linguistic_reviewer.md
# ✅ 132 lines (content_reviewer), 103 lines (linguistic_reviewer)

# Content Reviewer criteria present
grep -i "construct definition anchoring|competitor construct|facet coverage" app/prompts/content_reviewer.md | wc -l
# ✅ 6 matches

# Linguistic Reviewer quantifier rules present
grep -i "Category 1|Category 2|Category 3|time anchoring" app/prompts/linguistic_reviewer.md | wc -l
# ✅ 6 matches
```

## Success Criteria Met

- ✅ content_reviewer.md enhanced with 3-step correspondence evaluation framework
- ✅ Construct definition anchoring guidance with scoring thresholds
- ✅ Competitor construct specification with distinctiveness scoring
- ✅ Facet coverage tracking with imbalance detection
- ✅ linguistic_reviewer.md enhanced with vague quantifier detection rules
- ✅ 3 categories of quantifiers with detection patterns and repair guidance
- ✅ Severity scoring rules for each quantifier category
- ✅ All 2 reviewer tests pass (AGT-05, AGT-06)

## Deviations from Plan

None - plan executed exactly as written.

## Files Modified

- `app/prompts/content_reviewer.md` - Added Evaluation Framework section (39 lines)
- `app/prompts/linguistic_reviewer.md` - Added Vague Quantifier Detection and Repair section (58 lines)
- `tests/test_prompts.py` - Unskipped 2 tests for AGT-05 and AGT-06

## Next Steps

Prompts now ready for integration into agent execution flow. Enhanced evaluation frameworks should improve reviewer accuracy and consistency during item validation.

## Performance

- **Duration**: 7.35 minutes
- **Commits**: 2 (1 per task)
- **Tests**: 2 unskipped, 2 passing
- **Files**: 3 modified

## Self-Check: PASSED

All claims verified:
- ✅ SUMMARY.md file created
- ✅ All modified files exist (3 files)
- ✅ All commits exist (2 commits: 0a49017, d70c8f3)
- ✅ All tests pass (2 tests)
