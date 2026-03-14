# Phase 9: Dynamic Instrument Comparison - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

System dynamically discovers validated comparison instruments from academic literature and assesses convergent/discriminant validity without copyright infringement. Covers instrument search via Perplexity Academic, hybrid fallback to hardcoded defaults, convergent validity (same-construct instruments), discriminant validity (related-but-distinct constructs), copyright safeguards (metadata only, publisher blocklist), plagiarism detection (cosine similarity flagging), and comparison display panel in results UI. GPT-5.2 reasoning model configuration and parallel analytics execution are Phase 10 scope.

</domain>

<decisions>
## Implementation Decisions

### Instrument discovery strategy
- Retrieve exactly 2 instruments per generation: 1 convergent (same construct) and 1 discriminant (related-but-distinct construct)
- Search-first approach: try Perplexity Academic search, fall back to hardcoded defaults if search fails (no credits, timeout, no results)
- Hardcoded defaults span broad psychological domains (personality, clinical, organizational, social, cognitive) — not just org psych
- Instruments shown in results panel only after generation completes — no intermediate SSE events for discovery
- Existing Web Surfer Perplexity integration extended with instrument-specific query synthesis

### Comparison panel layout
- Single collapsible card (own section below CorrelationPanel, separate from it)
- Collapsed by default, matching Phase 8 progressive disclosure pattern
- Card has two sections: convergent instrument + discriminant instrument side-by-side
- Essential metadata per instrument: name, author + year, construct measured, APA citation, one-line similarity rationale
- Convergent validity shown as numeric score (0-1) with pass/warning threshold — no narrative rationale
- No dedicated export button — comparison data included in existing full JSON export

### Cross-construct display
- Discriminant instrument displayed inline in the comparison card (not a separate panel)
- Warning badge (orange pill) when estimated correlation > 0.85 with related construct: "High overlap detected (r = X.XX)"
- One-line educational explanations for convergent and discriminant validity concepts (tooltip or subtitle)
- Dual-direction scoring (A→B and B→A) averaged — show only the averaged result, individual directions are implementation detail
- All validity flags are advisory/informational only — no blocking actions, consistent with Phase 8 pattern

### Copyright safeguards
- Hardcoded publisher blocklist for Perplexity searches: major test publisher domains (pearson.com, parinc.com, mhs.com, wpspublish.com, etc.)
- Metadata-only storage enforced at schema level (ComparisonInstrument has no item_text field — Phase 7 schema)
- Small disclaimer footer in comparison card: "Only instrument metadata is stored. No copyrighted item text is retrieved or displayed."

### Plagiarism detection
- Per-item warning badges on flagged items in results table when cosine similarity > 0.85 to retrieved instrument items
- Red/orange warning pill: "Potential similarity to [Instrument] item"
- Informational only — no auto-removal, no revision suggestions, no blocking
- Consistent with Phase 8 "advisory, not blocking" philosophy for LLM-estimated metrics

### Claude's Discretion
- Perplexity Academic query construction strategy for instrument discovery
- Cosine similarity implementation approach (LLM-based or sklearn)
- Hardcoded default instrument selection (specific scales per domain)
- Comparison score threshold values for pass/warning
- Convergent/discriminant scoring prompt engineering
- Publisher blocklist extent (specific domains beyond the obvious ones)
- Card styling details, badge colors, tooltip content

</decisions>

<specifics>
## Specific Ideas

- User wants lean output: only 1 convergent + 1 discriminant instrument, not a large set
- Score-only convergent validity display — no narrative paragraphs, just threshold-based scoring
- No separate comparison export — data lives in the full JSON export already
- Plagiarism badges are informational flags, not action triggers

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `web_surfer.py:surf()`: Perplexity Academic integration with domain filtering — extend for instrument-specific queries
- `evaluation/item_comparison.py:_compare_single_direction()` + `_average_comparison_results()`: Dual-direction LLM-as-judge pattern for position bias mitigation
- `CorrelationPanel.tsx`: Collapsible panel pattern for analytics display below GeneratedItemsTable
- `CorrelationSummaryCard.tsx`: Summary card pattern with metrics and badges
- `Pill` / `Badge` components: Status indicators for pass/warning/error flags
- `ComparisonInstrument` Pydantic model + TypeScript type: Already defined in Phase 7 (metadata-only schema)
- `CrossConstructComparison` + `ConstructPairAnalysis` types: Already defined in Phase 7
- `comparison_node` / `cross_construct_node` placeholders in `graph.py`: Ready for real implementation
- `get_gpt52_analytics_model()`: GPT-5.2 factory with high reasoning effort for analytics
- `_accumulate_tokens()`: Token tracking pattern for GPT-5.2 reasoning tokens
- Brand CSS variables: --primary (#008da1), --accent (#a7d12b) for brand-consistent visualization

### Established Patterns
- Collapsible panels collapsed by default (Phase 8 CorrelationPanel)
- Export buttons inside panel context, not main dropdown (Phase 8)
- Educational one-line metric explanations (Phase 8 CorrelationSummaryCard)
- Advisory warnings, not blocking (Phase 8 — LLM estimates are informational)
- Optional fields with None defaults for backward compatibility (Phase 3.1 precedent)
- SSE node events via step() context manager
- ConfigDict(extra="forbid") on all Pydantic models
- Graceful analytics failure: return {} on error, FinalOutput fields stay None

### Integration Points
- `comparison_node` in graph.py: Replace no-op with instrument search + convergent validity scoring
- `cross_construct_node` in graph.py: Replace no-op with discriminant validity analysis
- `GeneratedItemsTable.tsx`: Add collapsible comparison card below CorrelationPanel
- `FinalOutput.comparison_instruments` + `FinalOutput.cross_construct_analysis`: Backend populates, frontend reads
- `web_surfer.py`: Extend with instrument-specific search queries (new function, not modifying existing surf())
- `settings.py`: Add publisher blocklist configuration
- Item results table: Add plagiarism warning badges to individual items

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-dynamic-instrument-comparison*
*Context gathered: 2026-03-14*
