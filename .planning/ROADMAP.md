# Roadmap: MAPIG Production Optimization

## Overview

Transform MAPIG from an OpenAI-powered prototype into a production-ready psychometric item generator with Claude API, automated construct validation, and deployment to Vercel. The journey progresses from implementing research-backed validation gates, optimizing agent architecture with psychometric principles, migrating to Claude API with smart model allocation, adding production export features, deploying to serverless infrastructure, and establishing comprehensive evaluation benchmarks. Every phase builds toward the core value: generating psychometrically valid, production-ready assessment items with automated construct validation.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: LLM-as-Judge Validation Gate** - Automated construct validity scoring with rejection/retry logic (completed 2026-03-08)
- [ ] **Phase 2: Agent Architecture Optimization** - Research-backed prompt refinement with psychometric principles
- [ ] **Phase 3: Claude API Migration** - Smart model allocation with OpenAI fallback and UI selector
- [x] **Phase 4: Production Features** - Multi-format export with validation scores and audit trails (completed 2026-03-08)
- [ ] **Phase 5: Vercel Deployment** - Serverless FastAPI conversion with production URL
- [ ] **Phase 6: Comprehensive Evaluation Framework** - Benchmarking against published scales with success metrics

## Phase Details

### Phase 1: LLM-as-Judge Validation Gate
**Goal**: Items are automatically validated for construct correspondence immediately after generation, with low-scoring items rejected and regenerated before reaching human reviewers

**Depends on**: Nothing (first phase)

**Requirements**: VAL-01, VAL-02, VAL-03, VAL-04, VAL-05, VAL-06, VAL-07, VAL-08, VAL-09

**Success Criteria** (what must be TRUE):
  1. Validation agent executes immediately after Item Writer completes, before any reviewers see the items
  2. Each generated item receives a 1-10 score with explicit chain-of-thought reasoning visible in the UI
  3. Items scoring below 7.0 are automatically rejected and regenerated without human intervention
  4. System attempts up to 3 regenerations per rejected item before accepting the best-scoring version
  5. Results UI displays validation scores across 4 dimensions (correspondence 50%, distinctiveness 25%, clarity 15%, specificity 10%) with reasoning for each item

**Plans**: 5 plans

Plans:
- [x] 01-01-PLAN.md — Create test scaffolding for TDD workflow (Wave 1) — ✓ 2026-03-08
- [x] 01-02-PLAN.md — Add validation schemas, Claude configuration, and LLM factory (Wave 2) — ✓ 2026-03-08
- [x] 01-03-PLAN.md — Implement validation agent with multi-dimensional scoring rubric (Wave 3) — ✓ 2026-03-08
- [x] 01-04-PLAN.md — Integrate validation gate into graph with conditional routing (Wave 4) — ✓ 2026-03-08
- [x] 01-05-PLAN.md — Display validation scores and reasoning in Results UI (Wave 5) — ✓ 2026-03-08

### Phase 2: Agent Architecture Optimization
**Goal**: All 7 agents apply research-backed psychometric principles through optimized prompts that enforce item quality standards, semantic diversity, and comprehensive bias detection

**Depends on**: Phase 1

**Requirements**: AGT-01, AGT-02, AGT-03, AGT-04, AGT-05, AGT-06, AGT-07, AGT-08, AGT-09, AGT-10

**Success Criteria** (what must be TRUE):
  1. Item Writer generates items that explicitly demonstrate 10 core psychometric principles (unidimensionality, clarity, reading level, positive keying only, semantic diversity)
  2. Generated items meet targeted reading levels automatically (6th-8th grade general, 5th-6th clinical, 10th-12th specialized) as agent judgment
  3. Bias Reviewer detects all 7 bias types via structured checklist evaluation, including intersectional bias for combined identities
  4. Content Reviewer enforces construct correspondence with explicit facet balancing
  5. Critic makes routing decisions based on adaptive severity thresholds by iteration, enabling early termination for high-quality items

**Plans**: 6 plans

Plans:
- [x] 02-01-PLAN.md — Create test scaffolds for prompt optimizations (Wave 0)
- [x] 02-02-PLAN.md — Optimize Item Writer prompt with 10 psychometric principles (Wave 1)
- [x] 02-03-PLAN.md — Optimize Bias Reviewer prompt with 7-type taxonomy (Wave 1)
- [x] 02-04-PLAN.md — Optimize Content and Linguistic Reviewer prompts (Wave 1)
- [x] 02-05-PLAN.md — Optimize Meta Editor and Critic with adaptive thresholds (Wave 2)
- [ ] 02-06-PLAN.md — Remove test skip decorators from Item Writer tests (Wave 1, gap closure)

### Phase 3: Claude API Migration
**Goal**: MAPIG runs on Claude API by default with smart model allocation (Opus for validation, Sonnet for other agents) while maintaining OpenAI as user-selectable fallback

**Depends on**: Phase 2

**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, API-07

**Success Criteria** (what must be TRUE):
  1. User can select between Claude and OpenAI models via UI dropdown before starting item generation
  2. System automatically allocates Claude Opus for Validation Agent and Claude Sonnet for all other agents when Claude is selected
  3. CLAUDE_API_KEY environment variable is configured in Vercel and system falls back gracefully if not present
  4. Item generation workflow completes successfully using Claude models end-to-end
  5. Cost tracking displays total API spend broken down by model (Opus vs Sonnet vs OpenAI) in results UI

**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md — Backend model infrastructure with smart allocation (Wave 1)
- [ ] 03-02-PLAN.md — Frontend model selector and cost tracking UI (Wave 1)
- [ ] 03-03-PLAN.md — End-to-end integration and Vercel documentation (Wave 2)

### Phase 03.1: Enhance FinalOutput schema with user metadata and review feedback (INSERTED)

**Goal:** FinalOutput schema includes user_request and review feedback arrays enabling complete metadata export without breaking backward compatibility

**Requirements**: SCHEMA-01, SCHEMA-02, SCHEMA-03, SCHEMA-04

**Depends on:** None (independent schema enhancement for Phase 4 dependencies)

**Success Criteria** (what must be TRUE):
  1. FinalOutput schema contains optional user_request field with backward-compatible defaults
  2. FinalOutput schema contains review feedback arrays (linguistic, bias, content) with Field(default_factory=list)
  3. finalize_node populates all enhanced fields from GraphState without breaking existing logic
  4. Frontend TypeScript types mirror backend schema changes exactly
  5. Existing API consumers continue working without modification (null/empty arrays for new fields)

**Plans:** 2/3 plans executed

Plans:
- [ ] 03.1-00-PLAN.md — Create test scaffolds for schema validation and graph integration (Wave 0)
- [ ] 03.1-01-PLAN.md — Add optional metadata fields to FinalOutput and update finalize_node (Wave 1)

### Phase 4: Production Features
**Goal**: Users can export complete item sets with full metadata in their preferred format (Markdown, CSV, JSON) including validation scores and audit trails

**Depends on**: Phase 3.1 (requires enhanced FinalOutput schema)

**Requirements**: FEAT-01, FEAT-02, FEAT-03, FEAT-04, FEAT-05, FEAT-06

**Success Criteria** (what must be TRUE):
  1. Download button appears in results UI with format selector (Markdown, CSV, JSON)
  2. Exported files contain items, construct definition, user constraints, evidence sources, and full audit trail (thread_id, run_id, iteration_count, model allocation)
  3. Validation scores are included in exports with all 4 dimension scores, reasoning, and attempt count per item
  4. Review feedback from all agents (Content, Linguistic, Bias, Meta Editor) is preserved in export with agent attribution
  5. User can download results immediately after generation completes without additional configuration

**Plans**: 1 plan

Plans:
- [x] 04-01-PLAN.md — Multi-format export implementation with RFC 4180-compliant CSV, JSON, and Markdown formats — ✓ 2026-03-08

### Phase 5: Vercel Deployment
**Goal**: MAPIG runs on Vercel serverless infrastructure with production URL, maintaining all functionality including SSE streaming and SQLite checkpoints

**Depends on**: Phase 4

**Requirements**: DEP-01, DEP-02, DEP-03, DEP-04, DEP-05, DEP-06, DEP-07, DEP-08

**Success Criteria** (what must be TRUE):
  1. Production URL is accessible publicly and handles end-to-end item generation workflow
  2. SSE streaming displays real-time agent progress events in frontend exactly as in local development
  3. SQLite checkpoints enable session resumption after interruptions (users can return to in-progress runs)
  4. CLAUDE_API_KEY and OPENAI_API_KEY are configured as Vercel environment variables and accessible to serverless functions
  5. First request after cold start completes within 5 seconds (cold start optimization)

**Plans**: TBD

Plans:
- [ ] TBD during phase planning

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

**Plans**: TBD

Plans:
- [ ] TBD during phase planning

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 3.1 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. LLM-as-Judge Validation Gate | 5/5 | Complete    | 2026-03-08 |
| 2. Agent Architecture Optimization | 5/6 | In Progress|  |
| 3. Claude API Migration | 2/3 | In Progress|  |
| 3.1. Enhance FinalOutput schema | 0/2 | Complete    | 2026-03-08 |
| 4. Production Features | 0/1 | Complete    | 2026-03-08 |
| 5. Vercel Deployment | 0/TBD | Not started | - |
| 6. Comprehensive Evaluation Framework | 0/TBD | Not started | - |

---
*Roadmap created: 2026-03-08*
*Last updated: 2026-03-08 (Phase 3.1 requirements and dependency added)*
