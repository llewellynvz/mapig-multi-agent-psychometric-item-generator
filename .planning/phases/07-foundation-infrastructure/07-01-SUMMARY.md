---
phase: 07-foundation-infrastructure
plan: 01
subsystem: schemas
tags: [analytics, pydantic, typescript, correlation, comparison, discriminant-validity]
dependency_graph:
  requires: []
  provides:
    - CorrelationMatrix schema
    - ComparisonInstrument schema
    - CrossConstructComparison schema
    - FinalOutput analytics extension
    - Frontend analytics types
  affects:
    - backend/schemas.py
    - src/lib/types.ts
    - tests/test_schemas.py
tech_stack:
  added:
    - Pydantic v2 validation constraints (ge=-1.0, le=1.0 for correlations)
    - TypeScript interfaces for analytics types
  patterns:
    - ConfigDict(extra="forbid") for all new models
    - Field(default_factory=list) for mutable defaults
    - Optional[Type] for backward compatibility
    - Symmetric type mirroring (Python ↔ TypeScript)
key_files:
  created:
    - .planning/phases/07-foundation-infrastructure/07-01-SUMMARY.md
  modified:
    - backend/schemas.py: +105 lines (5 new analytics models, FinalOutput extension)
    - src/lib/types.ts: +53 lines (5 new TypeScript interfaces, FinalOutput extension, AuditMetadata completion)
    - tests/test_schemas.py: +359 lines (7 new test functions)
decisions:
  - decision: Use flat list of CorrelationCell (upper-triangular only) instead of 2D matrix
    rationale: Simpler serialization, avoids null padding for upper-triangular data, easier to iterate in UI
    alternatives: 2D array with nulls, sparse matrix format
  - decision: Store disclaimer as field with default value instead of adding at UI render time
    rationale: Ensures disclaimer always present in exported JSON, backend owns the disclaimer text, consistent with audit metadata pattern
    alternatives: UI-side disclaimer injection
  - decision: Allow optional construct_pairs in CrossConstructComparison (default_factory=list)
    rationale: Enables incremental implementation - Phase 9 can provide summary analysis_summary first, then add per-pair analysis in refinement
    alternatives: Make construct_pairs required
  - decision: Use string for internal_consistency_flag and discriminant_validity_flag instead of enum
    rationale: LLM agents output strings, avoids Pydantic enum validation errors if LLM produces slight variation, simpler for Phase 8-9 implementation
    alternatives: Literal type with strict validation
metrics:
  duration_minutes: 3
  tasks_completed: 2
  tests_added: 7
  files_modified: 3
  lines_added: 517
  commits: 2
  completed_date: "2026-03-14T10:03:11Z"
---

# Phase 7 Plan 01: Analytics Schema Foundation Summary

**One-liner:** Define Pydantic models for correlation matrix (CorrelationCell, CorrelationMatrix), instrument comparison (ComparisonInstrument), and discriminant validity (ConstructPairAnalysis, CrossConstructComparison), extend FinalOutput with optional analytics fields, and mirror all types in frontend TypeScript.

## What Was Built

Added five new Pydantic models to `backend/schemas.py` that establish the data contracts for v2.0 analytics features:

1. **CorrelationCell** - Single pairwise correlation with confidence interval (item_i_index, item_j_index, correlation [-1.0, 1.0], ci_low, ci_high)
2. **CorrelationMatrix** - Scale-level correlation analysis (cells list, Cronbach's alpha [0.0, 1.0], mean inter-item correlation, internal consistency flag, disclaimer)
3. **ComparisonInstrument** - Validated instrument from literature (name, construct, citation, optional psychometric properties)
4. **ConstructPairAnalysis** - Per-pair discriminant validity reasoning (construct_a, construct_b, estimated correlation, validity flag, reasoning)
5. **CrossConstructComparison** - Full discriminant validity assessment (target construct, comparison constructs list, summary, construct pairs, disclaimer)

Extended `FinalOutput` schema with three optional fields:
- `correlation_matrix: Optional[CorrelationMatrix]` - Synthetic correlation analysis (Phase 8)
- `comparison_instruments: List[ComparisonInstrument]` - Literature instruments (Phase 9)
- `cross_construct_analysis: Optional[CrossConstructComparison]` - Discriminant validity (Phase 9)

Mirrored all backend types in `src/lib/types.ts` with field-for-field TypeScript interfaces. Also completed `AuditMetadata` interface by adding missing `chatgpt_cost`, `smart_validation_used`, and `validation_model_used` fields.

## Implementation Details

### Backend Schema Design

All analytics models follow project conventions:
- `model_config = ConfigDict(extra="forbid")` - Reject unexpected fields
- Numeric constraints via Field(..., ge=X, le=Y) - Enforce valid ranges
- `Field(default_factory=list)` for mutable defaults - Prevent shared references across instances
- Optional fields with default=None - Enable incremental implementation

**CorrelationCell** constraints:
- `correlation`, `ci_low`, `ci_high`: ge=-1.0, le=1.0 (valid correlation range)
- `item_i_index`, `item_j_index`: ge=0 (non-negative item indices)

**CorrelationMatrix** constraints:
- `cells`: min_length=1 (at least one correlation)
- `cronbachs_alpha`: ge=0.0, le=1.0 (valid reliability range)
- `disclaimer`: default="LLM-estimated, not empirically validated" (transparency)

**ComparisonInstrument** constraints:
- `name`, `construct`: min_length=2
- `source_citation`: min_length=5
- `sample_items_count`: ge=0 (if provided)

**ConstructPairAnalysis** constraints:
- `estimated_correlation`: ge=-1.0, le=1.0 (if provided)
- `reasoning`: max_length=500 (prevent token bloat)

**CrossConstructComparison** constraints:
- `target_construct`: min_length=2
- `analysis_summary`: min_length=10
- `construct_pairs`: default_factory=list (optional per-pair analysis)
- `disclaimer`: default="LLM-estimated, not empirically validated"

### FinalOutput Backward Compatibility

Existing v1.1 code that creates `FinalOutput(final_items=[...], audit=...)` continues to work unchanged:
- `correlation_matrix` defaults to `None`
- `comparison_instruments` defaults to `[]` (via default_factory=list)
- `cross_construct_analysis` defaults to `None`

Tested via `test_finaloutput_analytics_backward_compat` - verified existing pattern still passes.

### TypeScript Type Mirroring

All backend Pydantic models mirrored as TypeScript interfaces in `src/lib/types.ts`:
- Required fields → non-optional properties
- Optional[T] → property?: Type
- List[T] → Type[]
- float → number
- str → string

Also completed `AuditMetadata` interface by adding:
- `chatgpt_cost?: number` (was missing from frontend but present in backend since Phase 3)
- `smart_validation_used?: boolean`
- `validation_model_used?: string`

TypeScript compilation verified via `npx tsc --noEmit --strict src/lib/types.ts` - no type errors.

## Testing

Added 7 new test functions to `tests/test_schemas.py` (359 lines):

**CorrelationCell validation:**
- `test_correlation_cell_validation` - Valid creation, boundary values (-1.0, 1.0), rejects out-of-range (correlation > 1.0, < -1.0), rejects negative item index

**CorrelationMatrix validation:**
- `test_correlation_matrix_validation` - Valid creation with cells and aggregates, disclaimer default check, boundary values (alpha 0.0 and 1.0), rejects invalid alpha (> 1.0), rejects empty cells list

**ComparisonInstrument validation:**
- `test_comparison_instrument_validation` - Valid creation with all fields, minimal valid (only required fields), rejects name too short, rejects extra field (extra="forbid")

**CrossConstructComparison validation:**
- `test_cross_construct_comparison_validation` - Valid creation with construct_pairs, minimal valid (no pairs), disclaimer default, rejects target_construct too short, rejects extra field

**FinalOutput backward/forward compatibility:**
- `test_finaloutput_analytics_backward_compat` - FinalOutput without analytics fields → defaults to None/[]
- `test_finaloutput_analytics_populated` - FinalOutput with all analytics fields → serializes correctly via model_dump()
- `test_finaloutput_analytics_mutable_defaults` - comparison_instruments list not shared across instances

**All tests pass:**
- 7 new tests: PASSED
- 14 existing tests: PASSED (backward compatibility verified)
- Total: 21/21 tests passing

## Verification

1. All existing tests pass: `python -m pytest tests/test_schemas.py -x` → 21/21 PASSED
2. New analytics schema tests pass: All 7 new tests PASSED
3. TypeScript types compile: `npx tsc --noEmit --strict src/lib/types.ts` → No errors
4. Backward compatibility verified: `test_finaloutput_backward_compatibility` still passes (Phase 03.1 pattern)
5. Mutable defaults verified: `test_finaloutput_mutable_defaults` passes for both old and new list fields

## Deviations from Plan

### Auto-fixed Issues

**None** - Plan executed exactly as written. No bugs, missing functionality, or blocking issues encountered.

## Key Decisions

1. **Flat list for CorrelationMatrix.cells (not 2D array)**
   - Stores upper-triangular correlations as flat list (N*(N-1)/2 cells for N items)
   - Simpler JSON serialization, no null padding, easier to map() in React
   - UI rendering (Phase 8) will reconstruct 2D heatmap from flat list

2. **Disclaimer as field with default value**
   - Backend owns disclaimer text ("LLM-estimated, not empirically validated")
   - Always present in exported JSON, ensures transparency
   - Alternative (UI-side injection) would require frontend to remember disclaimer

3. **Optional construct_pairs in CrossConstructComparison**
   - Enables incremental implementation: Phase 9 can provide `analysis_summary` first, add per-pair analysis in refinement
   - Uses `Field(default_factory=list)` for mutable default safety

4. **String flags instead of enums**
   - `internal_consistency_flag` and `discriminant_validity_flag` are strings, not Literal types
   - LLM agents output strings naturally, avoids Pydantic validation errors if LLM produces slight variation ("Good" vs "good")
   - Simpler for Phase 8-9 agent implementation

## Files Modified

**Created:**
- `.planning/phases/07-foundation-infrastructure/07-01-SUMMARY.md` (this file)

**Modified:**
- `backend/schemas.py` (+105 lines)
  - Added 5 analytics models before FinalOutput class
  - Extended FinalOutput with 3 optional analytics fields
  - All models use ConfigDict(extra="forbid")
  - All List fields use Field(default_factory=list)

- `src/lib/types.ts` (+53 lines)
  - Added 5 analytics TypeScript interfaces
  - Extended FinalOutput interface with 3 optional analytics fields
  - Completed AuditMetadata interface (added chatgpt_cost, smart_validation_used, validation_model_used)

- `tests/test_schemas.py` (+359 lines)
  - Added 7 test functions for analytics schemas
  - Tests validation constraints, extra="forbid", backward/forward compatibility, mutable defaults

## Dependencies

**Requirements fulfilled:**
- INFRA-01: Schema extensions for analytics data (CorrelationMatrix, ComparisonInstrument, CrossConstructComparison added to FinalOutput)
- INFRA-02: GraphState extensions for analytics data (deferred to Plan 02 - agent state modifications)

**Enables:**
- Phase 8 (Correlation Analysis): CorrelationMatrix schema ready for correlation_analyzer_agent to populate
- Phase 9 (Comparison + Cross-Construct): ComparisonInstrument and CrossConstructComparison schemas ready for comparison_agent
- All analytics features now have data contracts to implement against

**Affects:**
- `backend/schemas.py` - All analytics agents will import these types
- `src/lib/types.ts` - All analytics UI components will import these interfaces
- `tests/test_schemas.py` - Baseline test coverage for analytics schemas

## Next Steps

1. **Plan 02** - Extend GraphState with analytics fields, update graph builder to add analytics nodes
2. **Phase 8** - Implement correlation_analyzer_agent using CorrelationMatrix schema
3. **Phase 9** - Implement comparison_agent using ComparisonInstrument and CrossConstructComparison schemas
4. **UI rendering** - Phase 8/9 frontend work will consume the TypeScript types defined here

## Commits

1. `b8659c0` - feat(07-01): define analytics Pydantic models and extend FinalOutput
2. `40cc0fb` - feat(07-01): mirror analytics types in frontend TypeScript

## Self-Check: PASSED

**Files created:**
- FOUND: .planning/phases/07-foundation-infrastructure/07-01-SUMMARY.md

**Files modified:**
- FOUND: backend/schemas.py (contains "class CorrelationMatrix")
- FOUND: src/lib/types.ts (contains "export interface CorrelationMatrix")
- FOUND: tests/test_schemas.py (contains "test_correlation_matrix_validation")

**Commits exist:**
- FOUND: b8659c0 (feat(07-01): define analytics Pydantic models and extend FinalOutput)
- FOUND: 40cc0fb (feat(07-01): mirror analytics types in frontend TypeScript)

**Tests pass:**
- VERIFIED: All 21 tests in test_schemas.py pass
- VERIFIED: TypeScript compiles without errors

All claims in this summary are verified and accurate.
