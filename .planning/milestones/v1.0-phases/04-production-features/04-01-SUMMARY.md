---
phase: 04-production-features
plan: 01
subsystem: frontend-export
tags:
  - export
  - csv
  - json
  - markdown
  - user-experience
  - data-portability
dependency_graph:
  requires:
    - Phase 03.1: FinalOutput schema with user_request and review feedback fields
    - Phase 01: Validation scores (4 dimensions)
  provides:
    - Multi-format export (CSV, JSON, Markdown)
    - RFC 4180-compliant CSV with UTF-8 BOM
    - Complete metadata export (validation, review feedback, audit trail)
    - localStorage format persistence
  affects:
    - GeneratedItemsTable UI (CardFooter added)
tech_stack:
  added:
    - Vitest testing framework
    - React Testing Library
    - jsdom polyfills for Radix UI
  patterns:
    - TDD RED-GREEN-REFACTOR methodology
    - RFC 4180 CSV escaping
    - Client-side file download with Blob API
    - localStorage for user preferences
key_files:
  created:
    - frontend/vitest.config.ts (Vitest configuration)
    - frontend/src/test/setup.ts (test setup with jsdom polyfills)
    - frontend/src/lib/export.ts (export formatting functions)
    - frontend/src/lib/__tests__/export.test.ts (17 unit tests)
    - frontend/src/components/__tests__/GeneratedItemsTable.test.tsx (6 integration tests)
  modified:
    - frontend/src/lib/utils.ts (added sanitizeFilename)
    - frontend/src/components/GeneratedItemsTable.tsx (added export UI)
    - frontend/package.json (added test dependencies and script)
decisions:
  - Use TDD methodology with RED-GREEN-REFACTOR for all implementation tasks
  - Remove old Download CSV and Download JSON buttons in favor of unified export system with format selector
  - Place export controls in CardFooter (not CardHeader) for clearer UI separation between copy and download actions
  - Use RFC 4180 CSV formatting with UTF-8 BOM for Excel compatibility
  - Include all metadata in exports (validation scores, review feedback, audit trail, user_request)
  - Use `any` type for test mocks to avoid complex Vitest type conflicts
metrics:
  duration_minutes: 8
  tasks_completed: 3
  tests_written: 23
  tests_passing: 23
  commits: 5
  files_created: 5
  files_modified: 3
  lines_added: 650+
  completed_at: "2026-03-08T23:06:30Z"
---

# Phase 04 Plan 01: Multi-Format Export Functionality Summary

**One-liner:** Client-side export system with CSV (RFC 4180, UTF-8 BOM), JSON, and Markdown formats including full metadata (validation scores, review feedback, audit trail) from Phase 3.1 FinalOutput schema enhancements.

## Objective

Added multi-format export functionality to the Results UI, enabling users to download complete item sets with full metadata in three formats: CSV for analysis in Excel/R/SPSS, JSON for programmatic access, and Markdown for stakeholder documentation.

## What Was Built

### Task 0: Test Infrastructure Setup
- Installed Vitest, React Testing Library, jsdom test dependencies
- Created Vitest configuration with React plugin and jsdom environment
- Set up test directory structure with `__tests__` folders
- Added jsdom polyfills for Radix UI components (hasPointerCapture, releasePointerCapture, setPointerCapture, scrollIntoView)
- Scaffolded test files for Wave 1 tasks
- **Verification:** 2 scaffold tests passing

### Task 1: Export Formatting Functions (TDD)
**RED Phase:**
- Wrote 17 failing tests covering:
  - CSV UTF-8 BOM and RFC 4180 escaping (quotes, commas, newlines)
  - CSV metadata rows from user_request (construct, definition, population, constraints)
  - CSV review_feedback column with filtered comments
  - JSON structure matching FinalOutput with Phase 3.1 fields
  - Markdown sections (definition, items, validation table, review feedback, audit trail)
  - Filename sanitization and timestamp format (YYYYMMDD-HHMMSS)
- **Commit:** test(04-01): add failing tests for export functions (TDD RED)

**GREEN Phase:**
- Implemented `exportToCsv`: UTF-8 BOM, metadata rows, RFC 4180 field escaping, review_feedback column
- Implemented `exportToJson`: 2-space formatted JSON with full FinalOutput structure
- Implemented `exportToMarkdown`: 6 sections including construct definition, items, validation scores table, review feedback (3 subsections), audit trail
- Implemented `generateFilename`: sanitized construct name + YYYYMMDD-HHMMSS timestamp
- Implemented `sanitizeFilename` utility: lowercase, special char replacement, 50 char limit, "untitled" fallback
- **Verification:** All 17 tests passing
- **Commit:** feat(04-01): implement export functions with RFC 4180 compliance (TDD GREEN)

### Task 2: Export UI Integration (TDD)
**RED Phase:**
- Wrote 6 failing tests covering:
  - Format selector renders with 3 options (CSV, JSON, Markdown)
  - Download button triggers download with selected format
  - localStorage persistence of format preference
  - Format loads from localStorage on mount
  - Download button disabled when fullOutput is null
  - Item count summary displays correctly
- **Commit:** test(04-01): add failing tests for export UI (TDD RED)

**GREEN Phase:**
- Added CardFooter to GeneratedItemsTable with:
  - Format selector dropdown (CSV, JSON, Markdown)
  - Download button with Download icon from lucide-react
  - Item count summary with validation stats
- Implemented `handleFormatChange`: updates state and localStorage
- Implemented `handleDownload`: format-aware content generation, blob creation, file download, resource cleanup
- Removed old Download CSV and Download JSON buttons from CardHeader (replaced by unified system)
- Added localStorage persistence with SSR guard and error handling
- **Verification:** All 6 tests passing
- **Commit:** feat(04-01): add export UI to GeneratedItemsTable (TDD GREEN)

**Type Fix:**
- Resolved TypeScript type conflicts in test mocks by using `any` type for vi.fn declarations
- **Commit:** fix(04-01): resolve TypeScript type errors in test mocks

## Implementation Details

### CSV Export Features
- **UTF-8 BOM:** Ensures proper character display in Excel
- **Metadata rows:** Construct name, definition, target population, constraints from `user_request`
- **RFC 4180 compliance:** Fields with quotes/commas/newlines wrapped in quotes, internal quotes doubled
- **Columns:** item_number, item_text, rationale, validation_score, validation_accept, attempt_count, dimension_scores (JSON), evidence_citations (semicolon-separated), review_feedback (JSON array)
- **Windows line endings:** \r\n for Excel compatibility

### JSON Export Features
- Full FinalOutput structure with 2-space indentation
- Includes Phase 3.1 fields: user_request, linguistic_feedback, bias_feedback, content_feedback
- All validation results and audit metadata preserved

### Markdown Export Features
- **Section 1:** Title and timestamp
- **Section 2:** Construct Definition (from user_request)
- **Section 3:** Generated Items (text, rationale, evidence citations)
- **Section 4:** Validation Scores (table with all 4 dimensions)
- **Section 5:** Review Feedback (3 subsections: Linguistic, Bias, Content)
- **Section 6:** Audit Trail (thread_id, run_id, iterations, validation attempts/failures)

### UI Enhancements
- Format selector persists preference across page refreshes
- Download button disabled when no data available
- Item count summary includes validation stats (rejected count, regeneration count)
- Clean separation: Copy actions in CardHeader, Download action in CardFooter

## Verification Results

### Automated Tests
- **Total tests:** 23 (17 export function tests + 6 UI integration tests)
- **Pass rate:** 100% (23/23)
- **Test coverage:**
  - CSV: UTF-8 BOM, metadata rows, RFC 4180 escaping, review feedback column
  - JSON: structure validation, indentation
  - Markdown: 6 sections, validation table, review feedback subsections
  - Filename: sanitization, timestamp format
  - UI: format selector, download trigger, localStorage persistence, disabled state

### TypeScript Compilation
- No type errors
- All exports properly typed with FinalOutput interface

### Success Criteria Met
- [x] Download button in GeneratedItemsTable CardFooter with format selector (3 options)
- [x] CSV export with UTF-8 BOM, metadata rows, review_feedback column, RFC 4180 compliance
- [x] JSON export matches FinalOutput structure with Phase 3.1 fields
- [x] Markdown export with 6 sections (definition, items, validation table, review feedback, audit trail)
- [x] File naming: `{construct-name}_{YYYYMMDD-HHMMSS}.{ext}`
- [x] Format preference persists via localStorage
- [x] All exports include validation scores (4 dimensions + reasoning + attempt count)
- [x] All exports include review feedback from linguistic, bias, and content reviewers
- [x] All exports include user_request metadata (construct_definition, target_population, constraints)
- [x] All exports include audit trail (thread_id, run_id, iterations, validation attempts/failures)
- [x] Frontend build completes with no TypeScript errors
- [x] Download button disabled when fullOutput is null
- [x] All automated tests pass (23/23)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical] Missing Vitest React plugin**
- **Found during:** Task 0
- **Issue:** Vitest configuration referenced @vitejs/plugin-react but package wasn't installed, causing "MODULE_NOT_FOUND" error on test run
- **Fix:** Installed @vitejs/plugin-react as dev dependency
- **Files modified:** frontend/package.json
- **Commit:** 97d1241 (included in Task 0 commit)
- **Justification:** Required for Vitest to work with React components; blocking issue for test execution

**2. [Rule 2 - Critical] Missing jsdom polyfills for Radix UI**
- **Found during:** Task 2 GREEN phase
- **Issue:** Radix UI Select component calls `hasPointerCapture`, `setPointerCapture`, `releasePointerCapture`, `scrollIntoView` methods not implemented in jsdom, causing test failures
- **Fix:** Added polyfills in test setup file
- **Files modified:** frontend/src/test/setup.ts
- **Commit:** ca495cc (included in Task 2 commit)
- **Justification:** Essential for Radix UI components to work in jsdom test environment; without these, all Select-related tests fail

**3. [Rule 1 - Bug] Test query finding multiple elements**
- **Found during:** Task 2 GREEN phase
- **Issue:** `getByText('CSV')` found multiple elements (one in trigger, one in dropdown), causing test failure
- **Fix:** Changed to `getAllByText` and verified length > 0
- **Files modified:** frontend/src/components/__tests__/GeneratedItemsTable.test.tsx
- **Commit:** ca495cc (included in Task 2 commit)
- **Justification:** Test implementation bug; expected behavior that format name appears in both trigger and menu

**4. [Rule 1 - Bug] TypeScript type errors in test mocks**
- **Found during:** Post-implementation type-check
- **Issue:** Complex Vitest mock types incompatible with URL API types (`createObjectURL`, `revokeObjectURL`)
- **Fix:** Used `any` type for mock declarations to avoid type conflicts
- **Files modified:** frontend/src/components/__tests__/GeneratedItemsTable.test.tsx
- **Commit:** e5357c5
- **Justification:** Type system limitation; tests work correctly at runtime, type annotations were causing compilation errors

## Technical Decisions

### TDD Methodology
- Followed strict RED-GREEN-REFACTOR cycle for both tasks
- RED: Write failing tests first, commit
- GREEN: Implement minimal code to pass tests, commit
- REFACTOR: No refactoring needed (code was clean on first pass)
- **Benefit:** Caught edge cases early (CSV escaping, multiple text matches in tests)

### RFC 4180 CSV Compliance
- Implemented proper field escaping: wrap in quotes if contains quote/comma/newline, double internal quotes
- Added UTF-8 BOM (\uFEFF) for Excel compatibility
- Used Windows line endings (\r\n)
- **Benefit:** CSV files open correctly in Excel without encoding issues

### Unified Export System
- Replaced two separate download buttons with one format selector + download button
- **Benefit:** Cleaner UI, easier to extend (add new formats like PDF in future), consistent download behavior

### Client-side Resource Management
- Used `URL.revokeObjectURL()` after download to clean up memory
- **Benefit:** Prevents memory leaks in long sessions with multiple downloads

## Files Modified/Created

### Created (5 files, ~650+ lines)
1. **frontend/vitest.config.ts** (17 lines)
   - Vitest configuration with React plugin, jsdom environment, path aliases
2. **frontend/src/test/setup.ts** (22 lines)
   - Test setup with jest-dom matchers and jsdom polyfills
3. **frontend/src/lib/export.ts** (275 lines)
   - `exportToCsv`, `exportToJson`, `exportToMarkdown`, `generateFilename`, `escapeCsvField` helper
4. **frontend/src/lib/__tests__/export.test.ts** (256 lines)
   - 17 unit tests for export functions
5. **frontend/src/components/__tests__/GeneratedItemsTable.test.tsx** (197 lines)
   - 6 integration tests for export UI

### Modified (3 files)
1. **frontend/src/lib/utils.ts** (+21 lines)
   - Added `sanitizeFilename` utility function
2. **frontend/src/components/GeneratedItemsTable.tsx** (+64 lines, -41 lines removed)
   - Added export UI (CardFooter, format selector, download handler)
   - Removed old download buttons
   - Added localStorage persistence
3. **frontend/package.json** (+4 dependencies, +1 script)
   - Added vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom, @vitejs/plugin-react
   - Added "test" script

## Testing Coverage

### Export Function Tests (17 tests)
- CSV: UTF-8 BOM, metadata rows, quote escaping, comma escaping, review feedback column
- JSON: FinalOutput structure, 2-space indentation
- Markdown: all sections present, validation dimensions table, review feedback subsections, user_request data
- Filename: sanitization, timestamp format, edge cases (empty strings, special chars)

### UI Integration Tests (6 tests)
- Format selector renders with 3 options
- Download button triggers download with selected format
- localStorage persistence on format change
- localStorage loading on component mount
- Download button disabled when fullOutput is null
- Item count summary displays correctly

## Performance Metrics

- **Duration:** 8 minutes
- **Tasks completed:** 3/3 (100%)
- **Tests written:** 23
- **Tests passing:** 23 (100%)
- **Commits:** 5 (1 setup, 2 TDD RED, 2 TDD GREEN, 1 type fix)
- **Files created:** 5
- **Files modified:** 3
- **Lines added:** ~650+

## Dependencies Satisfied

### Phase 03.1 FinalOutput Schema Enhancements
- Successfully utilized `user_request` field for CSV metadata rows and Markdown construct definition
- Successfully utilized `linguistic_feedback`, `bias_feedback`, `content_feedback` arrays for review feedback export
- All exports include complete metadata without breaking changes to existing consumers

### Phase 01 Validation Scores
- All 4 validation dimensions (correspondence, distinctiveness, clarity, specificity) exported in CSV, Markdown, and JSON
- Dimension scores include reasoning, score value, and attempt count

## Integration Points

### Upstream Dependencies
- **Phase 03.1:** FinalOutput schema with optional user_request and feedback arrays
- **Phase 01:** ItemValidation with dimension_scores array
- **shadcn/ui:** Select, CardFooter, Download icon components

### Downstream Consumers
- Users exporting data for Excel/R/SPSS analysis (CSV)
- Users exporting data for programmatic processing (JSON)
- Users exporting data for stakeholder documentation (Markdown)
- Future phases may reference export patterns for other data types

## Next Steps

No blockers or issues. Plan complete. Ready for manual verification and integration testing:

1. Start dev server: `cd frontend && npm run dev`
2. Generate items with any construct
3. Verify format selector shows CSV, JSON, Markdown options
4. Test CSV export: verify UTF-8 characters, metadata rows, review feedback column in Excel
5. Test JSON export: verify structure, user_request, feedback arrays
6. Test Markdown export: verify 6 sections, validation table, review feedback subsections
7. Test localStorage: change format, refresh page, verify format persists
8. Test disabled state: verify download button disabled when no data

## Lessons Learned

1. **TDD RED-GREEN-REFACTOR is highly effective for UI work** - Caught edge cases early (CSV escaping, multiple text matches)
2. **jsdom requires polyfills for modern web APIs** - Radix UI components need pointer capture and scroll methods
3. **RFC 4180 CSV is critical for Excel compatibility** - UTF-8 BOM and proper escaping prevent encoding issues
4. **Type-only test issues can be resolved with pragmatic `any` usage** - Tests work correctly, type system limitations shouldn't block progress
5. **Phase 3.1 schema enhancements were perfectly timed** - Export functionality would be incomplete without user_request and feedback fields

---

**Status:** ✅ Complete - All tasks executed, all tests passing, TypeScript compilation succeeds, ready for manual verification
