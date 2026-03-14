# Project Research Summary

**Project:** MAPIG v2.0 - Psychometric Rigor (Synthetic Correlations, Instrument Comparison, Reasoning Models)
**Domain:** Multi-agent psychometric item generation with construct validation
**Researched:** 2026-03-14
**Confidence:** MEDIUM-HIGH

## Executive Summary

MAPIG v2.0 aims to add scale-level psychometric rigor through three key capabilities: synthetic inter-item correlation analysis, dynamic comparison with validated instruments, and advanced reasoning model integration (GPT-5.2/o3). Research shows this is achievable using the existing LangGraph architecture with a post-finalize analytics branch pattern, avoiding disruption to the validated v1.1 workflow.

The recommended approach leverages LLM-estimated synthetic correlations (validated in recent research with r=0.61-0.75 predictive accuracy), Perplexity Academic search for dynamic instrument discovery, and GPT-5.2 reasoning models for deep validity analysis. Critical stack decisions include: NumPy-only correlation computation to avoid pandas bloat (Vercel 250 MB serverless limit), visx React library for heatmap visualization, and langchain-openai 2.x upgrade for reasoning model support. The architecture follows a parallel analytics pattern where correlation, comparison, and cross-construct nodes execute after item finalization but before final output.

Key risks center on: (1) treating synthetic correlations as equivalent to empirical data (mitigation: explicit labeling, confidence intervals, benchmark validation), (2) copyright infringement through dynamic literature search (mitigation: public-domain allowlist, metadata-only storage), (3) GPT-5.2 reasoning token cost explosion (mitigation: budget caps, adaptive thinking mode allocation), and (4) serverless timeout with multi-step analytics (mitigation: streaming partial results, persistent checkpointing, 800s Fluid Compute upgrade). All risks have identified mitigations that can be implemented during phased rollout.

## Key Findings

### Recommended Stack

v2.0 extends the existing FastAPI + LangGraph + Next.js serverless stack with minimal new dependencies, prioritizing compatibility with Vercel's 250 MB function limit and existing architecture patterns.

**Core technologies:**
- **NumPy 2.1.x (backend)**: Correlation matrix computation with `np.corrcoef()` — lightweight alternative to pandas (20-30 MB vs 100-150 MB), likely already in transitive dependencies
- **langchain-openai 2.x (upgrade from 1.1.7)**: GPT-5.2, o3, o1 reasoning model support with `reasoning.effort` parameter — enables deep validity analysis with configurable thinking depth
- **visx (frontend)**: React + D3 heatmap visualization (~28 KB gzipped) — tree-shakeable, Airbnb-maintained, integrates with existing shadcn/Radix patterns
- **Perplexity API Academic mode (existing)**: Dynamic literature search with scholarly source prioritization — already integrated, no new dependencies required

**Critical constraint:** Vercel serverless function size limit (250 MB uncompressed). Current stack (~100 MB) + NumPy (~30 MB) = ~130 MB total, leaving 120 MB buffer. If exceeded, fallback to client-side correlation computation (pure TypeScript, ~30 lines).

**Alternatives avoided:** pandas (too heavy for serverless), embedding models (abandoned in v1.0, requires PyTorch ~500 MB), D3 directly (lower-level than needed), MUI X Charts (design system conflict).

### Expected Features

Research identifies a clear split between table stakes (expected by users familiar with psychometric tools) and differentiators (unique capabilities not offered by traditional item generators).

**Must have (table stakes):**
- Inter-item correlation matrix display — standard psychometric output in ShinyItemAnalysis, jMetrik, Xcalibre
- Internal consistency metrics (Cronbach's alpha) — fundamental reliability measure, minimum standard is α ≥ 0.70
- Correlation visualization (heatmap) — raw matrices hard to interpret, visual display expected
- Convergent validity evidence — demonstrates items measure the same construct (required for construct validation)
- Discriminant validity evidence — demonstrates items don't measure unrelated constructs (required for construct validation)
- Validated instrument search — replace hardcoded nearest neighbors with dynamic literature-grounded comparisons

**Should have (competitive):**
- LLM-estimated synthetic correlations (SurveyBot3000 approach) — generate correlation matrices WITHOUT response data; competitive advantage (r=0.61-0.75 predictive accuracy)
- Dynamic instrument repository search — auto-discover validated comparison instruments from literature, not hardcoded lists
- Cross-construct comparison against published items — compare generated items directly to gold-standard instruments
- Confidence intervals for synthetic correlations — quantify uncertainty, build trust in LLM estimates
- Multi-model synthetic validation — compare Claude + GPT-5.2 estimates for higher confidence
- Automated convergent/discriminant flagging — proactive quality control before data collection

**Defer (v2+):**
- Polychoric/tetrachoric correlations — marginal benefit over Pearson for synthetic estimates (no actual ordinal response data)
- Nomological network visualization — high complexity graph display, correlation matrix provides same information
- Factor structure prediction with CFA — requires structural equation modeling, defer to v3
- Model fit indices (RMSEA, CFI, TLI) — requires factor analysis implementation, defer to v3

### Architecture Approach

All three v2.0 features operate on finalized items (not drafts), making them ideal for a post-finalize analytics branch that runs after validation completes but before final output. This pattern preserves the validated v1.1 workflow while adding psychometric rigor as a parallel enhancement layer.

**Major components:**

1. **Psychometric Analytics Node (fanout)** — Triggers parallel execution of three analytics branches using LangGraph's Send API; isolates analytics failures from item generation
2. **Correlation Node** — Generates synthetic correlations using LLM-estimated item relationships; computes Pearson correlations, Cronbach's alpha, internal consistency flags
3. **Comparison Node** — Enhances existing Web Surfer agent to search for validated instruments measuring same construct; extracts instrument metadata (names, citations, psychometric properties) without storing copyrighted items
4. **Cross-Construct Node** — Assesses discriminant validity by comparing generated items to instruments measuring related-but-distinct constructs; uses dual-direction LLM-as-judge scoring to mitigate position bias
5. **Analytics Aggregator Node** — Merges results from parallel branches back into FinalOutput schema; gracefully handles analytics failures (populate null values, allow generation to complete)

**Graph structure:**
```
finalize_node → psychometric_analytics_node (fanout)
                  ├─> correlation_node ────┐
                  ├─> comparison_node ──────┤
                  └─> cross_construct_node ─┘
                            ↓
                  analytics_aggregator_node → END
```

**Key decisions:**
- Run analytics POST-finalize (not during generation) — avoids wasting API cost on items that fail validation
- Use parallel execution (Send API) — correlation, comparison, cross-construct run simultaneously for faster results
- Fail gracefully (null values if analytics error) — analytics are enhancements, not requirements for successful generation
- Reuse existing agents (enhance Web Surfer, extend Validation Agent) — minimal code duplication, proven patterns
- Optional GPT-5.2 integration — user toggle in UI with cost warning, defaults to existing models

### Critical Pitfalls

Research identified six critical pitfalls with specific prevention strategies and phase assignments.

1. **Treating LLM Synthetic Correlations as Empirical Data** — LLMs estimate correlations without response data; inter-item correlations show sharp reductions (0.048-0.35 range) and data contamination risk. Prevention: explicit labeling ("LLM-estimated, not empirically validated"), confidence intervals, benchmark validation on 5+ known scales before production, ensemble approach (3+ LLM providers), prominent limitations documentation in UI.

2. **Copyright Infringement Through Dynamic Instrument Search** — Perplexity retrieves copyrighted psychometric instruments (NEO-PI-R, MMPI-3, BDI); displaying items violates copyright. Prevention: allowlist public-domain sources only (IPIP, NIH Toolbox), block copyrighted publishers in domain filter (doi.org/10.1037 = APA PsycTests), store metadata NEVER item text, plagiarism detection (flag generated items with cosine >0.85 to retrieved items), prominent user disclaimer.

3. **Invalid Cross-Construct Comparisons (LLM-as-Judge Artifacts)** — Position bias, prompt sensitivity cause up to 76% variation in task accuracy; comparisons inflate similarity scores. Prevention: dual-direction comparison (A→B and B→A averaged, already in v1.1 evaluation), standardized prompt templates, multi-dimensional scoring (not single similarity score), benchmark against known nomological networks, display reasoning chain for user assessment, flag comparisons with high prompt sensitivity (>15% score variance).

4. **GPT-5.2 Reasoning Token Cost Explosion** — Reasoning tokens (invisible via API) billed as output tokens; 500-token visible response may consume 2000+ total tokens (4x cost multiplier). Prevention: thinking mode selector in UI with cost multiplier warning ("High mode: ~4-6x cost"), budget caps per run, adaptive thinking allocation (Low for drafts → High for final validation), real-time cost estimation BEFORE generation, fallback to non-reasoning models if budget exceeded, post-run thinking vs output token breakdown in audit.

5. **Serverless Timeout with Multi-Step Correlation Analysis** — Vercel 300s timeout; 50 items = 1,225 pairwise comparisons at 200ms each = timeout risk when combined with generation workflow. Prevention: streaming correlation computation (partial results via SSE), persistent checkpointing (Vercel Postgres + PostgresSaver for resumption after cold start), correlation caching (Redis/Vercel KV for identical item pairs), hybrid execution (separate endpoint for correlation vs inline), timeout warning UI for >30 items, Fluid Compute upgrade to 800s documented, fallback to approximate correlations (subset of representative items).

6. **Replacing Hardcoded Nearest Neighbors Without Validation** — Current content reviewer uses psychometrically-informed hardcoded org psych neighbors; dynamic search risks irrelevant constructs (semantic similarity ≠ psychometric competitor). Prevention: hybrid approach (keep hardcoded defaults + supplement with literature-based), neighbor filtering (max 5-8 neighbors, domain-matched, empirical correlation >0.3), validation benchmark (dynamic vs expert-curated agreement >70% required), user override capability, neighbor provenance display (cite sources), fallback to defaults if search fails.

## Implications for Roadmap

Based on research, suggested phase structure follows a low-risk-to-high-risk progression with validation gates between phases.

### Phase 1: Foundation & Schema Extensions
**Rationale:** Establish data structures and GPT-5.2 infrastructure before implementing analytics features; enables parallel work on Phases 2-4.
**Delivers:** GraphState schema extensions (CorrelationMatrix, ComparisonInstrument, CrossConstructComparison), FinalOutput schema fields, GPT-5.2 support in llm_factory with reasoning.effort parameter, placeholder analytics nodes in graph builder.
**Addresses:** Technical debt avoidance (schema changes before implementation).
**Avoids:** N/A (foundational phase, no user-facing features).
**Research needed:** NO — standard Pydantic schema design, documented GPT-5.2 API structure.

### Phase 2: Synthetic Correlation Analysis
**Rationale:** Highest-value differentiator with moderate risk; correlation computation is well-understood (NumPy `np.corrcoef()`); validates architecture pattern before more complex features.
**Delivers:** Correlation node implementation (synthetic response generation + Pearson correlation), correlation heatmap display (visx), Cronbach's alpha computation, internal consistency flags, correlation matrix export (CSV/JSON).
**Addresses:** Table stakes (correlation matrix display, internal consistency metrics, correlation visualization) + differentiator (LLM-estimated synthetic correlations).
**Avoids:** Pitfall 1 (treating synthetic as empirical) via explicit labeling, confidence intervals, benchmark validation on 5 known scales; Pitfall 5 (serverless timeout) via streaming partial results.
**Uses:** NumPy (STACK.md), visx (STACK.md).
**Implements:** Correlation Node (ARCHITECTURE.md post-finalize analytics pattern).
**Research needed:** NO — established psychometric practice, NumPy well-documented; BUT requires empirical validation (benchmark testing on 5+ published scales with known correlation matrices).

### Phase 3: Dynamic Literature Search & Instrument Comparison
**Rationale:** Builds on existing Web Surfer infrastructure; enables Phase 4 (cross-construct requires comparison instruments); moderate copyright risk requires careful safeguards.
**Delivers:** Web Surfer enhancement with `surf_for_instruments()` variant, comparison node implementation (literature search for validated instruments), comparison instruments display panel, copyright safeguards (public-domain allowlist, publisher blocklist, metadata-only storage), plagiarism detection (cosine similarity >0.85 flag).
**Addresses:** Table stakes (validated instrument search, convergent validity evidence) + differentiator (dynamic instrument repository search).
**Avoids:** Pitfall 2 (copyright infringement) via public-domain allowlist (IPIP, NIH Toolbox, arxiv.org, PLOS), blocklist (doi.org/10.1037 APA PsycTests, Pearson, Hogrefe, PAR), metadata-only storage, prominent user disclaimer; Pitfall 6 (invalid dynamic neighbors) via hybrid approach (hardcoded + literature), filtering (max 5-8, domain-matched), validation benchmark (>70% agreement).
**Uses:** Perplexity Academic mode (STACK.md), existing Web Surfer agent patterns.
**Implements:** Comparison Node (ARCHITECTURE.md).
**Research needed:** MAYBE — test Perplexity Academic search ability to retrieve full instrument details vs just citations; validate on 10 known constructs (job satisfaction, burnout, engagement) before broader rollout.

### Phase 4: Cross-Construct Comparison Analysis
**Rationale:** Requires Phase 3 (comparison instruments) as dependency; highest psychometric sophistication; leverages proven v1.1 LLM-as-judge validation pattern.
**Delivers:** Cross-construct node implementation (discriminant validity assessment), dual-direction LLM-as-judge scoring (A→B and B→A averaged), multi-dimensional scoring breakdown (correspondence, distinctiveness, facet alignment), cross-construct comparison display table, automated validity flagging (correlation >0.85 = potential discriminant validity issue).
**Addresses:** Table stakes (discriminant validity evidence) + differentiator (cross-construct comparison against published items).
**Avoids:** Pitfall 3 (invalid cross-construct comparison) via dual-direction scoring (already in v1.1 evaluation framework), standardized prompts, multi-dimensional breakdown, benchmark validation on known nomological networks (e.g., NEO-IPIP facets), reasoning chain display for user assessment.
**Uses:** Existing Validation Agent LLM-as-judge pattern (ARCHITECTURE.md).
**Implements:** Cross-Construct Node (ARCHITECTURE.md).
**Research needed:** YES — requires identifying appropriate comparison constructs for each user request; test automated neighbor discovery on 10 benchmark constructs; validate dual-direction scoring reduces position bias to <10% delta.

### Phase 5: Parallel Analytics Integration & Performance Optimization
**Rationale:** All three analytics features implemented (Phases 2-4); refactor to parallel execution for performance; add persistent checkpointing to enable timeout resumption.
**Delivers:** Psychometric analytics fanout node (Send API parallel execution), analytics aggregator node (merge results), Vercel Postgres integration (PostgresSaver for persistent checkpointing), correlation caching (Redis/Vercel KV), streaming progress events (SSE), timeout warning UI (>30 items), Fluid Compute upgrade documentation (800s timeout).
**Addresses:** Performance optimization (parallel vs sequential ~3x speedup).
**Avoids:** Pitfall 5 (serverless timeout) via persistent checkpointing (resumption after cold start), caching (avoid redundant API calls), streaming (partial results), Fluid Compute 800s upgrade path.
**Uses:** LangGraph Send API (ARCHITECTURE.md parallel workflows), Vercel Postgres (deferred from v1.1).
**Implements:** Psychometric Analytics Node + Analytics Aggregator Node (ARCHITECTURE.md).
**Research needed:** NO — LangGraph Send API well-documented; BUT requires load testing (50-item correlation analysis completes in <240s on 3 consecutive runs).

### Phase 6: GPT-5.2 Reasoning Model Integration
**Rationale:** All analytics features functional (Phases 2-4); GPT-5.2 adds depth to validity analysis but introduces cost risk; optional feature with user opt-in.
**Delivers:** UI toggle for GPT-5.2 analytics (with cost warning modal), reasoning effort selector (none/low/medium/high/xhigh), cost multiplier display ("High mode: ~4-6x cost"), budget caps per run (abort if exceeded), adaptive thinking allocation (Low for drafts → High for final validation), post-run audit breakdown (reasoning tokens vs output tokens), fallback logic (GPT-4o-mini if GPT-5.2 unstable or budget exceeded).
**Addresses:** Differentiator (multi-model synthetic validation via GPT-5.2 deep reasoning).
**Avoids:** Pitfall 4 (reasoning token cost explosion) via cost warning modal BEFORE generation, budget caps (abort at threshold), adaptive thinking mode (task-specific allocation), real-time cost estimation, audit trail breakdown (reasoning vs output tokens separately), fallback to non-reasoning models.
**Uses:** langchain-openai 2.x (STACK.md upgrade), GPT-5.2 reasoning.effort parameter.
**Implements:** Model factory enhancement (ARCHITECTURE.md).
**Research needed:** YES — langchain-openai 2.x compatibility issues documented (GitHub issues #29632, #29947); requires thorough testing of upgrade impact on existing gpt-4o calls; A/B comparison (GPT-4o-mini vs GPT-5.2 high effort) to validate accuracy improvement justifies cost increase.

### Phase Ordering Rationale

- **Phase 1 before all others:** Schema changes must happen before implementation to avoid refactoring; GPT-5.2 infrastructure needed by Phases 4 and 6.
- **Phase 2 early (correlation):** Validates post-finalize analytics architecture pattern before more complex features; highest user value (differentiator); moderate risk with clear mitigations.
- **Phase 3 before Phase 4 (comparison → cross-construct):** Cross-construct analysis requires comparison instruments as input; copyright safeguards must be validated before broader feature rollout.
- **Phase 4 standalone (cross-construct):** Most psychometrically sophisticated; benefits from proven dual-direction scoring pattern (v1.1 evaluation); can fail gracefully without blocking Phases 2-3.
- **Phase 5 after Phases 2-4 (performance optimization):** Requires all analytics features implemented; parallel execution refactor avoids premature optimization; persistent checkpointing deferred until analytics features validated.
- **Phase 6 last (GPT-5.2):** Highest cost risk; optional enhancement not blocker; benefits from analytics features being functional with existing models; langchain-openai 2.x compatibility concerns warrant careful testing after core features stable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Dynamic Literature Search):** Requires testing Perplexity Academic mode's ability to retrieve full instrument details (construct name, facets, validation citations) vs just paper abstracts; validate on 10-20 known constructs (job satisfaction, burnout, engagement, Big Five facets) to ensure retrieval quality before production.
- **Phase 4 (Cross-Construct Comparison):** Requires automated identification of related-but-distinct constructs for discriminant validity testing; test neighbor discovery algorithm on benchmark constructs with established nomological networks (e.g., NEO-IPIP) to validate >70% agreement with expert-curated neighbors.
- **Phase 6 (GPT-5.2 Integration):** langchain-openai 2.x upgrade shows ongoing compatibility issues (GitHub issues #29632, #29947, #32714); requires thorough testing of `max_completion_tokens` vs deprecated `max_tokens` parameter; validate A/B comparison (GPT-4o-mini baseline vs GPT-5.2 high/xhigh effort) to quantify accuracy improvement vs cost increase trade-off.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Standard Pydantic schema design, documented GPT-5.2 API structure (official OpenAI docs).
- **Phase 2 (Correlation):** NumPy `np.corrcoef()` well-documented, established psychometric practice (Cronbach's alpha, inter-item correlation ranges); visx heatmap has extensive examples and tutorials.
- **Phase 5 (Performance):** LangGraph Send API well-documented with map-reduce examples; Vercel Postgres integration standard pattern (already researched for v1.1 deferred feature).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | NumPy, visx, Perplexity well-documented; langchain-openai 2.x has known compatibility issues (MEDIUM) but mitigations identified (fallback to 1.1.7, test thoroughly) |
| Features | HIGH | SurveyBot3000 research validates synthetic correlation approach (r=0.61-0.75 predictive accuracy); table stakes identified from psychometric software analysis (ShinyItemAnalysis, jMetrik); differentiators grounded in Nature publications |
| Architecture | HIGH | Post-finalize analytics pattern proven in LangGraph workflows; reuses v1.1 validation patterns (dual-direction scoring, LLM-as-judge); Send API parallel execution well-documented |
| Pitfalls | HIGH | All six critical pitfalls have identified prevention strategies with specific implementation steps; phase-to-pitfall mapping clear; recovery strategies documented for each |

**Overall confidence:** MEDIUM-HIGH

Primary uncertainty: langchain-openai 2.x stability (GitHub issues show ongoing parameter compatibility problems with o3 models) and Vercel serverless size constraint (NumPy may push total function size close to 250 MB limit).

### Gaps to Address

Research identified specific gaps requiring validation during implementation:

- **NumPy serverless size validation:** Current stack (~100 MB) + NumPy (~30 MB) approaches Vercel 250 MB limit with ~120 MB buffer. Mitigation: deploy to preview environment in Phase 2, check function size in logs; if >200 MB warning, fallback to client-side correlation computation (pure TypeScript implementation, ~30 lines).

- **Perplexity instrument retrieval quality:** Unknown if Perplexity Academic mode can retrieve full instrument metadata (construct name, facet structure, validation citations, psychometric properties) vs just paper abstracts. Mitigation: test on 10-20 known constructs (job satisfaction, burnout, engagement, Big Five facets) in Phase 3 before production; if retrieval insufficient, supplement with Semantic Scholar API for citation metadata.

- **langchain-openai 2.x upgrade impact:** GitHub issues (#29632, #29947, #32714) show `max_completion_tokens` parameter compatibility problems; upgrade may break existing gpt-4o calls. Mitigation: test upgrade in isolation in Phase 1; validate all existing agent calls (Item Writer, Bias Reviewer, Critic) still work; keep fallback to langchain-openai 1.1.7 if breaking changes detected.

- **GPT-5.2 cost vs accuracy trade-off:** Unknown if accuracy improvement justifies 4-6x cost increase for validation tasks. Mitigation: A/B comparison in Phase 6 (GPT-4o-mini baseline vs GPT-5.2 high/xhigh effort) on 20+ test cases; measure validation accuracy delta; document cost multiplier; default to GPT-4o-mini unless user explicitly enables GPT-5.2.

- **Correlation estimation benchmark validation:** LLM synthetic correlations must be validated against known scales before production to avoid Pitfall 1 (treating as empirical data). Mitigation: test correlation estimation in Phase 2 on 5+ published scales with known correlation matrices (e.g., IPIP Big Five, PHQ-9, GAD-7); require r>0.6 agreement between LLM-estimated and published correlations; document limitations prominently in UI.

- **Dynamic neighbor discovery validation:** Automated identification of related-but-distinct constructs for discriminant validity testing must match expert judgment. Mitigation: test neighbor discovery in Phase 4 on 10+ benchmark constructs with established nomological networks (NEO-IPIP facets, org psych meta-analyses); require >70% agreement with expert-curated neighbors; hybrid approach (keep hardcoded defaults + supplement with literature) ensures fallback.

## Sources

### Primary (HIGH confidence)

**Synthetic Correlations & LLM Psychometrics:**
- [Language Models Accurately Infer Correlations Between Psychological Items](https://journals.sagepub.com/doi/10.1177/25152459251377093) — SurveyBot3000 validates synthetic predictions with r=0.75 in-sample, r=0.61 out-of-sample for 449 scales
- [Rethinking psychometrics through LLMs: how item semantics shape measurement](https://www.nature.com/articles/s41598-025-21289-8) — Semantic similarity matrices correlate highly with empirical data; LLMs predict item correlations without observations
- [A psychometric framework for evaluating and shaping personality traits in large language models](https://www.nature.com/articles/s42256-025-01115-6) — Inter-item correlations in LLMs range 0.048-0.35 (BFI), 0.22-0.31 (scenarios)

**Stack & Technology:**
- [NumPy correlation documentation](https://numpy.org/doc/stable/reference/generated/numpy.corrcoef.html) — Official NumPy API docs for Pearson correlation
- [visx GitHub - Airbnb visualization components](https://github.com/airbnb/visx) — React + D3 heatmap components (19.9k stars)
- [GPT-5.2 API documentation](https://developers.openai.com/api/docs/models/gpt-5.2) — Official OpenAI reasoning.effort parameter docs
- [LangChain Issue #29632 - Extend support for OpenAI o3 style models](https://github.com/langchain-ai/langchain/issues/29632) — Known compatibility issues with reasoning models

**Architecture & LangGraph:**
- [Parallel workflows in LangGraph](https://medium.com/@ameejais0999/parallel-workflows-in-langgraph-a-practical-approach-6e4340ceb8d4) — Send API parallel execution pattern
- [Best practices for scale development and validation](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/) — Psychometric validation protocol (CFA, RMSEA ≤0.06, CFI ≥0.95)

**Pitfalls & Validation:**
- [Psychometric scales, copyright protection and translation](https://blogs.ucl.ac.uk/copyright/2017/11/17/psychometric-scales-copyright-protection-and-translation/) — Copyright restrictions on test instruments
- [Measuring what Matters: Construct Validity in Large Language Model Benchmarks](https://arxiv.org/pdf/2511.04703) — LLM evaluation artifacts (position bias, prompt sensitivity, up to 76% variation)
- [Vercel Functions Limits](https://vercel.com/docs/functions/limitations) — 250 MB uncompressed limit, 300s timeout (Pro), 800s (Fluid Compute)

### Secondary (MEDIUM confidence)

**Feature Landscape:**
- [ShinyItemAnalysis](https://shinyitemanalysis.org/) — Standard psychometric software features (correlation matrices, reliability, validity analysis)
- [Mental Measurements Yearbook](https://guides.nyu.edu/tests/finding-info) — Comprehensive guide to 2,000+ contemporary testing instruments

**Deployment & Performance:**
- [Mastering LangGraph Checkpointing: Best Practices for 2025](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025) — PostgresSaver persistent checkpointing patterns
- [OpenAI API Pricing 2026](https://devtk.ai/en/blog/openai-api-pricing-guide-2026/) — GPT-5.2 reasoning token pricing ($14/1M output tokens)

### Tertiary (LOW confidence)

**Emerging Research:**
- [Leveraging LLM-Respondents for Item Evaluation](https://arxiv.org/abs/2407.10899) — LLM respondents produce item parameters with r>0.8 correlation to human data (needs empirical validation)
- [Semantic embeddings reveal and address taxonomic incommensurability](https://www.nature.com/articles/s41562-024-02089-y) — Semantic embeddings predict psychometric properties; r=0.75 observed vs predicted internal consistency (emerging approach)

---
*Research completed: 2026-03-14*
*Ready for roadmap: yes*
