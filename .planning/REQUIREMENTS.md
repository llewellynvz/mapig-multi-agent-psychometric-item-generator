# Requirements: MAPIG Production Optimization

**Defined:** 2026-03-08
**Core Value:** Generate psychometrically valid, production-ready assessment items with automated construct validation

## v1 Requirements

Requirements for production deployment milestone. Research-backed optimization followed by deployment.

### Phase 1: LLM-as-Judge Validation Gate

- [ ] **VAL-01**: Validation agent executes immediately after Item Writer, before reviewers
- [ ] **VAL-02**: Multi-dimensional scoring (correspondence 50%, distinctiveness 25%, clarity 15%, specificity 10%)
- [ ] **VAL-03**: Chain-of-thought prompting with explicit reasoning before scores
- [ ] **VAL-04**: 1-10 categorical scale with clear criterion definitions per level
- [ ] **VAL-05**: Automatic rejection threshold ≥7.0 for item acceptance
- [ ] **VAL-06**: Immediate retry logic (regenerate rejected items only, max 3 attempts)
- [ ] **VAL-07**: Claude Opus model for validation agent (highest accuracy)
- [ ] **VAL-08**: Validation scores and reasoning visible in results UI
- [ ] **VAL-09**: Export validation metadata (all dimension scores, reasoning, attempt count)

### Phase 2: Agent Architecture Optimization

- [ ] **AGT-01**: Refine Item Writer prompt with 10 core psychometric principles
- [ ] **AGT-02**: Add semantic diversity instructions to prevent over-paraphrasing
- [ ] **AGT-03**: Enforce reading level targeting (6th-8th grade general, 5th-6th clinical, 10th-12th specialized)
- [ ] **AGT-04**: Positive keying only (eliminate reverse-scored item generation)
- [ ] **AGT-05**: Refine Content Reviewer with construct correspondence criteria
- [ ] **AGT-06**: Refine Linguistic Reviewer with vague quantifier context rules
- [ ] **AGT-07**: Refine Bias Reviewer with 7-type taxonomy + intersectionality check
- [ ] **AGT-08**: Implement multi-pass bias review (separate evaluations per bias type)
- [ ] **AGT-09**: Update Meta Editor with facet balancing enforcement
- [ ] **AGT-10**: Enhance Critic with adaptive iteration thresholds (severity-based routing)
- [ ] **AGT-11**: Optional: A/B test Content + Bias reviewer consolidation (7→6 agents)

### Phase 3: Claude API Migration

- [ ] **API-01**: Add Anthropic SDK dependency to backend
- [ ] **API-02**: Update LLM factory to support Claude models (Opus, Sonnet, Haiku)
- [ ] **API-03**: Smart model allocation (Opus for validation, Sonnet for other agents)
- [ ] **API-04**: OpenAI fallback option (user-selectable)
- [ ] **API-05**: CLAUDE_API_KEY environment variable in Vercel
- [ ] **API-06**: UI model selector (Claude vs OpenAI, default Claude)
- [ ] **API-07**: Cost tracking per model (Opus vs Sonnet vs OpenAI)

### Phase 4: Production Features

- [ ] **FEAT-01**: Download button with format selector (Markdown, CSV, JSON)
- [ ] **FEAT-02**: Export full metadata (items + construct + constraints + evidence sources)
- [ ] **FEAT-03**: Include validation scores in export (all 4 dimensions + reasoning)
- [ ] **FEAT-04**: Include review feedback history in export
- [ ] **FEAT-05**: Export format selector UI component
- [ ] **FEAT-06**: Audit trail export (thread_id, run_id, iteration_count, model info)

### Phase 5: Vercel Deployment

- [ ] **DEP-01**: Convert FastAPI endpoints to Vercel serverless functions
- [ ] **DEP-02**: Adapt LangGraph state machine for serverless execution
- [ ] **DEP-03**: Maintain SQLite checkpoint compatibility (local storage)
- [ ] **DEP-04**: Deploy Next.js frontend to Vercel
- [ ] **DEP-05**: Configure CLAUDE_API_KEY and OPENAI_API_KEY in Vercel environment
- [ ] **DEP-06**: Production URL accessible and functional
- [ ] **DEP-07**: SSE streaming works in Vercel serverless environment
- [ ] **DEP-08**: Cold start optimization (<5s first request)

### Phase 6: Comprehensive Evaluation Framework

- [ ] **EVAL-01**: Item quality metrics (clarity score, bias score, construct validity score)
- [ ] **EVAL-02**: Agent performance metrics (accuracy, reliability per agent)
- [ ] **EVAL-03**: End-to-end workflow metrics (total time, iteration count, acceptance rate)
- [ ] **EVAL-04**: Benchmark constructs (5 test cases: personality, clinical, social, organizational, attitudes)
- [ ] **EVAL-05**: Compare generated items to published scales (expert comparison)
- [ ] **EVAL-06**: Automated eval suite runnable on demand
- [ ] **EVAL-07**: Success criteria: validation scores improve ≥15% vs baseline
- [ ] **EVAL-08**: Success criteria: generated items comparable to published scales

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Advanced Validation

- **VAL-10**: Embedding-based semantic redundancy detection (cosine similarity >0.85)
- **VAL-11**: Convergent/discriminant validity analysis with related constructs
- **VAL-12**: Factor analysis simulation (item-total correlations, factor loadings)

### Empirical Validation

- **EMP-01**: Collect empirical data with 200+ participants per construct
- **EMP-02**: Differential Item Functioning (DIF) analysis across demographic groups
- **EMP-03**: Measurement invariance testing across groups
- **EMP-04**: Correlation analysis with established scales
- **EMP-05**: Calibrate LLM-as-judge thresholds against empirical validity indices

### Advanced Features

- **FEAT-07**: Item bank repository (searchable library of generated items)
- **FEAT-08**: Construct search engine (find similar existing constructs)
- **FEAT-09**: Real-time collaboration (multi-user feedback on item sets)
- **FEAT-10**: Custom validation rubrics (user-defined scoring dimensions)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Training custom embedding models | LLM-as-judge validation sufficient, embedding approach has lower accuracy (r=0.59 vs 80% agreement) |
| Synthetic response generation | Complex, time-intensive; LLM-as-judge provides adequate validation for v1 |
| Supabase integration | SQLite checkpoints adequate, avoid unnecessary infrastructure |
| User authentication system | Single-user workflow sufficient for initial production deployment |
| Mobile app development | Web-first approach, responsive design covers mobile use cases |
| Real-time chat/collaboration | Not required for solo item generation workflow |
| Custom fine-tuning of LLMs | Pre-trained Claude Opus/Sonnet sufficient for psychometric tasks |
| Multi-language support | English-only for v1, international expansion requires DIF research |

## Traceability

Mapping requirements to phases. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| VAL-01 to VAL-09 | Phase 1 | Pending |
| AGT-01 to AGT-11 | Phase 2 | Pending |
| API-01 to API-07 | Phase 3 | Pending |
| FEAT-01 to FEAT-06 | Phase 4 | Pending |
| DEP-01 to DEP-08 | Phase 5 | Pending |
| EVAL-01 to EVAL-08 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 54 total
- Mapped to phases: 54
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 after research synthesis*
