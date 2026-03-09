# Roadmap: MAPIG Production Optimization

## Milestones

- ✅ **v1.0 Production Optimization** — Phases 1-4 (shipped 2026-03-09)
- 📋 **v1.1 Deployment** — Phases 5-6 (planned)

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

### 📋 v1.1 Deployment (In Progress)

- [x] Phase 5: Vercel Deployment (4/4 plans) — completed 2026-03-09
- [ ] Phase 6: Comprehensive Evaluation Framework (4 plans)

## Phase Details

### Phase 5: Vercel Deployment
**Goal**: MAPIG runs on Vercel serverless infrastructure with production URL, maintaining all functionality including SSE streaming with in-memory checkpointing

**Depends on**: Phase 4

**Requirements**: DEP-01, DEP-02, DEP-03, DEP-04, DEP-05, DEP-06, DEP-07

**Note**: DEP-08 (cold start optimization <5s) deferred to v2 per user decision. Baseline measurements documented in 05-03.

**Success Criteria** (what must be TRUE):
  1. Production URL is accessible publicly and handles end-to-end item generation workflow
  2. SSE streaming displays real-time agent progress events in frontend exactly as in local development
  3. In-memory checkpoints maintain state during single run (session resumption not required after cold start for v1)
  4. CLAUDE_API_KEY and OPENAI_API_KEY are configured as Vercel environment variables and accessible to serverless functions
  5. Cold start performance documented with baseline measurements (DEP-08 optimization deferred to v2)

**Plans**: 4 plans

Plans:
- [x] 05-00-PLAN.md — Create test scaffolds for Vercel deployment (Wave 0)
- [x] 05-01-PLAN.md — Backend serverless conversion with MemorySaver and CORS configuration (Wave 2)
- [x] 05-02-PLAN.md — Frontend Vercel configuration and deployment documentation (Wave 3)
- [x] 05-03-PLAN.md — Vercel deployment, verification, and cold start baseline (Wave 4)

**Production URL**: https://lmaig-langgraph.vercel.app/
**Deployment**: Single-project monorepo pattern (Next.js + Python in one Vercel project)

### Phase 6: Comprehensive Evaluation Framework
**Goal**: System quality is validated through automated evaluation suite measuring item quality, agent performance, workflow efficiency, and construct validity against published scales with documented success criteria

**Depends on**: Phase 5

**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06, EVAL-07, EVAL-08

**Success Criteria** (what must be TRUE):
  1. Automated evaluation suite runs on demand, generating reports across 4 dimensions (item quality, agent performance, workflow metrics, construct validity)
  2. Evaluation includes 5 benchmark constructs (personality, clinical, social, organizational, attitudes) with test cases
  3. Generated items are compared to published scales by expert reviewers with documented comparison results
  4. Validation scores demonstrate ≥15% improvement over baseline (pre-optimization system)
  5. Success criteria are documented: validation score improvement ≥15% AND generated items rated as comparable to published scales by experts

**Plans**: 4 plans

Plans:
- [ ] 06-01-PLAN.md — Backend evaluation infrastructure with LLM-as-judge comparison (Wave 1)
- [ ] 06-02-PLAN.md — Benchmark scale sourcing and storage (Wave 1)
- [ ] 06-03-PLAN.md — Evaluation suite orchestrator and baseline comparison (Wave 2)
- [ ] 06-04-PLAN.md — Dashboard UI and API endpoint (Wave 3)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 3.1 → 4 → 5 → 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. LLM-as-Judge Validation Gate | v1.0 | 5/5 | Complete | 2026-03-08 |
| 2. Agent Architecture Optimization | v1.0 | 6/6 | Complete | 2026-03-08 |
| 3. Claude API Migration | v1.0 | 3/3 | Complete | 2026-03-09 |
| 3.1. Enhanced FinalOutput Schema | v1.0 | 2/2 | Complete | 2026-03-08 |
| 4. Production Features | v1.0 | 1/1 | Complete | 2026-03-08 |
| 5. Vercel Deployment | v1.1 | 4/4 | Complete | 2026-03-09 |
| 6. Comprehensive Evaluation Framework | v1.1 | 0/4 | Planned | - |

---
*Roadmap created: 2026-03-08*
*Last updated: 2026-03-09 (Phase 6 planning complete)*
