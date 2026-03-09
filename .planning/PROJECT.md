# MAPIG: Production Psychometric Item Generator

## What This Is

MAPIG is a production-ready multi-agent platform for generating psychometrically sound assessment items, powered by Claude API with automated construct validation. The system uses research-backed agent optimization to generate items for psychological assessments (personality, clinical, organizational, social psychology) with LLM-as-judge quality control, explicit evidence trails, and full metadata export capabilities.

## Core Value

Generate psychometrically valid, production-ready assessment items with automated construct validation that ensures items truly measure what they claim to measure, backed by established test development principles.

## Requirements

### Validated

<!-- Baseline system capabilities -->

- ✓ 7-agent workflow (Web Surfer, Item Writer, Content Reviewer, Linguistic Reviewer, Bias Reviewer, Meta Editor, Critic) — baseline
- ✓ Evidence-bounded generation from approved sources (local + Perplexity academic search) — baseline
- ✓ Iterative review/revision cycles with human feedback loops — baseline
- ✓ LangGraph state machine with SQLite checkpointing for run recovery — baseline
- ✓ FastAPI backend with SSE streaming for real-time progress — baseline
- ✓ Next.js frontend with guided Setup → Run → Results flow — baseline
- ✓ Typed schemas (Pydantic) enforcing contracts between agents — baseline
- ✓ Audit metadata tracking (thread_id, run_id, iteration_count, evidence sources) — baseline
- ✓ Constraint model (baseline + user constraints) — baseline
- ✓ Mock mode for testing without API keys — baseline

<!-- v1.0 Production Optimization -->

- ✓ LLM-as-judge validation gate with 4-dimensional scoring (correspondence 50%, distinctiveness 25%, clarity 15%, specificity 10%) — v1.0
- ✓ Automated quality control with 7.0 acceptance threshold and smart retry logic (max 3 attempts) — v1.0
- ✓ Validation agent using Claude Opus 4.6 for highest accuracy — v1.0
- ✓ Validation scores and reasoning visible in Results UI — v1.0
- ✓ Item Writer enhanced with 10 psychometric principles and semantic diversity controls — v1.0
- ✓ Reading level targeting (6th-8th grade general, 5th-6th clinical, 10th-12th specialized) — v1.0
- ✓ Content Reviewer refined with construct correspondence criteria — v1.0
- ✓ Linguistic Reviewer enhanced with vague quantifier context rules — v1.0
- ✓ Bias Reviewer upgraded with 7-type taxonomy and intersectionality checks — v1.0
- ✓ Meta Editor with facet balancing enforcement — v1.0
- ✓ Critic with adaptive iteration thresholds (severity-based routing) — v1.0
- ✓ Claude API integration with smart model allocation (Opus validation, Sonnet others) — v1.0 (80% cost reduction)
- ✓ OpenAI fallback option (user-selectable via UI model selector) — v1.0
- ✓ Enhanced FinalOutput schema with user_request and review feedback arrays — v1.0
- ✓ Multi-format export (CSV, JSON, Markdown) with RFC 4180 compliance — v1.0
- ✓ Full metadata export (validation scores, review feedback, audit trail) — v1.0

### Active

<!-- Next milestone: Deployment and Evaluation -->

**1. Vercel Deployment**
- [ ] Convert FastAPI endpoints to Vercel serverless functions
- [ ] Adapt LangGraph state machine for serverless execution
- [ ] Maintain SQLite checkpoint compatibility (local storage)
- [ ] Deploy Next.js frontend to Vercel
- [ ] Configure CLAUDE_API_KEY and OPENAI_API_KEY in Vercel environment
- [ ] Production URL accessible and functional
- [ ] SSE streaming works in Vercel serverless environment
- [ ] Cold start optimization (<5s first request)

**2. Comprehensive Evaluation Framework**
- [ ] Item quality metrics (clarity score, bias score, construct validity score)
- [ ] Agent performance metrics (accuracy, reliability per agent)
- [ ] End-to-end workflow metrics (total time, iteration count, acceptance rate)
- [ ] Benchmark constructs (5 test cases: personality, clinical, social, organizational, attitudes)
- [ ] Compare generated items to published scales (expert comparison)
- [ ] Automated eval suite runnable on demand
- [ ] Success criteria: validation scores improve ≥15% vs baseline
- [ ] Success criteria: generated items comparable to published scales

**3. Optional Phase 2 Enhancements**
- [ ] A/B test Content + Bias reviewer consolidation (7→6 agents)
- [ ] Token tracking implementation (infrastructure ready from Phase 3)

### Out of Scope

- Supabase integration — not needed, SQLite checkpoints sufficient
- User authentication system — keep open access for v1
- Mobile app development — web-first approach
- Real-time collaboration features — single-user workflow adequate
- Changing core frontend functionality — only add download button, model selector, export options
- Training custom embedding models — use LLM-as-judge instead of SurveyBot3000 approach
- Generating synthetic response data — LLM-as-judge validation sufficient for v1

## Context

**Current State (v1.0):**
- Tech stack: FastAPI + LangGraph + Next.js, Claude Opus/Sonnet, 18,460 LOC (Python + TypeScript)
- 7 specialized agents with research-backed optimization: Web Surfer (evidence) → Item Writer (10 psychometric principles) → Validation Agent (4-dimensional scoring) → Parallel Reviews (Content, Linguistic, Bias) → Critic (adaptive thresholds) → Meta Editor (facet balancing) → loop or finalize
- LLM-as-judge validation gate: 7.0 threshold, max 3 retries, Claude Opus 4.6
- Smart model allocation: Opus for validation (accuracy), Sonnet for other agents (80% cost reduction)
- Full metadata export: CSV/JSON/Markdown with validation scores, review feedback, audit trail
- Evidence sources: local markdown files + Perplexity academic search with domain allowlist
- Frontend: Next.js with model selector, export controls, SSE event streaming
- Backend: FastAPI with AsyncSqliteSaver checkpoints, streaming endpoints

**Research Foundation:**
- SurveyBot3000 paper (synthetic correlations) validates LLM-as-judge approach
- Psychometric test development literature (construct validity, item writing, bias minimization)
- 10 core principles integrated into Item Writer prompt
- 7-type bias taxonomy with intersectionality checks

**Known Issues:**
- Phase 2 Nyquist validation gap (missing automated test coverage for agent optimizations)
- Phase 3 token tracking infrastructure ready but implementation deferred
- Not yet deployed to production (Vercel deployment in Phase 5)

## Constraints

- **Tech Stack**: FastAPI + LangGraph + Next.js — preserve existing architecture
- **Deployment**: Vercel serverless — requires FastAPI conversion to serverless functions
- **Performance**: Parallel agent execution where possible (research, reviews)
- **API Costs**: Smart model allocation to balance quality and cost (Opus for validation only)
- **Data Privacy**: No user data persistence beyond session checkpoints (SQLite local)
- **Compatibility**: Maintain backward compatibility with existing approved_sources data
- **Quality**: All changes must demonstrably improve item quality (eval-driven)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Claude API (not OpenAI) as default | Superior reasoning capabilities for psychometric validation, better prompt following for complex agent tasks | ✓ Good — v1.0 shipped with Claude default, OpenAI fallback working |
| LLM-as-judge validation (not embedding similarity) | Transparent reasoning, explicit scoring, aligns with research-backed validation | ✓ Good — 4-dimensional scoring with chain-of-thought reasoning implemented |
| Smart model allocation (Opus validation, Sonnet others) | Balance quality and cost; validation is critical path, other agents less demanding | ✓ Good — 80% cost reduction achieved while maintaining validation accuracy |
| Vercel serverless deployment (not traditional hosting) | Simplified deployment, automatic scaling, cost-effective for intermittent use | — Pending — Phase 5 |
| No Supabase (keep SQLite) | Current checkpointing sufficient, avoid unnecessary complexity | ✓ Good — SQLite checkpoints working well, no issues |
| Research-driven optimization (not intuition-based) | Psychometric validity requires evidence-based practices, not guesswork | ✓ Good — 10 psychometric principles + 7-type bias taxonomy integrated |
| Multi-format export (MD/CSV/JSON) | Different use cases require different formats (documentation vs analysis) | ✓ Good — RFC 4180 CSV + full metadata export implemented |
| Comprehensive evals (4 dimensions) | Need multiple lenses to validate system improvement (items, agents, workflow, validity) | — Pending — Phase 6 |
| Positive keying only (no reverse-scored items) | Research shows reverse-scored items reduce reliability and introduce method effects | ✓ Good — Item Writer enforces positive keying with rationale |
| Validation gate before reviewers (not after) | Catch fundamental construct misalignment early, save API costs on doomed items | ✓ Good — Prevents wasted reviewer cycles on invalid items |

---
*Last updated: 2026-03-09 after v1.0 milestone completion*
