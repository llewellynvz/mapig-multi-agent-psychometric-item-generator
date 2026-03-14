# Phase 7: Foundation & Infrastructure - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Schema extensions (CorrelationMatrix, ComparisonInstrument, CrossConstructComparison), LLM factory upgrade for GPT-5.2 reasoning models, and analytics node placeholders in the graph builder. Existing v1.1 generation workflow must remain fully functional. No UI changes, no real analytics logic — pure infrastructure scaffolding for Phases 8-10.

</domain>

<decisions>
## Implementation Decisions

### Correlation data model
- Rich cells: each CorrelationCell stores correlation value, confidence interval (ci_low, ci_high), and item pair reference (item_i_index, item_j_index)
- Flat list of CorrelationCell objects (not 2D nested array) — N*(N-1)/2 entries for upper-triangular matrix
- Aggregate metrics embedded directly in CorrelationMatrix type: cronbachs_alpha, mean_inter_item_correlation, internal_consistency_flag
- Disclaimer field embedded in CorrelationMatrix schema, defaulting to "LLM-estimated, not empirically validated" — enforces CORR-05 at data layer

### GPT-5.2 reasoning integration
- reasoning_effort hardcoded to "high" for GPT-5.2 analytics tasks — not user-configurable
- GPT-5.2 used for analytics agents (correlation, comparison, cross-construct); item writer stays Claude Sonnet, reviewers/validator stay Claude (existing smart allocation preserved)
- New gpt52_tokens_used counter in GraphState alongside existing opus/sonnet/openai/chatgpt counters
- Track reasoning_tokens vs output_tokens separately for GPT-5.2 — enables GPT-05 requirement (post-run audit) without refactoring later

### Analytics graph topology
- Analytics placeholder nodes sit after finalize_node, before END (sequential chain)
- Three separate nodes: correlation_node, comparison_node, cross_construct_node — maps 1:1 to Phases 8-9
- Sequential execution for Phase 7 (no-op placeholders don't need parallelism); Phase 10 converts to parallel Send API
- Analytics nodes emit SSE node_start/complete events consistent with existing progress UX

### Export backward compatibility
- New FinalOutput fields (correlation_matrix, comparison_instruments, cross_construct_analysis) use Optional with None defaults — same proven pattern from Phase 3.1
- Correlation CSV export as separate file (correlation_matrix.csv) alongside items.csv — matrix data doesn't fit item-per-row format
- JSON export includes full CorrelationMatrix object with all cells, aggregates, and disclaimer
- TypeScript types in src/lib/types.ts updated in Phase 7 to match backend schema types — keeps frontend type-safe

### Claude's Discretion
- Exact field names and Pydantic model structure for ComparisonInstrument and CrossConstructComparison types
- LLM factory caching strategy for GPT-5.2 (lru_cache adjustment for reasoning_effort parameter)
- No-op implementation details for analytics node placeholders
- SSE event naming conventions for analytics nodes
- Token tracking data structure for reasoning_tokens separation

</decisions>

<specifics>
## Specific Ideas

- "Reasoning should be set as a default to High! Should not be configured. Should be hardcoded in the prompt" — user is firm on no reasoning_effort configurability
- GPT-5.2 should be default for all agents EXCEPT item writer and reviewers where Claude is currently the default
- Follow Phase 3.1 precedent for backward-compatible schema extension (Optional fields with None defaults)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GraphState` (TypedDict, total=False): Extensible with new optional keys — analytics fields slot in naturally
- `FinalOutput` schema: Already extended once in Phase 3.1 with Optional fields — proven pattern
- `_accumulate_tokens()` in graph.py: Token accumulation pattern ready to extend for gpt52_tokens_used
- `get_chat_model_for_agent()` in llm_factory.py: Agent-based routing already implemented — GPT-5.2 analytics routing follows same pattern
- `step()` context manager: Handles SSE event emission — analytics nodes can use it directly
- `build_graph()` node registration pattern: `builder.add_node` + `builder.add_edge` — placeholders follow identically

### Established Patterns
- `ConfigDict(extra="forbid")` on all Pydantic models — new types must follow
- `@lru_cache` on model factory functions — needs adjustment for GPT-5.2 reasoning_effort parameter
- Token tracking via per-model counters in GraphState (opus_tokens_used, sonnet_tokens_used, etc.)
- Cost calculation in finalize_node using blended per-1M-token rates
- Agent I/O wrappers (e.g., ItemWriterResponse) for type-safe graph node returns

### Integration Points
- `finalize_node` → currently connects to `END` — analytics nodes insert between finalize and END
- `FinalOutput` consumed by frontend `src/lib/types.ts` — TypeScript types must mirror new fields
- SSE event stream in `main.py` event_generator — new node events propagate automatically via step() context manager
- Export logic in frontend components — CSV/JSON/Markdown renderers need to handle Optional analytics fields

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-foundation-infrastructure*
*Context gathered: 2026-03-14*
