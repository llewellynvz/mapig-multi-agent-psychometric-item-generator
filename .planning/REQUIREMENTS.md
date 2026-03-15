# Requirements: MAPIG v2.0 Psychometric Rigor

**Defined:** 2026-03-14
**Core Value:** Generate psychometrically valid, production-ready assessment items with automated construct validation that ensures items truly measure what they claim to measure, backed by established test development principles.

## v2.0 Requirements

Requirements for v2.0 milestone. Each maps to roadmap phases.

### Synthetic Correlations

- [x] **CORR-01**: System generates LLM-estimated inter-item correlation matrix for finalized item sets without requiring response data
- [x] **CORR-02**: System computes Cronbach's alpha from synthetic correlation matrix with minimum threshold flag (alpha >= 0.70)
- [x] **CORR-03**: System provides confidence intervals for each synthetic correlation estimate
- [x] **CORR-04**: System validates synthetic correlations against 5+ published scales with known correlation matrices (benchmark: r > 0.6 agreement)
- [x] **CORR-05**: System labels all synthetic correlations as "LLM-estimated, not empirically validated" in UI and exports
- [x] **CORR-06**: System computes internal consistency flags (mean inter-item correlation in 0.15-0.50 optimal range)

### Instrument Comparison

- [x] **INST-01**: System dynamically searches for validated comparison instruments via Perplexity Academic based on user's construct definition
- [x] **INST-02**: System replaces hardcoded org psych nearest neighbor constructs with literature-grounded search results
- [x] **INST-03**: System uses hybrid approach for neighbor constructs (hardcoded defaults + literature supplements, fallback to defaults if search fails)
- [x] **INST-04**: System provides convergent validity evidence by comparing generated items to instruments measuring the same construct
- [x] **INST-05**: System enforces copyright safeguards (public-domain allowlist, publisher blocklist, metadata-only storage, never store copyrighted item text)
- [x] **INST-06**: System detects potential plagiarism by flagging generated items with cosine similarity > 0.85 to retrieved instrument items

### Cross-Construct Comparison

- [x] **XCON-01**: System assesses discriminant validity by comparing generated items against instruments measuring related-but-distinct constructs
- [x] **XCON-02**: System uses dual-direction LLM-as-judge scoring (A to B and B to A averaged) to mitigate position bias in cross-construct comparisons
- [x] **XCON-03**: System provides automated validity flagging (correlation > 0.85 with related construct = discriminant validity concern)
- [x] **XCON-04**: System identifies related-but-distinct constructs for comparison using dynamic neighbor discovery (validated against expert-curated at > 70% agreement)

### Visualization & UI

- [x] **UI-01**: User can view correlation heatmap for generated item set using visx visualization
- [x] **UI-02**: User can view psychometric analytics panel below results showing correlation matrix, comparison instruments, and cross-construct analysis
- [x] **UI-03**: User can view comparison display card showing matched validated instruments with source citations
- [x] **UI-04**: User can view cross-construct comparison table with discriminant validity assessments
- [x] **UI-05**: User can export correlation matrices in CSV and JSON formats with labeled rows/columns
- [x] **UI-06**: All new UI components match existing shadcn/ui design patterns and Radix primitives

### GPT-5.2 Reasoning Models

- [ ] **GPT-01**: System supports GPT-5.2 reasoning model with configurable reasoning effort (none/low/medium/high/xhigh)
- [x] **GPT-02**: System defaults to high reasoning effort for GPT-5.2 analytics tasks
- [x] **GPT-03**: User can toggle GPT-5.2 for analytics via UI with cost warning modal (4-6x multiplier displayed)
- [x] **GPT-04**: System enforces budget caps per run and aborts if reasoning token cost exceeds threshold
- [x] **GPT-05**: System provides post-run audit breakdown showing reasoning tokens vs output tokens separately

### Infrastructure

- [x] **INFRA-01**: GraphState schema extended with CorrelationMatrix, ComparisonInstrument, and CrossConstructComparison types
- [x] **INFRA-02**: FinalOutput schema extended with correlation_matrix, comparison_instruments, and cross_construct_analysis fields
- [x] **INFRA-03**: Analytics nodes execute post-finalize in parallel using LangGraph Send API (correlation, comparison, cross-construct simultaneously)
- [x] **INFRA-04**: Analytics failures handled gracefully (populate null values, item generation completes successfully)
- [x] **INFRA-05**: llm_factory.py supports GPT-5.2 reasoning models with hardcoded high reasoning effort for analytics tasks

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Psychometrics

- **ADV-01**: System computes polychoric/tetrachoric correlations for ordinal Likert data
- **ADV-02**: System predicts factor structure from item text alone (CFA without response data)
- **ADV-03**: System provides model fit indices (RMSEA, CFI, TLI) for predicted factor structure
- **ADV-04**: System supports multi-model synthetic validation (compare Claude + GPT-5.2 estimates for higher confidence)

### Visualization Enhancements

- **VIS-01**: System displays nomological network visualization (graph showing construct relationships)
- **VIS-02**: System provides instrument versioning and run comparison across sessions

### Performance

- **PERF-01**: System uses persistent checkpointing (Vercel Postgres + PostgresSaver) for timeout resumption
- **PERF-02**: System caches correlation results (Redis/Vercel KV) for identical item pairs

## Out of Scope

| Feature | Reason |
|---------|--------|
| Generating synthetic response data | LLMs as respondents have narrow variability, semantic drift, "AI-slop" contamination risk |
| Causal claims from correlations | Correlation != causation; fundamental misinterpretation risk |
| Treating synthetic correlations as empirical | Synthetic estimates are predictions, not observations; claiming equivalence damages credibility |
| IRT parameter estimation without data | IRT requires response data; difficulty/discrimination estimates from text alone are unreliable |
| Recursive AI training on generated items | "AI-slop" degrades training data; pollutes item pools with derivative content |
| Correlation "cut-offs" as absolute rules | Context-dependent; provide guidance ranges, not hard thresholds |
| Generating reverse-scored items | Research shows reverse-scored items reduce reliability and introduce method effects |
| Full instrument item text display | Copyright restrictions; store metadata only, never copyrighted item text |

## Traceability

Which phases cover which requirements. Updated after roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 7 | Complete |
| INFRA-02 | Phase 7 | Complete |
| INFRA-05 | Phase 7 | Pending |
| CORR-01 | Phase 8 | Complete |
| CORR-02 | Phase 8 | Complete |
| CORR-03 | Phase 8 | Complete |
| CORR-04 | Phase 8 | Complete |
| CORR-05 | Phase 8 | Complete |
| CORR-06 | Phase 8 | Complete |
| UI-01 | Phase 8 | Complete |
| UI-05 | Phase 8 | Complete |
| INST-01 | Phase 9 | Complete |
| INST-02 | Phase 9 | Complete |
| INST-03 | Phase 9 | Complete |
| INST-04 | Phase 9 | Complete |
| INST-05 | Phase 9 | Complete |
| INST-06 | Phase 9 | Complete |
| XCON-01 | Phase 9 | Complete |
| XCON-02 | Phase 9 | Complete |
| XCON-03 | Phase 9 | Complete |
| XCON-04 | Phase 9 | Complete |
| UI-02 | Phase 9 | Complete |
| UI-03 | Phase 9 | Complete |
| UI-04 | Phase 9 | Complete |
| GPT-01 | Phase 10 | Pending |
| GPT-02 | Phase 10 | Complete |
| GPT-03 | Phase 10 | Complete |
| GPT-04 | Phase 10 | Complete |
| GPT-05 | Phase 10 | Complete |
| INFRA-03 | Phase 10 | Complete |
| INFRA-04 | Phase 10 | Complete |
| UI-06 | Phase 10 | Complete |

**Coverage:**
- v2.0 requirements: 28 total
- Mapped to phases: 28 (100% coverage)
- Unmapped: 0

**Phase distribution:**
- Phase 7 (Foundation & Infrastructure): 3 requirements
- Phase 8 (Synthetic Correlation Analysis): 8 requirements
- Phase 9 (Dynamic Instrument Comparison): 14 requirements
- Phase 10 (GPT-5.2 Integration & Analytics Optimization): 8 requirements

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-15 (Phase 10 Plan 01 complete - GPT-02, GPT-04, GPT-05, INFRA-03, INFRA-04 verified)*
