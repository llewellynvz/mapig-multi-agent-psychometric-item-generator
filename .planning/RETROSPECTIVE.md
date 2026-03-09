# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MAPIG Production Optimization

**Shipped:** 2026-03-09
**Phases:** 5 (1-4, 3.1) | **Plans:** 17 | **Timeline:** 28 days

### What Was Built

- **LLM-as-Judge Validation Gate:** 4-dimensional scoring system (correspondence 50%, distinctiveness 25%, clarity 15%, specificity 10%) with automated quality control, 7.0 threshold, and smart retry logic (max 3 attempts)
- **Research-Backed Agent Optimization:** Enhanced Item Writer with 10 psychometric principles, semantic diversity controls, reading level targeting; refined all reviewers with research-backed criteria (7-type bias taxonomy, construct correspondence framework, vague quantifier rules)
- **Claude API Integration:** Smart model allocation achieving 80% cost reduction (Opus for validation, Sonnet for other agents) with OpenAI fallback
- **Enhanced Metadata Schema:** FinalOutput extended with user_request and review feedback arrays (backward compatible)
- **Production Export System:** Multi-format export (CSV, JSON, Markdown) with RFC 4180 compliance and complete audit trail (validation scores, review feedback, model info, iteration counts)

### What Worked

- **TDD methodology with test scaffolds:** Created pytest scaffolds with skip decorators first, enabling RED-GREEN-REFACTOR workflow without breaking builds
- **Research-driven optimization:** Deep literature review before prompt engineering led to evidence-based improvements (10 psychometric principles, 7-type bias taxonomy) rather than guesswork
- **Smart model allocation:** Early decision to use Opus only for validation and Sonnet for other agents achieved significant cost savings while maintaining quality
- **Decimal phase insertion:** Phase 3.1 seamlessly inserted for schema enhancement without disrupting roadmap numbering
- **Workflow agent integration:** GSD workflow with verification, plan checking, and validation agents caught issues early and ensured quality
- **Parallel execution:** Wave-based parallelization in Phase 2 (Item Writer, Bias Reviewer, Content/Linguistic Reviewer in parallel) maximized efficiency

### What Was Inefficient

- **Phase 2 Nyquist gap:** Agent prompt optimizations lacked automated test coverage, requiring retroactive validation
- **Multiple revision cycles:** Some plans (02-06, 03, 04) required plan checker feedback and revisions before execution, suggesting initial planning could be more thorough
- **Token tracking deferred:** Infrastructure built in Phase 3 but implementation deferred, leaving incomplete feature
- **AGT-11 ambiguity:** Optional requirement (A/B test Content + Bias consolidation) created confusion about phase completion criteria

### Patterns Established

- **Validation-first architecture:** Validate construct validity early (before reviewers) to prevent wasted cycles on fundamentally flawed items
- **Chain-of-thought scoring:** Require explicit reasoning before scores in validation rubrics (improves transparency and reliability)
- **Backward-compatible schema evolution:** Add optional fields with Field(default_factory=list) to extend schemas without breaking existing consumers
- **RFC 4180 CSV with UTF-8 BOM:** Standard CSV export format for Excel compatibility
- **Provider-agnostic LLM factory:** Abstract model provider selection to enable easy switching between Claude and OpenAI

### Key Lessons

1. **Research before implementation:** Deep literature review (psychometric test development principles) led to concrete, evidence-based improvements that would have been missed with intuition-based optimization
2. **Smart cost optimization over blanket cost-cutting:** Using premium models (Opus) for critical paths (validation) while using efficient models (Sonnet) elsewhere balances quality and cost better than using cheap models everywhere
3. **Test coverage gaps bite later:** Skipping automated tests for prompt optimizations (Phase 2) created technical debt that surfaced during milestone audit, requiring retroactive validation work
4. **Decimal phases for urgent insertions work well:** Phase 3.1 inserted cleanly without renumbering, maintaining clear execution order
5. **Optional requirements create ambiguity:** AGT-11 marked as optional led to confusion about whether Phase 2 was "complete" — better to defer to separate phase or mark as explicit tech debt

### Cost Observations

- Model mix: Primarily Sonnet for development with Opus for validation agent (estimated 20% Opus, 80% Sonnet)
- Sessions: Multiple across 28 days (exact count not tracked in v1.0)
- Notable: Smart model allocation achieved 80% cost reduction vs all-Opus approach while maintaining validation accuracy
- TDD approach frontloaded cost (test scaffolds) but reduced debugging/rework costs later

---

## Milestone: v1.1 — Deployment

**Shipped:** 2026-03-09
**Phases:** 2 (5-6) | **Plans:** 8 | **Timeline:** 1 day

### What Was Built

- **Production Deployment:** Single-project Vercel deployment at https://lmaig-langgraph.vercel.app/ with Next.js and Python serverless unified under one domain (monorepo pattern, no CORS needed)
- **Serverless Backend:** Native ASGI conversion with MemorySaver for ephemeral checkpointing, production CORS for *.vercel.app domains
- **Frontend Production Config:** Next.js standalone mode, environment templates, comprehensive deployment documentation
- **LLM-as-Judge Evaluation:** 4-dimensional item comparison (quality, construct, style, psychometric) with dual-direction evaluation to mitigate position bias
- **Benchmark Infrastructure:** 5 published scales (IPIP-NEO, PHQ-9, Social Connectedness, JSS, Environmental Attitudes) providing 25 gold-standard test cases
- **Evaluation Dashboard:** /evaluation route with automated quality metrics, baseline comparison, documented success criteria (≥15% improvement + dimensions ≥7.0)

### What Worked

- **Single-project deployment pattern:** Simplified from originally planned two-project setup; same-origin architecture eliminated CORS complexity
- **Native ASGI research:** Early research (05-RESEARCH.md) corrected Mangum assumption, preventing deployment failure
- **TDD with fast execution:** Test scaffolds (05-00) created first, enabling rapid verification throughout phases 5-6
- **Structured evaluation response:** 4-section JSON API format (current/baseline/improvement/success_criteria) eliminated frontend calculation complexity
- **Position bias mitigation:** Dual-direction comparison (forward + reverse) provided unbiased evaluation scores
- **Rapid execution:** 8 plans completed in single day with production deployment verified

### What Was Inefficient

- **Incomplete original completion:** Milestone was initially marked complete but lacked key accomplishments in MILESTONES.md and missing requirements archive
- **Plan 05-03 outdated architecture:** Plan referenced two-project setup (frontend + backend as separate Vercel projects) but actual implementation used single-project monorepo — plan adaptation required during execution
- **DEP-08 deferral:** Cold start optimization marked as requirement but deferred without explicit decision documentation until execution

### Patterns Established

- **Monorepo serverless pattern:** Next.js at root + Python in /api for unified Vercel deployment (single domain, no CORS, single environment config)
- **Ephemeral checkpointing trade-off:** MemorySaver acceptable for v1 (works during single run); persistent storage deferred to v2
- **Dual-direction comparison:** Evaluate both item orderings (generated→published, published→generated) and average to eliminate position bias
- **Structured evaluation JSON:** Return current/baseline/improvement/success_criteria sections to eliminate frontend recalculation

### Key Lessons

1. **Research corrects assumptions:** 05-RESEARCH.md definitively proved Vercel has native ASGI support (not Mangum); prevented deployment failure from wrong adapter
2. **Simplify architecture when possible:** Single Vercel project simpler than two-project setup; same-origin eliminates CORS, environment variables, preview URL complexity
3. **Document deferred requirements explicitly:** DEP-08 (cold start) should have been marked deferred in requirements, not left as incomplete — creates confusion during audit
4. **Complete all completion steps:** Milestone marked "complete" but lacked accomplishments in MILESTONES.md and requirements archive — better to complete all workflow steps at once
5. **Position bias matters:** LLM-as-judge research shows position bias is real; dual-direction evaluation worth 2x API cost for unbiased scores

### Cost Observations

- Model mix: Primarily Sonnet for development, Opus for evaluation comparison (estimated 30% Opus, 70% Sonnet)
- Sessions: 2 sessions (initial completion, retroactive completion of missing steps)
- Notable: Evaluation suite runs ~60s in mock mode (25 comparisons), production timing TBD
- TDD approach: Test scaffolds frontloaded time but caught issues early (e.g., DraftItem.item_text attribute)

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Timeline | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 28 days | 5 | First milestone - established GSD workflow patterns |
| v1.1 | 1 day | 2 | Rapid execution - deployment + evaluation framework in single day |

### Cumulative Quality

| Milestone | Plans | Nyquist Compliant | Tech Debt Items |
|-----------|-------|-------------------|-----------------|
| v1.0 | 17 | 4/5 phases (80%) | 2 (Nyquist gap, token tracking) |
| v1.1 | 8 | 2/2 phases (100%) | 2 (cold start optimization, eval dashboard nav link) |

### Top Lessons (Verified Across Milestones)

1. **Research-driven decisions prevent failures:** v1.0 (psychometric principles) and v1.1 (native ASGI) both benefited from upfront research correcting initial assumptions
2. **Simplicity wins when possible:** v1.1 single-project deployment simpler than two-project plan; v1.0 smart model allocation simpler than complex cost optimization
3. **Complete workflow steps together:** v1.1 initial completion missed accomplishments/requirements — better to finish all steps in one session
4. **TDD frontloads effort but reduces rework:** Both milestones used test scaffolds first; caught issues early (v1.0 validation logic, v1.1 DraftItem.item_text attribute)
