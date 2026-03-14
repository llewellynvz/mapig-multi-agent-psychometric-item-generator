# Phase 8: Synthetic Correlation Analysis - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Generated item sets include LLM-estimated inter-item correlation matrices with McDonald's omega and internal consistency metrics displayed in interactive heatmap visualization. Includes correlation estimation via GPT-5.2, heatmap UI component, quality summary card, CSV/JSON export, and calibration validation in the evaluation suite. Dynamic instrument search and comparison against user-specific constructs are Phase 9 scope.

</domain>

<decisions>
## Implementation Decisions

### Heatmap design & placement
- Collapsible panel below GeneratedItemsTable, following QualityChecksPanel expand/collapse pattern
- Collapsed by default — items shown first, user expands correlation panel when ready
- Hover tooltips showing exact correlation value, CI range, and item pair text
- Click opens detail popover with full reasoning for that pair
- Brand-consistent color scale using Psynalytics palette (primary teal #008da1, accent lime #a7d12b) — not standard academic blue-white-red
- visx library for heatmap visualization (per UI-01 requirement)

### Reliability metric
- McDonald's omega (ω) replaces Cronbach's alpha as the primary reliability metric
- Phase 7 schema field `cronbachs_alpha` renamed to `mcdonalds_omega` (breaking schema change from Phase 7)
- Threshold: ω ≥ 0.70 = pass, ω < 0.70 = warning (same threshold, better metric)
- Rationale: Alpha assumes tau-equivalence (equal factor loadings) which is rarely true; omega is based on factor model and is the recommended modern alternative

### Warning & flag presentation
- Separate quality summary card below the heatmap (not a banner, not inline badges)
- Card shows: McDonald's omega value + pass/warning status, mean inter-item correlation + optimal range flag (0.15-0.50), internal consistency assessment
- Brief one-line explanations for each metric (educational, not just numbers)
- Warnings are informational only — no blocking action, no suggestions for revision
- LLM estimates are advisory — hard blocking would be overstepping given these are synthetic, not empirical

### Benchmark validation (CORR-04)
- Fixed calibration scales: 5 well-published scales with known correlation matrices selected by researcher agent during research phase
- Scales should span different psychological domains (personality, clinical, organizational, etc.)
- Must have published correlation matrices available (not just alpha values)
- Validation runs as part of evaluation suite (/evaluation framework), not per-generation
- Proves the LLM estimation method works (system calibration) — separate from Phase 9's dynamic instrument comparison
- Benchmark: r > 0.6 agreement between LLM-estimated and published correlations

### Export format
- Square matrix CSV format with item text headers (truncated), one correlation value per cell — familiar to SPSS/R users
- Confidence intervals in a separate file (not inline in the square matrix CSV)
- Export button inside the correlation panel (contextual, not in the main export dropdown)
- Disclaimer ("LLM-estimated, not empirically validated") in JSON export only, not in CSV
- JSON export includes full CorrelationMatrix object with all cells, aggregates, omega, and disclaimer

### Claude's Discretion
- Exact Psynalytics brand color gradient for heatmap (derived from primary/accent CSS variables)
- visx component architecture (HeatmapRect vs HeatmapCircle, axis labels, responsive sizing)
- LLM prompt engineering for pairwise correlation estimation (single prompt vs batched)
- CI estimation method from LLM responses
- McDonald's omega calculation approach (factor loading extraction from correlation matrix)
- Calibration scale selection criteria during research phase
- Quality summary card layout and styling details
- Hover tooltip and click popover component implementation
- CI file format (separate CSV or included in JSON only)

</decisions>

<specifics>
## Specific Ideas

- "Keep to my brand colours!" — heatmap must use Psynalytics teal/lime palette, not standard academic color schemes
- "I think we should rather use McDonald's Omega instead of Alpha" — user is firm on omega over alpha as the reliability metric
- User clarified that dynamic instrument search for benchmarking is Phase 9 scope; Phase 8 calibration is about proving the method works on fixed known scales
- Quality summary card should be educational — include brief explanations of what metrics mean

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `QualityChecksPanel` (src/components/QualityChecksPanel.tsx): Expand/collapse pattern for the correlation panel
- `SurfaceCard` / `InsetPanel` (src/components/ui/surface-card.tsx): Card components for quality summary card
- `Pill` / `Badge` (src/components/ui/pill.tsx, badge.tsx): Status indicators for pass/warning flags
- `exportToCsv()` / `exportToJson()` (src/lib/export.ts): Export function patterns to extend for correlation matrix
- `CorrelationMatrix` / `CorrelationCell` types (src/lib/types.ts): TypeScript types already defined in Phase 7
- `CorrelationMatrix` / `CorrelationCell` Pydantic models (backend/schemas.py): Backend schemas already defined
- `correlation_node` placeholder (backend/graph.py:623): No-op node ready for real implementation
- `get_gpt52_analytics_model()` (backend/agents/llm_factory.py): GPT-5.2 factory with high reasoning effort
- Brand CSS variables (src/app/globals.css): --primary (#008da1), --accent (#a7d12b), --destructive (#ef4444)

### Established Patterns
- `ConfigDict(extra="forbid")` on all Pydantic models — new types must follow
- Optional fields with None defaults for backward compatibility (Phase 3.1 precedent)
- SSE node events via `step()` context manager — correlation_node already emits events
- Token tracking via per-model counters in GraphState (gpt52_tokens_used, gpt52_reasoning_tokens)
- Evaluation framework at /evaluation with benchmark scales and 4-dimensional metrics

### Integration Points
- `correlation_node` in graph.py: Replace no-op with real correlation estimation logic
- `GeneratedItemsTable.tsx`: Add collapsible correlation panel below items
- `export.ts`: Add correlation matrix CSV export function
- `FinalOutput.correlation_matrix`: Backend populates, frontend reads from SSE stream
- `/evaluation` framework: Add correlation calibration benchmarks
- Schema migration: Rename `cronbachs_alpha` → `mcdonalds_omega` in backend/schemas.py and src/lib/types.ts

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-synthetic-correlation-analysis*
*Context gathered: 2026-03-14*
