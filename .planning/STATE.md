---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Psychometric Rigor
status: executing
stopped_at: Completed 08-01-PLAN.md (Correlation analysis engine)
last_updated: "2026-03-14T11:41:49.951Z"
last_activity: 2026-03-14 — Completed Plan 08-01 (Correlation analysis engine with McDonald's omega)
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 5
  completed_plans: 3
  percent: 60
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Generate psychometrically valid, production-ready assessment items with automated construct validation that ensures items truly measure what they claim to measure, backed by established test development principles

**Current focus:** v2.0 Psychometric Rigor — Adding scale-level validation through synthetic correlations, instrument comparison, and advanced reasoning models

## Current Position

Phase: Phase 8 (Synthetic Correlation Analysis)
Plan: Plan 01 Complete (1/3 plans)
Status: Phase 8 In Progress — Correlation Engine Complete
Last activity: 2026-03-14 — Completed Plan 08-01 (Correlation analysis engine with McDonald's omega)

Progress: [██████░░░░] 60% (0/4 phases complete, 3/5 total plans across phases)

## Performance Metrics

**Velocity:**
- v1.0: 17 plans across 5 phases (Feb 9 → Mar 9, 2026)
- v1.1: 8 plans across 2 phases (Mar 9, 2026)
- Average: 3.6 plans per phase

**Projected for v2.0:**
- 4 phases at 3.6 plans/phase = ~14-16 plans estimated

**Phase 7 Execution:**

| Plan | Tasks | Duration | Files | Commits |
|------|-------|----------|-------|---------|
| 07-01 | 3 tasks | ~15min | 3 files | 3 commits |
| 07-02 | 2 tasks | 6m 44s | 5 files | 2 commits |

**Phase 7 Total:** 2 plans, 5 tasks, 8 files modified, 5 commits, ~22 minutes
| Phase 08 P01 | 533 | 2 tasks | 12 files |

## Accumulated Context

### Decisions

**v2.0 roadmap decisions:**

| Decision | Rationale | Phase Impact |
|----------|-----------|--------------|
| Merge comparison + cross-construct (Phase 9) | Both require instrument search infrastructure; share Web Surfer enhancement; discriminant validity needs comparison instruments as input | Reduces phases from 6 to 4 (coarse granularity) |
| Merge GPT-5.2 + analytics optimization (Phase 10) | Both about cost/performance; reasoning models most valuable for analytics tasks; parallel execution needed regardless of model choice | Defers optimization until all analytics features functional |
| Foundation first (Phase 7) | Schema changes must happen before implementation to avoid refactoring; GPT-5.2 infrastructure needed by Phases 8-10 | Enables parallel development in later phases |
| Correlation before comparison (Phase 8 → 9) | Validates post-finalize analytics architecture with simpler feature; highest user value differentiator; moderate risk with clear mitigations | De-risks architecture before complex features |

**Carried from v1.0 + v1.1:** See PROJECT.md Key Decisions table.

Key decisions carrying forward:
- Research-driven optimization: All changes must be evidence-based from psychometric literature
- LLM-as-judge validation: Transparent reasoning, explicit scoring, dual-direction comparisons
- Smart model allocation: Opus for validation, Sonnet for others (80% cost reduction maintained)
- Single-project Vercel deployment: Monorepo pattern, same-origin, no CORS
- MemorySaver checkpointing: Ephemeral, acceptable for v2 (persistent checkpointing deferred)

**Phase 7 Plan-specific decisions:**

**07-01 (Analytics Schema Foundation):**
- Use flat list for CorrelationMatrix.cells instead of 2D array for simpler serialization and UI iteration
- Store disclaimer as field with default value in CorrelationMatrix and CrossConstructComparison to ensure transparency in exported JSON

**07-02 (GPT-5.2 Analytics Infrastructure):**
- Hardcoded high reasoning effort for GPT-5.2 analytics (not configurable) — ensures consistent analytics quality, simplifies configuration
- Placeholder nodes emit SSE events via step() context manager — provides frontend progress tracking even though nodes are no-op in Phase 7
- Separate reasoning_tokens from output_tokens in usage tracking — GPT-5.2 billing separates reasoning from output, enables accurate cost calculation
- [Phase 08]: Simplified omega formula instead of reliabiliPy due to scikit-learn 1.8.0 incompatibility

### Roadmap Evolution

**Phase structure rationale:**

Research suggested 6 phases but coarse granularity setting (config.json) requires 3-5 phases. Consolidated to 4 phases by merging related work:

1. **Phase 7 (Foundation)**: INFRA requirements — schema extensions, analytics scaffolding, GPT-5.2 support
2. **Phase 8 (Correlation)**: CORR + partial UI — synthetic correlation analysis with heatmap
3. **Phase 9 (Comparison)**: INST + XCON + partial UI — combined comparison and cross-construct (share instrument search)
4. **Phase 10 (Optimization)**: GPT + remaining INFRA + UI-06 — reasoning models + parallel execution

**Coverage validation:**
- Total v2.0 requirements: 28
- Mapped to phases: 28 (100% coverage)
- No orphaned requirements

### Pending Todos

**Phase 7 Complete — Next Phase:**
1. Begin Phase 8 planning with `/gsd:plan-phase 8`
2. Implement correlation analysis using GPT-5.2 analytics model
3. Create correlation matrix UI component with heatmap visualization
4. Deploy to Vercel preview to test NumPy serverless size impact

### Blockers/Concerns

**Carried tech debt:**
- Phase 2 Nyquist validation gap (80% compliant) — not blocking v2.0
- Phase 3 token tracking infrastructure deferred — not blocking v2.0
- Cold start optimization deferred (DEP-08) — may impact Phase 10 (analytics timeout risk)
- Missing /evaluation nav link — cosmetic, not blocking
- Pre-existing test failure in test_bias_reviewer.py (references app/prompts/ instead of backend/prompts/) — cosmetic, not blocking Phase 8

**v2.0-specific risks identified in research:**

1. **NumPy serverless size**: Current stack (~100 MB) + NumPy (~30 MB) = ~130 MB total, leaving 120 MB buffer below Vercel 250 MB limit. Mitigation: Deploy to preview in Phase 8, check function size; fallback to client-side correlation if >200 MB.

2. **langchain-openai 2.x compatibility**: ✅ RESOLVED in Phase 7 — Used langchain-openai 1.x API with `max_tokens` instead of `max_completion_tokens`, ChatOpenAI accepts reasoning parameter correctly.

3. **Perplexity retrieval quality**: Unknown if Perplexity Academic can retrieve full instrument metadata vs just abstracts. Mitigation: Test on 10-20 known constructs in Phase 9 before production; supplement with Semantic Scholar if needed.

4. **Serverless timeout**: 50 items = 1,225 pairwise comparisons, timeout risk with 300s limit. Mitigation: Streaming partial results, correlation caching, Fluid Compute upgrade to 800s documented in Phase 10.

**No active blockers for Phase 8 planning.**

## Session Continuity

Last session: 2026-03-14T11:41:49.950Z
Stopped at: Completed 08-01-PLAN.md (Correlation analysis engine)
Resume: `/gsd:plan-phase 8`

**Phase 7 Summary:**
- ✅ Plan 01: Analytics Schema Foundation (FinalOutput.analytics field, Pydantic models, TypeScript types)
- ✅ Plan 02: GPT-5.2 Analytics Infrastructure (model factory, token tracking, analytics nodes)
- Status: Phase 7 complete, ready for Phase 8 (Correlation Analysis)

**Roadmap summary:**
- 4 phases (7-10) covering 28 requirements
- Coarse granularity (3-5 phases) applied via consolidation
- All requirements mapped (100% coverage)
- Dependencies: 7 → 8 → 9 → 10 (sequential execution)
- **Phase 7 complete ✅** — Foundation infrastructure ready for analytics features

---
*State initialized: 2026-03-14*
*Last updated: 2026-03-14T10:07:44Z (Phase 7 complete)*
