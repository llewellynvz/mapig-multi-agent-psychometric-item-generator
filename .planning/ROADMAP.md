# Roadmap: MAPIG Production Optimization

## Milestones

- ✅ **v1.0 Production Optimization** — Phases 1-4 (shipped 2026-03-09)
- ✅ **v1.1 Deployment** — Phases 5-6 (shipped 2026-03-09)
- 🚧 **v2.0 Psychometric Rigor** — Phases 7-10 (in progress)

## Phases

<details>
<summary>✅ v1.0 Production Optimization (Phases 1-4, 3.1) — SHIPPED 2026-03-09</summary>

- [x] Phase 1: LLM-as-Judge Validation Gate (5/5 plans) — completed 2026-03-08
- [x] Phase 2: Agent Architecture Optimization (6/6 plans) — completed 2026-03-08
- [x] Phase 3: Claude API Migration (3/3 plans) — completed 2026-03-09
- [x] Phase 3.1: Enhanced FinalOutput Schema (2/2 plans) — completed 2026-03-08
- [x] Phase 4: Production Features (1/1 plan) — completed 2026-03-08

**Archive:** See `.planning/milestones/v1.0-ROADMAP.md` for full details

</details>

<details>
<summary>✅ v1.1 Deployment (Phases 5-6) — SHIPPED 2026-03-09</summary>

- [x] Phase 5: Vercel Deployment (4/4 plans) — completed 2026-03-09
- [x] Phase 6: Comprehensive Evaluation Framework (4/4 plans) — completed 2026-03-09

**Archive:** See `.planning/milestones/v1.1-ROADMAP.md` for full details

</details>

### v2.0 Psychometric Rigor (Phases 7-10)

- [x] **Phase 7: Foundation & Infrastructure** ✅ COMPLETE (2/2 plans) — Schema extensions and analytics scaffolding
- [x] **Phase 8: Synthetic Correlation Analysis** ✅ COMPLETE (3/3 plans) — LLM-estimated inter-item correlations with heatmap visualization
- [ ] **Phase 9: Dynamic Instrument Comparison** - Literature-grounded validated instruments and cross-construct analysis
- [ ] **Phase 10: GPT-5.2 Integration & Analytics Optimization** - Advanced reasoning models with parallel execution

## Phase Details

### Phase 7: Foundation & Infrastructure
**Goal**: Graph state and schema infrastructure support psychometric analytics with GPT-5.2 reasoning model capability

**Depends on**: Phase 6

**Requirements**: INFRA-01, INFRA-02, INFRA-05

**Success Criteria** (what must be TRUE):
  1. GraphState schema includes CorrelationMatrix, ComparisonInstrument, and CrossConstructComparison types with proper field validation
  2. FinalOutput schema extended with correlation_matrix, comparison_instruments, and cross_construct_analysis fields without breaking existing exports
  3. LLM factory supports GPT-5.2 reasoning models with hardcoded high reasoning effort for analytics tasks
  4. Analytics node placeholders exist in graph builder with no-op implementations that pass through state unchanged
  5. Existing v1.1 generation workflow remains fully functional with all tests passing after schema changes

**Status:** ✅ COMPLETE (2/2 plans executed)

Plans:
- [x] 07-01-PLAN.md — Analytics Pydantic models, FinalOutput extension, TypeScript types
- [x] 07-02-PLAN.md — GPT-5.2 factory, token tracking, analytics placeholder nodes

**Deliverables:**
- ✅ FinalOutput.analytics field with CorrelationMatrix, ComparisonInstrument[], CrossConstructComparison types
- ✅ Pydantic models for all analytics types with proper field validation
- ✅ TypeScript type mirrors in frontend (CorrelationAnalysis, ComparisonInstrument, etc.)
- ✅ get_gpt52_analytics_model() factory function with hardcoded high reasoning effort
- ✅ TokenUsage.reasoning_tokens field for GPT-5.2 token tracking
- ✅ correlation_node, comparison_node, cross_construct_node placeholders in graph
- ✅ GraphState extended with gpt52_tokens_used, gpt52_reasoning_tokens, gpt52_output_tokens
- ✅ Analytics chain wired: finalize -> correlation -> comparison -> cross_construct -> END

### Phase 8: Synthetic Correlation Analysis
**Goal**: Generated item sets include LLM-estimated inter-item correlation matrices with McDonald's omega and internal consistency metrics displayed in interactive heatmap

**Depends on**: Phase 7

**Requirements**: CORR-01, CORR-02, CORR-03, CORR-04, CORR-05, CORR-06, UI-01, UI-05

**Success Criteria** (what must be TRUE):
  1. User can view correlation heatmap for finalized item sets showing pairwise correlation estimates in 2D grid with color-coded values
  2. Correlation display shows McDonald's omega with threshold flag (omega >= 0.70 = pass, <0.70 = warning)
  3. Each correlation cell displays confidence interval showing estimate uncertainty
  4. All correlations labeled prominently as "LLM-estimated, not empirically validated" in UI and exported files
  5. Synthetic correlations validated against 5 published scales with known correlation matrices achieving r > 0.6 agreement benchmark
  6. Internal consistency flags display when mean inter-item correlation falls outside 0.15-0.50 optimal range

**Status:** ✅ COMPLETE (3/3 plans executed)

Plans:
- [x] 08-01-PLAN.md — Backend correlation engine: schema migration, GPT-5.2 estimation, omega calculator, graph node
- [x] 08-02-PLAN.md — Frontend heatmap visualization: visx components, quality summary, export functions
- [x] 08-03-PLAN.md — Calibration validation: benchmark scales, evaluation suite integration

**Deliverables:**
- ✅ GPT-5.2 pairwise correlation estimation with batching (20 pairs/batch, 5 concurrent)
- ✅ McDonald's omega reliability metric (simplified formula, migrated from Cronbach's alpha)
- ✅ Internal consistency flagging (optimal_range/too_low/too_high based on mean inter-item r)
- ✅ visx heatmap with Psynalytics brand colors (teal-white-lime), tooltips, popovers
- ✅ Collapsible CorrelationPanel with CorrelationSummaryCard
- ✅ CSV/JSON correlation export functions
- ✅ 5-scale calibration validation (RSES, PHQ-9, UWES-9, UCLA Loneliness, SWLS) with r > 0.6 threshold

### Phase 9: Dynamic Instrument Comparison
**Goal**: System dynamically discovers validated comparison instruments from academic literature and assesses convergent/discriminant validity without copyright infringement

**Depends on**: Phase 8

**Requirements**: INST-01, INST-02, INST-03, INST-04, INST-05, INST-06, XCON-01, XCON-02, XCON-03, XCON-04, UI-02, UI-03, UI-04, UI-05

**Success Criteria** (what must be TRUE):
  1. User can view comparison instruments panel showing validated scales measuring same construct with source citations
  2. System replaces hardcoded org psych nearest neighbors with Perplexity Academic search results grounded in literature
  3. System uses hybrid approach (hardcoded defaults + literature supplements) with automatic fallback to defaults if search fails
  4. Comparison display shows convergent validity evidence (how generated items align with instruments measuring same construct)
  5. Cross-construct comparison table shows discriminant validity assessments (how generated items differ from related-but-distinct constructs)
  6. Copyright safeguards enforce public-domain allowlist, publisher blocklist, and metadata-only storage (never store copyrighted item text)
  7. Plagiarism detection flags generated items with cosine similarity > 0.85 to retrieved instrument items
  8. Dual-direction LLM-as-judge scoring (A to B and B to A averaged) mitigates position bias in cross-construct comparisons
  9. Automated validity flagging warns when correlation > 0.85 with related construct indicates potential discriminant validity concern
  10. Related-but-distinct constructs identified via dynamic neighbor discovery validated at > 70% agreement with expert-curated benchmarks

**Plans:** 3 plans

Plans:
- [ ] 09-01-PLAN.md — Instrument search engine with Perplexity Academic, hardcoded defaults, publisher blocklist, and plagiarism detector
- [ ] 09-02-PLAN.md — Dual-direction validity scoring engine and graph node wiring (comparison_node + cross_construct_node)
- [ ] 09-03-PLAN.md — Frontend ComparisonPanel, InstrumentCard, PlagiarismBadge, and GeneratedItemsTable integration

### Phase 10: GPT-5.2 Integration & Analytics Optimization
**Goal**: System supports GPT-5.2 reasoning models with cost controls and executes all analytics in parallel for optimal performance

**Depends on**: Phase 9

**Requirements**: GPT-01, GPT-02, GPT-03, GPT-04, GPT-05, INFRA-03, INFRA-04, UI-06

**Success Criteria** (what must be TRUE):
  1. User can toggle GPT-5.2 for analytics tasks via UI toggle with cost warning modal displaying 4-6x multiplier before generation
  2. GPT-5.2 defaults to high reasoning effort for analytics tasks (correlation, comparison, cross-construct analysis)
  3. System enforces budget caps per run and aborts generation if reasoning token cost exceeds threshold with clear error message
  4. Post-run audit breakdown shows reasoning tokens vs output tokens separately in cost summary
  5. Analytics nodes (correlation, comparison, cross-construct) execute in parallel using LangGraph Send API after item finalization
  6. Analytics failures handled gracefully by populating null values in FinalOutput allowing item generation to complete successfully
  7. All new UI components match existing shadcn/ui design patterns and Radix primitives without introducing design system conflicts

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 3.1 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. LLM-as-Judge Validation Gate | v1.0 | 5/5 | Complete | 2026-03-08 |
| 2. Agent Architecture Optimization | v1.0 | 6/6 | Complete | 2026-03-08 |
| 3. Claude API Migration | v1.0 | 3/3 | Complete | 2026-03-09 |
| 3.1. Enhanced FinalOutput Schema | v1.0 | 2/2 | Complete | 2026-03-08 |
| 4. Production Features | v1.0 | 1/1 | Complete | 2026-03-08 |
| 5. Vercel Deployment | v1.1 | 4/4 | Complete | 2026-03-09 |
| 6. Comprehensive Evaluation Framework | v1.1 | 4/4 | Complete | 2026-03-09 |
| 7. Foundation & Infrastructure | v2.0 | 2/2 | Complete | 2026-03-14 |
| 8. Synthetic Correlation Analysis | v2.0 | 3/3 | Complete | 2026-03-14 |
| 9. Dynamic Instrument Comparison | v2.0 | 0/3 | Planned | - |
| 10. GPT-5.2 Integration & Analytics Optimization | v2.0 | 0/? | Not started | - |

---
*Roadmap created: 2026-03-08*
*Last updated: 2026-03-14 (Phase 9 planned - 3 plans created)*
