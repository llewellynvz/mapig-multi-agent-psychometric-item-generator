# MAPIG: Production Psychometric Item Generator

## What This Is

MAPIG is a multi-agent platform for generating psychometrically sound assessment items, currently using OpenAI. We are upgrading it to a production-ready system powered by Claude API with research-backed agent optimization, automated construct validation, and production deployment capabilities. The system generates items for psychological assessments (personality, clinical, organizational, social psychology) with explicit evidence trails and human-in-the-loop refinement.

## Core Value

Generate psychometrically valid, production-ready assessment items with automated construct validation that ensures items truly measure what they claim to measure, backed by established test development principles.

## Requirements

### Validated

<!-- Existing capabilities from current system -->

- ✓ 7-agent workflow (Web Surfer, Item Writer, Content Reviewer, Linguistic Reviewer, Bias Reviewer, Meta Editor, Critic) — existing
- ✓ Evidence-bounded generation from approved sources (local + Perplexity academic search) — existing
- ✓ Iterative review/revision cycles with human feedback loops — existing
- ✓ LangGraph state machine with SQLite checkpointing for run recovery — existing
- ✓ FastAPI backend with SSE streaming for real-time progress — existing
- ✓ Next.js frontend with guided Setup → Run → Results flow — existing
- ✓ Typed schemas (Pydantic) enforcing contracts between agents — existing
- ✓ Audit metadata tracking (thread_id, run_id, iteration_count, evidence sources) — existing
- ✓ Constraint model (baseline + user constraints) — existing
- ✓ Mock mode for testing without API keys — existing

### Active

<!-- Current milestone scope - optimize and deploy -->

**1. Claude API Migration**
- [ ] Smart model allocation: Opus for validation, Sonnet for other agents
- [ ] Support OpenAI as fallback option (user-selectable)
- [ ] UI model selector (Claude vs OpenAI, default to Claude)
- [ ] Environment variable management (CLAUDE_API_KEY in Vercel)
- [ ] Update LLM factory to support Anthropic SDK

**2. LLM-as-Judge Construct Validation**
- [ ] New validation agent with 1-10 numeric scoring
- [ ] Validate items immediately after Item Writer (before reviews)
- [ ] Automatic rejection and regeneration for items scoring <7
- [ ] Immediate retry logic (regenerate rejected items only)
- [ ] Max 3 retry attempts before proceeding with best-scoring items
- [ ] Validation scores visible in results UI

**3. Research-Backed Agent Optimization**
- [ ] Deep literature review: psychometric test development principles
- [ ] Research focus: construct validity, item writing best practices, bias minimization
- [ ] Analyze current 7-agent architecture against research findings
- [ ] Propose new agent structure OR refine existing agents (research decides)
- [ ] Optimize all agent prompts with explicit psychometric principles
- [ ] Document evidence-based rationale for all changes

**4. Production Features**
- [ ] Multi-format download button (Markdown, CSV, JSON)
- [ ] Export full metadata (items + construct + constraints + evidence + audit trail + validation scores)
- [ ] Export format selector in UI
- [ ] Review feedback included in exports

**5. Deployment to Vercel**
- [ ] Convert FastAPI to Vercel serverless functions
- [ ] Deploy Next.js frontend to Vercel
- [ ] Configure environment variables (API keys) in Vercel
- [ ] Maintain SQLite checkpoints (no Supabase needed)
- [ ] Production URL accessible for live testing

**6. Comprehensive Evaluation Framework**
- [ ] Eval 1: Item quality metrics (clarity, bias, construct validity)
- [ ] Eval 2: Agent performance metrics (accuracy, reliability per agent)
- [ ] Eval 3: End-to-end system quality (full workflow assessment)
- [ ] Eval 4: Construct validity benchmarks (compare to published scales)
- [ ] Success criteria: Higher validation scores + favorable benchmark comparison
- [ ] Automated eval suite runnable on demand

### Out of Scope

- Supabase integration — not needed, SQLite checkpoints sufficient
- User authentication system — keep open access for v1
- Mobile app development — web-first approach
- Real-time collaboration features — single-user workflow adequate
- Changing core frontend functionality — only add download button, model selector, export options
- Training custom embedding models — use LLM-as-judge instead of SurveyBot3000 approach
- Generating synthetic response data — LLM-as-judge validation sufficient for v1

## Context

**Existing System:**
- 7 specialized agents in LangGraph workflow: Web Surfer (evidence) → Item Writer (draft) → Parallel Reviews (Content, Linguistic, Bias) → Critic (decision) → Meta Editor (revision) → loop or finalize
- Evidence sources: local markdown files + Perplexity academic search with domain allowlist
- Frontend: Next.js with form validation, SSE event streaming, sessionStorage persistence
- Backend: FastAPI with AsyncSqliteSaver checkpoints, streaming endpoints
- Current model: OpenAI (gpt-4o-mini default)

**Research Foundation:**
- SurveyBot3000 paper (synthetic correlations) provides validation approach concept
- LLM-as-judge chosen over embedding similarity for transparency and reasoning
- Psychometric test development literature guides agent optimization
- Construct validity, item writing standards, bias minimization as core principles

**Production Requirements:**
- Items must be production-ready for psychological assessments
- Critical quality focus: these are real assessment items, not prototypes
- Evidence-based changes only (research-backed improvements)
- Automated validation ensures construct measurement integrity

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
| Claude API (not OpenAI) as default | Superior reasoning capabilities for psychometric validation, better prompt following for complex agent tasks | — Pending |
| LLM-as-judge validation (not embedding similarity) | Transparent reasoning, explicit scoring, aligns with research-backed validation | — Pending |
| Smart model allocation (Opus validation, Sonnet others) | Balance quality and cost; validation is critical path, other agents less demanding | — Pending |
| Vercel serverless deployment (not traditional hosting) | Simplified deployment, automatic scaling, cost-effective for intermittent use | — Pending |
| No Supabase (keep SQLite) | Current checkpointing sufficient, avoid unnecessary complexity | — Pending |
| Research-driven optimization (not intuition-based) | Psychometric validity requires evidence-based practices, not guesswork | — Pending |
| Multi-format export (MD/CSV/JSON) | Different use cases require different formats (documentation vs analysis) | — Pending |
| Comprehensive evals (4 dimensions) | Need multiple lenses to validate system improvement (items, agents, workflow, validity) | — Pending |

---
*Last updated: 2026-03-08 after initialization via /gsd:new-project*
