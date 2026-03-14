# Phase 6: Comprehensive Evaluation Framework - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Build an automated evaluation suite that measures MAPIG system quality across 4 dimensions (item quality, agent performance, workflow metrics, construct validity). Use 5 benchmark constructs from published scales. AI-based comparison of generated items to published scale items. Results displayed in dashboard UI with aggregated metrics.

No changes to item generation workflow—this is a pure evaluation/validation layer.

</domain>

<decisions>
## Implementation Decisions

### Evaluation Dimensions
- **All 4 dimensions equally weighted**:
  1. Item quality (clarity, bias, construct validity scores)
  2. Agent performance (accuracy, reliability per agent)
  3. Workflow metrics (total time, iteration count, acceptance rate)
  4. Construct validity (correspondence scores, distinctiveness)
- No prioritization—comprehensive evaluation
- Matches roadmap success criteria

### Results Presentation
- **Dashboard UI** — Web interface with visualization
- Can reuse existing Next.js components (GeneratedItemsTable, EvidenceAuditPanel patterns)
- **Aggregated summary metrics** — High-level scores per dimension (e.g., "Item Quality: 8.2/10", "Workflow: 95% acceptance rate")
- No per-agent breakdowns or per-construct drill-downs in v1 (keep simple)
- Dashboard accessible from main app (new route or tab)

### Baseline for ≥15% Improvement
- **Compare to pre-v1.0 system** — Run eval on current v1.0 (with LLM-as-judge validation) vs hypothetical baseline without validation gate
- Simple A/B comparison: system with validation gate vs system without
- Demonstrates value of v1.0 optimization work

### Benchmark Construct Sourcing
- **Use published scales** — 5 well-validated scales across domains (personality, clinical, social, organizational, attitudes)
- **Web Surfer agent finds scales** — Use Perplexity academic search to research and select scales (not Claude directly)
- **Selection criteria**:
  1. High citation count (widely used, credible)
  2. Open access / public domain (no restrictive copyright)
  3. Established validity evidence (documented psychometric properties)
- **5 items per construct** — 25 total items for evaluation (faster runtime, ~2-5 min)
- Web Surfer outputs scale metadata: name, author, year, domain, sample items

### AI-Based Comparison (Not Human Experts)
- **LLM-as-judge comparison** — Use Claude Opus to compare generated items to published scale items
- Same pattern as current validation gate (proven approach)
- **4 comparison criteria**:
  1. Quality parity — Are generated items of comparable quality to published items? (clarity, precision, readability)
  2. Construct fidelity — Do generated items measure the same construct as effectively?
  3. Stylistic similarity — Do generated items match tone, format, style of published scale?
  4. Psychometric properties — Similar item characteristics (difficulty, discrimination, bias)?
- Each criterion scored 1-10 with reasoning (structured output)

### Claude's Discretion
- Comparison results presentation format (aggregate scores vs per-item cards vs summary+drill-down)
- Dashboard UI design and component structure
- How to run pre-v1.0 baseline comparison (disable validation gate, regenerate items)
- Metrics aggregation formulas (how to combine scores across constructs)
- Dashboard routing and navigation integration

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Validation scoring**: `backend/agents/validator.py` already implements 4-dimensional LLM-as-judge scoring (correspondence, distinctiveness, clarity, specificity)
- **Web Surfer agent**: `backend/agents/web_surfer.py` with Perplexity integration for academic search
- **Results display**: `src/components/GeneratedItemsTable.tsx` shows items with validation scores—pattern can be extended for eval dashboard
- **Export system**: CSV/JSON/Markdown export already captures full metadata (validation scores, review feedback, audit trail)
- **Test infrastructure**: `tests/` with unit tests for agents, graph, schemas—eval suite can follow similar structure

### Established Patterns
- **LLM-as-judge**: Proven pattern with structured output (Pydantic schemas), Claude Opus for high-accuracy judgments
- **Dashboard UI**: Next.js App Router, shadcn/ui components, TanStack Query for state management
- **Agent invocation**: `invoke_structured(schema, messages)` wrapper from `backend/llm_utils.py`—reuse for eval judge agent
- **Metric tracking**: Already capture iteration_count, thread_id, run_id in audit metadata

### Integration Points
- **Eval dashboard route**: Add to `src/app/` (e.g., `/eval` or `/evaluation`)
- **Eval suite trigger**: New backend endpoint (e.g., `/v1/run-evaluation`) or CLI command
- **Benchmark data storage**: Store 5 published scales in `data/benchmarks/` (similar to `data/approved_sources/`)
- **Results storage**: Could reuse SQLite checkpointer or new `eval_results.json` file

</code_context>

<specifics>
## Specific Ideas

- **Web Surfer for scale selection**: Let the agent research and select scales rather than manually curating. Aligns with research-backed approach from Phase 2.
- **AI comparison instead of human experts**: Automate the "expert comparison" requirement using LLM-as-judge. Faster, more consistent, fits existing patterns.
- **Aggregated metrics only**: Keep dashboard simple in v1. Avoid complex drill-downs (per-agent, per-construct) that add implementation effort without clear value for initial evaluation.
- **5 items per construct**: Balance statistical validity with eval runtime. 25 items total is enough for meaningful comparison without being slow.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-comprehensive-evaluation-framework*
*Context gathered: 2026-03-09*
