---
phase: 03-claude-api-migration
plan: 02
subsystem: frontend-ui
tags: [ui, model-selection, cost-tracking, user-control]
dependency_graph:
  requires: [frontend/src/lib/schemas.ts, frontend/src/components/InstrumentSetupForm.tsx]
  provides: [model-provider-selector, cost-breakdown-display]
  affects: [frontend/src/lib/types.ts, frontend/src/components/EvidenceAuditPanel.tsx]
tech_stack:
  added: [shadcn/ui-select, model-provider-enum]
  patterns: [conditional-rendering, localStorage-persistence]
key_files:
  created: []
  modified:
    - frontend/src/lib/schemas.ts
    - frontend/src/components/InstrumentSetupForm.tsx
    - frontend/src/lib/types.ts
    - frontend/src/components/EvidenceAuditPanel.tsx
decisions:
  - id: model-provider-as-first-field
    summary: Positioned model_provider as first field in schema and first visible field in form UI
    rationale: User specification in 03-CONTEXT.md requires top placement for visibility and ease of access
  - id: cost-display-in-audit-panel
    summary: Added cost breakdown to EvidenceAuditPanel instead of creating new ResultsSummaryPanel
    rationale: ResultsSummaryPanel doesn't exist; EvidenceAuditPanel already displays audit metadata and is the logical location for cost tracking
  - id: conditional-cost-rendering
    summary: Display cost section only when audit.opus_cost and audit.total_cost are defined
    rationale: Graceful degradation ensures UI works before backend implements cost tracking (Plan 03-03)
metrics:
  duration: 3.05
  completed: 2026-03-09T02:06:38Z
  tasks_completed: 3
  files_modified: 4
  commits: 3
---

# Phase 03 Plan 02: Frontend Model Selection UI and Cost Display Summary

**One-liner:** Model provider selector (Claude/OpenAI) with cost breakdown display in audit panel

## Overview

Added frontend UI components to enable users to select their LLM provider (Claude as default, OpenAI as fallback) and view detailed API cost breakdowns after generation completes. This gives users control over model selection and transparency into API spending.

## Tasks Completed

### Task 1: Add model_provider field to frontend schema
**Status:** ✅ Complete
**Commit:** `6c7b455`

- Extended `instrumentSetupSchema` with `model_provider` enum field ("claude" | "openai")
- Positioned as first field in schema object
- Added `MODEL_PROVIDER_OPTIONS` constant for UI dropdown
- Updated `defaultInstrumentSetup` to default to "claude"
- TypeScript compilation successful

**Files modified:**
- `frontend/src/lib/schemas.ts`

### Task 2: Add model selector dropdown to InstrumentSetupForm
**Status:** ✅ Complete
**Commit:** `108358f`

- Imported shadcn/ui Select components and MODEL_PROVIDER_OPTIONS
- Added model provider dropdown as FIRST visible form field (before construct_name)
- Included helpful description: "Choose Claude for smart model allocation (Opus for validation, Sonnet for other agents) or OpenAI as fallback"
- Updated localStorage persistence to include model_provider field in form reset logic
- Follows existing shadcn/ui component patterns for consistent styling
- Build successful with no TypeScript errors

**Files modified:**
- `frontend/src/components/InstrumentSetupForm.tsx`

### Task 3: Add cost tracking display to EvidenceAuditPanel
**Status:** ✅ Complete
**Commit:** `dced061`

- Extended `AuditMetadata` interface with optional cost fields: `opus_cost`, `sonnet_cost`, `openai_cost`, `total_cost`
- Added cost breakdown section in `EvidenceAuditPanel` after Run summary section
- Conditional rendering: displays only when `opus_cost` and `total_cost` are defined
- Shows only models with non-zero costs (no $0.00 lines)
- Formatted as USD with 2 decimal places ($X.XX)
- Positioned in InsetPanel following existing design patterns
- Gracefully handles missing fields (works before backend implements cost tracking)

**Files modified:**
- `frontend/src/lib/types.ts`
- `frontend/src/components/EvidenceAuditPanel.tsx`

## Verification Results

All verification checks passed:

1. ✅ TypeScript compilation successful after each task
2. ✅ Frontend builds without errors (`npm run build`)
3. ✅ Model provider selector displayed as first field in form
4. ✅ Cost display gracefully handles missing metadata
5. ✅ UI components match existing shadcn/ui patterns

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Issue] ResultsSummaryPanel component doesn't exist**
- **Found during:** Task 3
- **Issue:** Plan references `ResultsSummaryPanel.tsx` but this component doesn't exist in the codebase. The actual component displaying audit metadata is `EvidenceAuditPanel.tsx`
- **Fix:** Added cost breakdown display to `EvidenceAuditPanel` instead of creating a new component. This is the logical location since it already displays audit trail information and follows the pattern of consolidated metadata display
- **Files modified:** `frontend/src/components/EvidenceAuditPanel.tsx`, `frontend/src/lib/types.ts`
- **Commit:** `dced061`

## Key Decisions

1. **Model provider as first field:** Positioned `model_provider` as the first field in both the schema definition and the visible form UI. This honors the user specification in 03-CONTEXT.md: "Location: Top of InstrumentSetupForm.tsx (first field before construct name)". High visibility ensures users consciously choose their provider.

2. **Cost display in audit panel:** Added cost breakdown to `EvidenceAuditPanel` rather than creating a new `ResultsSummaryPanel` component. The audit panel already serves as the consolidated metadata display location, making this a natural extension rather than fragmenting related information across multiple panels.

3. **Conditional cost rendering:** Used conditional rendering (`audit.opus_cost !== undefined && audit.total_cost !== undefined`) to only display the cost section when data is available. This ensures the UI works gracefully before the backend implements cost tracking in Plan 03-03, preventing empty or misleading displays.

4. **Zero-cost suppression:** Only display cost lines for models with non-zero costs. This prevents clutter and focuses user attention on actual spending rather than showing "$0.00" for unused models.

## Impact Assessment

### User Experience
- ✅ Users can now select between Claude (default) and OpenAI providers
- ✅ Selection persists across sessions via localStorage
- ✅ Cost transparency after generation completes
- ✅ No breaking changes to existing functionality

### Technical Debt
- None introduced
- Clean separation between UI and backend (cost fields optional)
- Follows existing patterns throughout

### Dependencies
- **Blocks:** None
- **Blocked by:** Backend cost tracking implementation (Plan 03-03) for cost display to show actual data
- **Enables:** User control over LLM provider selection immediately; cost display ready for backend integration

## Next Steps

1. **Plan 03-03:** Backend implements cost tracking by adding opus_cost, sonnet_cost, openai_cost, and total_cost fields to AuditMetadata. Once complete, the cost breakdown will automatically display with real data.

2. **Plan 03-04 (if exists):** Wire up model_provider selection to backend API request. Currently the UI captures user preference but doesn't yet send it to the backend.

## Self-Check

### Files Created
None - all modifications to existing files

### Files Modified
✅ FOUND: frontend/src/lib/schemas.ts (model_provider field, MODEL_PROVIDER_OPTIONS)
✅ FOUND: frontend/src/components/InstrumentSetupForm.tsx (model selector dropdown)
✅ FOUND: frontend/src/lib/types.ts (cost fields in AuditMetadata)
✅ FOUND: frontend/src/components/EvidenceAuditPanel.tsx (cost breakdown display)

### Commits
✅ FOUND: 6c7b455 (Task 1 - schema changes)
✅ FOUND: 108358f (Task 2 - model selector UI)
✅ FOUND: dced061 (Task 3 - cost display)

## Self-Check: PASSED

All claimed files exist with expected modifications. All commits present in git history. Build succeeds. Ready for state updates and final commit.
