---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Psychometric Rigor
status: executing
stopped_at: Completed 08-03-PLAN.md
last_updated: "2026-03-14T11:55:35.015Z"
last_activity: 2026-03-14 — Completed Plan 08-03 (Correlation calibration validation)
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 5
  completed_plans: 5
  percent: 60
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Generate psychometrically valid, production-ready assessment items with automated construct validation that ensures items truly measure what they claim to measure, backed by established test development principles

**Current focus:** v2.0 Psychometric Rigor — Phase 9: Dynamic instrument comparison and cross-construct analysis

## Current Position

Phase: Phase 9 (Dynamic Instrument Comparison)
Plan: Not started
Status: Ready to plan
Last activity: 2026-03-14 — Phase 8 complete (3/3 plans, 8/8 requirements verified)

Progress: [█████████░] 50% (2/4 phases complete, 5/5 total plans across completed phases)

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

**Phase 8 Execution:**

| Plan | Tasks | Duration | Files | Commits |
|------|-------|----------|-------|---------|
| 08-01 | 2 tasks | 8m 53s | 12 files | 3 commits |
| 08-02 | 3 tasks | 4m 20s | 8 files | 2 commits |
| 08-03 | 1 task | 5m 39s | 2 files | 1 commit |

**Phase 8 Total:** 3 plans, 6 tasks, 22 files modified, 6 commits, ~19 minutes

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
- [Phase 08]: Psynalytics brand color scale (teal-white-lime) for heatmap instead of blue-white-red to maintain brand consistency
- [Phase 08]: Correlation panel collapsed by default to reduce initial cognitive load, follows progressive disclosure pattern
- [Phase 08]: Export buttons inside correlation panel context instead of main export dropdown for domain-specific exports
- [Phase 08]: Use 5 well-documented open-access scales (RSES, PHQ-9, UWES-9, UCLA Loneliness, SWLS) for calibration spanning 5 psychological domains with published correlation matrices

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

**Phase 8 Complete — Next Phase:**
1. Begin Phase 9 planning with `/gsd:plan-phase 9`
2. Implement dynamic instrument comparison with Perplexity Academic search
3. Build cross-construct analysis with discriminant validity assessment
4. Deploy to Vercel preview to test NumPy serverless size impact (carried from Phase 8)

### Blockers/Concerns

**Carried tech debt:**
- Phase 2 Nyquist validation gap (80% compliant) — not blocking v2.0
- Phase 3 token tracking infrastructure deferred — not blocking v2.0
- Cold start optimization deferred (DEP-08) — may impact Phase 10 (analytics timeout risk)
- Missing /evaluation nav link — cosmetic, not blocking
- Pre-existing test failure in test_bias_reviewer.py (references app/prompts/ instead of backend/prompts/) — cosmetic, not blocking
- reliabiliPy incompatible with scikit-learn 1.8.0 — resolved with simplified omega formula in Phase 8
- GPT-5.2 token tracking not accumulated in GraphState yet — minor enhancement for Phase 10

**v2.0-specific risks identified in research:**

1. **NumPy serverless size**: Current stack (~100 MB) + NumPy (~30 MB) = ~130 MB total, leaving 120 MB buffer below Vercel 250 MB limit. Still needs preview deployment test.

2. **langchain-openai 2.x compatibility**: ✅ RESOLVED in Phase 7.

3. **Perplexity retrieval quality**: Critical for Phase 9. Unknown if Perplexity Academic can retrieve full instrument metadata vs just abstracts. Mitigation: Test on 10-20 known constructs before production; supplement with Semantic Scholar if needed.

4. **Serverless timeout**: 50 items = 1,225 pairwise comparisons, timeout risk with 300s limit. Mitigation in Phase 10.

**No active blockers for Phase 9 planning.**

## Session Continuity

Last session: 2026-03-14
Stopped at: Phase 8 complete, ready to plan Phase 9
Resume: `/gsd:discuss-phase 9`

**Phase 8 Summary:**
- ✅ Plan 01: Correlation Analysis Engine (GPT-5.2 pairwise estimation, McDonald's omega, graph.py wired)
- ✅ Plan 02: Correlation Heatmap UI (visx visualization, brand colors, export, collapsible panel)
- ✅ Plan 03: Calibration Validation (5-scale benchmark suite proving estimation reliability)
- Status: Phase 8 complete, verified (8/8 requirements), ready for Phase 9 (Dynamic Instrument Comparison)

**Roadmap summary:**
- 4 phases (7-10) covering 28 requirements
- Coarse granularity (3-5 phases) applied via consolidation
- All requirements mapped (100% coverage)
- Dependencies: 7 → 8 → 9 → 10 (sequential execution)
- **Phase 7 complete ✅** — Foundation infrastructure ready
- **Phase 8 complete ✅** — Correlation analysis fully implemented and verified

---
*State initialized: 2026-03-14*
*Last updated: 2026-03-14 (Phase 8 complete)*
