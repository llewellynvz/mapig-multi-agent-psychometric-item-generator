---
phase: 08-synthetic-correlation-analysis
plan: 02
subsystem: frontend
tags: [ui, visualization, correlation, heatmap, export]
dependency_graph:
  requires: [08-01]
  provides: [correlation-ui, heatmap-visualization, correlation-export]
  affects: [GeneratedItemsTable, results-view]
tech_stack:
  added: [visx/heatmap, visx/scale, visx/tooltip, visx/group, radix-ui/react-popover]
  patterns: [collapsible-panel, hover-tooltip, click-popover, csv-export, json-export]
key_files:
  created:
    - src/components/CorrelationPanel.tsx
    - src/components/CorrelationHeatmap.tsx
    - src/components/CorrelationSummaryCard.tsx
    - src/components/CorrelationTooltip.tsx
    - src/lib/export-correlation.ts
  modified:
    - src/components/GeneratedItemsTable.tsx
    - package.json
    - package-lock.json
decisions:
  - title: Psynalytics brand color scale for heatmap
    rationale: Use teal-white-lime gradient (#008da1 → #ffffff → #a7d12b) instead of academic blue-white-red to maintain brand consistency and avoid red-green colorblind issues
  - title: Collapsed by default for correlation panel
    rationale: Reduce initial cognitive load, allow users to expand when needed, follows progressive disclosure pattern
  - title: Export buttons inside panel context
    rationale: Correlation export is domain-specific, not part of main export dropdown; keeps exports contextual to correlation data
  - title: Custom className-based Pill styling
    rationale: Pill component doesn't support variant prop; use Tailwind classes for green (pass/optimal) and amber (warning) status indicators
  - title: Auto-approved human verification checkpoint
    rationale: Auto-chain mode active, UI components compile correctly, visual verification deferred to integration testing
metrics:
  duration: 260s
  completed: 2026-03-14T11:47:37Z
---

# Phase 08 Plan 02: Correlation Heatmap UI Summary

**One-liner:** Interactive visx heatmap with Psynalytics brand colors (teal-white-lime), collapsible panel, quality metrics card with McDonald's omega and mean inter-item correlation, hover tooltips, click popovers, and CSV/JSON exports.

## What Was Built

Complete frontend visualization for correlation matrix data computed by Plan 08-01:

1. **CorrelationHeatmap Component**: visx HeatmapRect implementation with:
   - Psynalytics brand color scale: teal (negative) → white (zero) → lime (positive)
   - Responsive cell sizing (scales down for large item sets)
   - Axis labels with 45° rotation on top axis
   - Color legend bar showing -1.0 to +1.0 gradient
   - Hover and click event handlers

2. **CorrelationTooltip Component**: Hover overlay displaying:
   - Correlation value (r) with 3 decimal precision
   - 95% confidence interval range
   - Item pair indices and truncated item text (30 chars)
   - Dark themed, positioned near cursor

3. **CorrelationSummaryCard Component**: Quality metrics display with:
   - McDonald's Omega with pass/warning pill (≥0.70 = pass)
   - Mean inter-item correlation with optimal/low/high pill (0.15-0.50 = optimal)
   - Internal consistency assessment text
   - Educational one-line descriptions for each metric
   - LLM-estimated disclaimer at bottom

4. **CorrelationPanel Component**: Collapsible container managing:
   - Expand/collapse toggle with chevron icons (collapsed by default)
   - Integration of heatmap, summary card, and tooltips
   - Click popover with full item text and correlation details
   - "Export CSV" button (downloads square matrix + CI file)
   - "Export JSON" button (downloads full CorrelationMatrix with disclaimer)

5. **export-correlation.ts Library**: Export functions including:
   - `exportCorrelationMatrixToCsv()`: Square matrix with metadata header, truncated column/row labels, UTF-8 BOM
   - `exportConfidenceIntervalsToCsv()`: Separate CI file with Item_i, Item_j, r, CI_Low, CI_High
   - `exportCorrelationMatrixToJson()`: Pretty-printed JSON with disclaimer field
   - `truncateItemText()`: Helper for 30-char truncation with ellipsis

6. **GeneratedItemsTable Integration**: Wired CorrelationPanel after QualityChecksPanel
   - Conditionally renders when `fullOutput.correlation_matrix` exists
   - Passes matrix data, item texts array, and construct name
   - Backward compatible (no render when correlation_matrix is null)

## Deviations from Plan

### Auto-approved Checkpoint

**Task 3 (checkpoint:human-verify) was auto-approved** because auto-chain mode is active (`config.json` has `workflow._auto_chain_active: true`).

- **What was built:** Complete correlation visualization with 5 components, export functions, and GeneratedItemsTable integration
- **Expected verification:** Manual visual check of heatmap colors, tooltips, exports, and dark mode
- **Auto-approval rationale:** TypeScript compilation passes cleanly, components follow established patterns (QualityChecksPanel, existing export functions), visual verification deferred to integration testing

**No other deviations** — plan executed exactly as written.

## Commits

| Task | Commit | Description | Files |
|------|--------|-------------|-------|
| 1 | `0276255` | feat(08-02): add correlation visualization components | 7 files (5 new components + package.json updates) |
| 2 | `9aeb2ef` | feat(08-02): wire CorrelationPanel into GeneratedItemsTable | src/components/GeneratedItemsTable.tsx |

## Key Decisions

**1. Psynalytics brand color scale**
- **Decision:** Use teal-white-lime gradient instead of standard blue-white-red
- **Rationale:** Maintains brand consistency, avoids red-green colorblind accessibility issues
- **Implementation:** `scaleLinear<string>({ domain: [-1, 0, 1], range: ['#008da1', '#ffffff', '#a7d12b'] })`

**2. Collapsed by default**
- **Decision:** CorrelationPanel starts collapsed, user expands on demand
- **Rationale:** Reduces initial cognitive load, follows progressive disclosure UX pattern
- **Implementation:** `useState(false)` for `isExpanded`, chevron indicates state

**3. Contextual export buttons**
- **Decision:** Export CSV/JSON buttons inside correlation panel, not in main export dropdown
- **Rationale:** Correlation data is domain-specific, contextual placement improves UX
- **Implementation:** SecondaryButton components in CardContent, trigger separate download functions

**4. Custom Pill styling**
- **Decision:** Use className with Tailwind for status colors instead of variant prop
- **Rationale:** Pill component doesn't support `variant` prop (simple wrapper), custom colors needed for pass/warning
- **Implementation:** `bg-green-500/20 text-green-400 border-green-500/40` for pass, `bg-amber-500/20 text-amber-400 border-amber-500/40` for warning

## Technical Highlights

**visx Integration:**
- HeatmapRect with custom color scale and gap spacing
- Responsive cell sizing: `Math.min(40, availableWidth / itemCount)`
- SVG axis labels with rotation transform for top labels

**Export Pattern:**
- UTF-8 BOM (`\uFEFF`) for Excel compatibility
- RFC 4180 CSV escaping via `escapeCsvField()`
- Square matrix reconstruction from flat cells list (symmetric lookup)
- Separate CI export for detailed analysis

**State Management:**
- Tooltip state with `{ visible, x, y, cell }` object
- Popover controlled state with Radix `open` and `onOpenChange`
- Cell lookup by indices with diagonal handling (i === j → 1.0)

**Dark Mode:**
- Heatmap stroke uses `var(--border)` CSS variable
- Tooltip and popover use dark slate backgrounds (#0b2a34, slate-900)
- Color legend maintains readability in both themes

## Verification

**Automated:**
- ✅ TypeScript compilation: `npm run type-check` passes (no errors in correlation components)
- ✅ Dependency installation: visx and Radix packages installed successfully
- ✅ Import validation: All components import and integrate without module resolution errors

**Manual (Auto-approved in auto-chain mode):**
- Deferred: Visual heatmap color verification (teal-white-lime gradient)
- Deferred: Tooltip hover interaction testing
- Deferred: Click popover detail display
- Deferred: CSV export file validation (square matrix format)
- Deferred: JSON export schema validation (includes disclaimer field)
- Deferred: Dark mode readability check

## Impact

**User Experience:**
- Users can now visualize correlation patterns at a glance
- Quality metrics (omega, mean r) provide psychometric context
- Export functions enable external analysis in Excel, R, Python
- Tooltips and popovers reduce need to export data for simple inspection

**Developer Experience:**
- visx provides robust data visualization primitives
- Radix Popover ensures accessible click interactions
- Export functions follow established RFC 4180 patterns
- Components are isolated and testable

**Next Steps:**
- Plan 08-03 will handle any visual refinements or integration issues discovered during testing
- Correlation panel is ready for Phase 9 (comparison instruments) and Phase 10 (optimization)

## Self-Check: PASSED

**Created files verified:**
```bash
✅ src/components/CorrelationPanel.tsx
✅ src/components/CorrelationHeatmap.tsx
✅ src/components/CorrelationSummaryCard.tsx
✅ src/components/CorrelationTooltip.tsx
✅ src/lib/export-correlation.ts
```

**Modified files verified:**
```bash
✅ src/components/GeneratedItemsTable.tsx (CorrelationPanel import and render)
✅ package.json (visx and Radix dependencies added)
```

**Commits verified:**
```bash
✅ 0276255: feat(08-02): add correlation visualization components
✅ 9aeb2ef: feat(08-02): wire CorrelationPanel into GeneratedItemsTable
```

All files exist, commits are in git history, TypeScript compiles cleanly.

---

**Execution time:** 4 minutes 20 seconds
**Auto-approved checkpoint:** Task 3 (human-verify) auto-approved due to active auto-chain mode
**Status:** ✅ Complete — Correlation visualization ready for integration testing
