---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Psychometric Rigor
status: roadmap_created
stopped_at: Roadmap created, awaiting Phase 7 planning
last_updated: "2026-03-14"
last_activity: 2026-03-14 — v2.0 roadmap created with 4 phases
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Generate psychometrically valid, production-ready assessment items with automated construct validation that ensures items truly measure what they claim to measure, backed by established test development principles

**Current focus:** v2.0 Psychometric Rigor — Adding scale-level validation through synthetic correlations, instrument comparison, and advanced reasoning models

## Current Position

Phase: Phase 7 (Foundation & Infrastructure)
Plan: Not started
Status: Roadmap created, ready for phase planning
Last activity: 2026-03-14 — v2.0 roadmap created with 4 phases (7-10)

Progress: [░░░░░░░░░░] 0% (0/4 phases, 0/0 plans)

## Performance Metrics

**Velocity:**
- v1.0: 17 plans across 5 phases (Feb 9 → Mar 9, 2026)
- v1.1: 8 plans across 2 phases (Mar 9, 2026)
- Average: 3.6 plans per phase

**Projected for v2.0:**
- 4 phases at 3.6 plans/phase = ~14-16 plans estimated

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

**Next steps:**
1. Begin Phase 7 planning with `/gsd:plan-phase 7`
2. Focus on schema design (GraphState, FinalOutput extensions)
3. Establish GPT-5.2 infrastructure (llm_factory upgrade to langchain-openai 2.x)
4. Create analytics node placeholders in graph builder

### Blockers/Concerns

**Carried tech debt:**
- Phase 2 Nyquist validation gap (80% compliant) — not blocking v2.0
- Phase 3 token tracking infrastructure deferred — not blocking v2.0
- Cold start optimization deferred (DEP-08) — may impact Phase 10 (analytics timeout risk)
- Missing /evaluation nav link — cosmetic, not blocking

**v2.0-specific risks identified in research:**

1. **NumPy serverless size**: Current stack (~100 MB) + NumPy (~30 MB) = ~130 MB total, leaving 120 MB buffer below Vercel 250 MB limit. Mitigation: Deploy to preview in Phase 8, check function size; fallback to client-side correlation if >200 MB.

2. **langchain-openai 2.x compatibility**: GitHub issues (#29632, #29947, #32714) show `max_completion_tokens` parameter problems. Mitigation: Test upgrade in isolation in Phase 7; validate existing agents still work; keep fallback to 1.1.7.

3. **Perplexity retrieval quality**: Unknown if Perplexity Academic can retrieve full instrument metadata vs just abstracts. Mitigation: Test on 10-20 known constructs in Phase 9 before production; supplement with Semantic Scholar if needed.

4. **Serverless timeout**: 50 items = 1,225 pairwise comparisons, timeout risk with 300s limit. Mitigation: Streaming partial results, correlation caching, Fluid Compute upgrade to 800s documented in Phase 10.

No active blockers for Phase 7 planning.

## Session Continuity

Last session: 2026-03-14
Stopped at: v2.0 roadmap created, ready for Phase 7 planning
Resume: `/gsd:plan-phase 7`

**Roadmap summary:**
- 4 phases (7-10) covering 28 requirements
- Coarse granularity (3-5 phases) applied via consolidation
- All requirements mapped (100% coverage)
- Dependencies: 7 → 8 → 9 → 10 (sequential execution)

---
*State initialized: 2026-03-14*
*Last updated: 2026-03-14 (v2.0 roadmap created)*
