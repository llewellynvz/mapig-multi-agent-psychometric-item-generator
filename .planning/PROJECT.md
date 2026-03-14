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

<!-- v1.1 Deployment -->

- ✓ Production deployment on Vercel serverless infrastructure — v1.1
- ✓ Single-project monorepo pattern (Next.js + Python in one Vercel project) — v1.1
- ✓ Native ASGI serverless conversion (no adapter needed) — v1.1
- ✓ MemorySaver for ephemeral in-memory checkpointing — v1.1
- ✓ Production CORS configured for *.vercel.app domains — v1.1
- ✓ Next.js standalone mode with environment templates — v1.1
- ✓ SSE streaming working in production environment — v1.1
- ✓ Comprehensive evaluation framework with 4-dimensional metrics — v1.1
- ✓ LLM-as-judge comparison with position bias mitigation — v1.1
- ✓ 5 benchmark scales (IPIP-NEO, PHQ-9, Social Connectedness, JSS, Environmental Attitudes) — v1.1
- ✓ 25 gold-standard test cases across psychological domains — v1.1
- ✓ Evaluation dashboard at /evaluation with automated metrics — v1.1
- ✓ Success criteria: ≥15% improvement + all dimensions ≥7.0/10 — v1.1
- ✓ Baseline comparison framework (current vs pre-optimization) — v1.1

### Validated

<!-- v2.0 Phase 8 -->

- ✓ Synthetic inter-item correlation analysis for generated item sets — Phase 8
- ✓ Correlation display card in results UI (visx heatmap with Psynalytics brand colors) — Phase 8
- ✓ McDonald's omega reliability metric (migrated from Cronbach's alpha) — Phase 8
- ✓ Calibration validation against 5 published psychological scales — Phase 8
- ✓ Internal consistency flagging (optimal/low/high based on mean inter-item r) — Phase 8
- ✓ CSV/JSON correlation export functions — Phase 8

### Active

<!-- v2.0 Psychometric Rigor -->

- [ ] Dynamic literature search for validated comparison instruments (replace hardcoded nearest neighbors)
- [ ] Cross-construct comparison against known validated instruments
- [ ] GPT 5.2 thinking mode configuration (high by default)

### Out of Scope

- Supabase integration — not needed, SQLite checkpoints sufficient
- User authentication system — keep open access for v1
- Mobile app development — web-first approach
- Real-time collaboration features — single-user workflow adequate
- Changing core frontend functionality — only add download button, model selector, export options
- Training custom embedding models — use LLM-as-judge instead of SurveyBot3000 approach
- Generating synthetic response data — LLM-as-judge validation sufficient for v1

## Context

**Current State (v1.1):**
- **Deployment**: Production at https://lmaig-langgraph.vercel.app/ (Vercel serverless, single-project monorepo)
- **Tech stack**: FastAPI + LangGraph + Next.js, Claude Opus/Sonnet, ~19,000 LOC (Python + TypeScript)
- **Architecture**: Native ASGI serverless, MemorySaver checkpointing, same-origin (no CORS)
- **7 specialized agents**: Web Surfer (evidence) → Item Writer (10 psychometric principles) → Validation Agent (4-dimensional scoring) → Parallel Reviews (Content, Linguistic, Bias) → Critic (adaptive thresholds) → Meta Editor (facet balancing) → loop or finalize
- **LLM-as-judge validation**: 7.0 threshold, max 3 retries, Claude Opus 4.6
- **Smart model allocation**: Opus for validation (accuracy), Sonnet for other agents (80% cost reduction)
- **Full metadata export**: CSV/JSON/Markdown with validation scores, review feedback, audit trail
- **Evidence sources**: Local markdown files + Perplexity academic search with domain allowlist
- **Frontend**: Next.js with model selector, export controls, SSE event streaming, evaluation dashboard
- **Backend**: FastAPI with MemorySaver (ephemeral checkpoints), streaming endpoints, evaluation API
- **Evaluation**: 4-dimensional metrics (quality, construct, style, psychometric), 5 benchmark scales (25 items), success criteria (≥15% improvement + dimensions ≥7.0)

**Research Foundation:**
- SurveyBot3000 paper (synthetic correlations) validates LLM-as-judge approach
- Psychometric test development literature (construct validity, item writing, bias minimization)
- 10 core principles integrated into Item Writer prompt
- 7-type bias taxonomy with intersectionality checks

**Known Issues (Tech Debt):**
- Phase 2 Nyquist validation gap (80% compliant, missing some automated test coverage)
- Phase 3 token tracking infrastructure ready but implementation deferred
- Cold start optimization deferred to v2 (DEP-08, ~3-8s typical)
- Missing navigation link to /evaluation dashboard (accessible via direct URL)
- Session resumption doesn't work after cold start (in-memory checkpoints only)

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
| Comprehensive evals (4 dimensions) | Need multiple lenses to validate system improvement (items, agents, workflow, validity) | ✓ Good — v1.1 shipped with 4-dimensional evaluation framework |
| Positive keying only (no reverse-scored items) | Research shows reverse-scored items reduce reliability and introduce method effects | ✓ Good — Item Writer enforces positive keying with rationale |
| Validation gate before reviewers (not after) | Catch fundamental construct misalignment early, save API costs on doomed items | ✓ Good — Prevents wasted reviewer cycles on invalid items |
| Single-project Vercel deployment (not two projects) | Simpler architecture, same-origin (no CORS), single environment config | ✓ Good — v1.1 deployed with monorepo pattern, documented in CLAUDE.md |
| Native ASGI (not Mangum adapter) | Vercel has native ASGI support; Mangum is AWS-specific and would fail | ✓ Good — Research corrected initial assumption, prevented deployment failure |
| MemorySaver checkpointing (not persistent storage) | Acceptable v1 trade-off: works during run, no cross-cold-start resumption | ✓ Good — Simplified deployment, session resumption deferred to v2 |
| Dual-direction comparison (position bias mitigation) | LLM-as-judge research shows position bias; evaluate both orderings and average | ✓ Good — 2x API cost acceptable for unbiased evaluation scoring |
| Simplified omega formula (not reliabiliPy) | reliabiliPy incompatible with scikit-learn 1.8.0; direct formula equivalent for tau-equivalent items | ✓ Good — Avoids dependency conflict, formula mathematically sound |
| Psynalytics brand colors for heatmap (teal-white-lime) | Brand consistency, avoids red-green colorblind issues | ✓ Good — Distinctive visual identity for correlation visualization |
| Collapsed correlation panel by default | Progressive disclosure reduces cognitive load | ✓ Good — Users expand on demand |

## Current Milestone: v2.0 Psychometric Rigor

**Goal:** Deepen construct validation by adding literature-grounded instrument comparison, synthetic inter-item correlations, and cross-construct analysis — transforming MAPIG from item-level validation to scale-level psychometric rigor.

**Target features:**
- Dynamic literature search for validated comparison instruments (replacing hardcoded org psych nearest neighbors)
- Synthetic inter-item correlation matrix for generated item sets
- Cross-construct comparison analysis against known validated instruments
- Correlation and comparison display card in results UI
- GPT 5.2 reasoning model support with high thinking mode by default

---
*Last updated: 2026-03-14 after Phase 8*
