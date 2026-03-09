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

## Cross-Milestone Trends

### Process Evolution

| Milestone | Timeline | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 28 days | 5 | First milestone - established GSD workflow patterns |

### Cumulative Quality

| Milestone | Plans | Nyquist Compliant | Tech Debt Items |
|-----------|-------|-------------------|-----------------|
| v1.0 | 17 | 4/5 phases (80%) | 2 (Nyquist gap, token tracking) |

### Top Lessons (Verified Across Milestones)

1. *To be populated after v1.1+ when cross-milestone patterns emerge*
