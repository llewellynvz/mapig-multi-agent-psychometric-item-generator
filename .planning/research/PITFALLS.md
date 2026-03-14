# Pitfalls Research: v2.0 Psychometric Rigor

**Domain:** Adding LLM-based synthetic correlations, dynamic instrument comparison, and reasoning model integration to psychometric item generation system
**Researched:** 2026-03-14
**Confidence:** HIGH

---

## Critical Pitfalls

### Pitfall 1: Treating LLM Synthetic Correlations as Equivalent to Real Psychometric Data

**What goes wrong:**
LLMs estimate inter-item correlations without actual response data. Research shows sharp reductions in inter-item correlation (0.048–0.35 for personality inventories) and that LLMs primarily recognize explicit trait cues rather than express context-independent traits. Presenting synthetic correlations as validated psychometric evidence misleads users about scale reliability.

**Why it happens:**
- SurveyBot3000 validation creates false confidence in LLM correlation estimation
- LLMs can predict correlations for items they've seen during training (data contamination)
- Ensemble approaches (multiple LLMs) show improved accuracy but still fundamentally different from human response distributions
- Narrow proficiency distributions in LLMs limit variability mimicry

**How to avoid:**
1. **Label synthetic correlations explicitly**: "LLM-estimated (not empirically validated)"
2. **Show confidence intervals**: Display range, not point estimates
3. **Validate against known scales first**: Test correlation estimation on benchmark instruments with published correlation matrices before production use
4. **Document limitations prominently**: Warning card in UI explaining these are predictions, not validations
5. **Use ensemble approach**: Combine 3+ different LLM providers (GPT-4, Claude, Gemini) to approximate broader distribution
6. **Add data contamination check**: If correlations are suspiciously high (>0.8) for novel constructs, flag potential training data overlap

**Warning signs:**
- Correlation estimates above 0.7 for items without semantic overlap
- Perfect rank-order preservation across all item pairs
- Unrealistically narrow confidence intervals (<0.05 range)
- Correlations identical across different LLM providers (suggests training data contamination)
- User feedback: "These correlations don't match our pilot data"

**Phase to address:**
Phase 1 (Correlation Agent Design) — Build validation framework BEFORE production release

---

### Pitfall 2: Copyright Infringement Through Dynamic Instrument Search

**What goes wrong:**
Dynamic literature search retrieves copyrighted psychometric instruments (e.g., NEO-PI-R, MMPI-3, Beck Depression Inventory). Displaying items verbatim, using them for comparison, or extracting them into training data violates copyright. Publishers like Pearson, Hogrefe, and PAR actively protect test materials. Legal risk includes DMCA claims, licensing violations, and IP litigation.

**Why it happens:**
- Academic papers quote items for methodological purposes (fair use for scholarship ≠ fair use for commercial tool)
- Perplexity/academic search returns full-text PDFs with embedded items
- LLMs trained on published instruments can reconstruct copyrighted items from memory
- Difference between "comparison analysis" (risky) and "literature reference" (safer) is unclear

**How to avoid:**
1. **Allowlist public-domain instruments only**: IPIP, Public-domain scales, NIH Toolbox (open-access components)
2. **Block known copyrighted publishers**: Exclude doi.org/10.1037 (APA PsycTests), Pearson, Hogrefe, PAR in Perplexity domain filter
3. **Extract metadata, not items**: Store construct name, citation, facet structure — NEVER store verbatim item text
4. **Implement plagiarism detection**: Check generated items against retrieved instruments using text similarity (cosine >0.85 = likely plagiarism)
5. **User disclaimer**: "Comparison uses published constructs, not copyrighted items. For validated instruments, contact test publisher."
6. **Add manual review gate**: Flag any comparison involving NEO, MMPI, BDI, PHQ-9 commercial versions for human approval before display

**Warning signs:**
- Retrieved documents from Pearson Clinical, Hogrefe, or PAR websites
- Perplexity results include "Purchase instrument at..." links
- Generated items score >0.85 semantic similarity to retrieved comparison items
- User uploads copyrighted instrument PDF to "approved sources"
- Legal inquiry email from test publisher

**Phase to address:**
Phase 2 (Dynamic Literature Search) — Implement copyright safeguards BEFORE enabling Perplexity integration

---

### Pitfall 3: Invalid Cross-Construct Comparisons Due to LLM Evaluation Artifacts

**What goes wrong:**
LLM-as-judge comparison between generated items and validated instruments produces inflated similarity scores due to position bias, prompt sensitivity, and lack of construct validity. Trivial prompt perturbations cause up to 76% variation in task accuracy. Changing subject from human to statistical model severs score from original interpretive foundation. Users trust comparison scores that don't reflect actual psychometric equivalence.

**Why it happens:**
- Position bias: LLMs favor first-presented option (A vs B ≠ B vs A)
- Evaluation degrees of freedom: Prompt framing, few-shot count, chain-of-thought, tool use all shift scores meaningfully
- Construct validity gap: LLM benchmarks systematically violate psychometric principles (poorly defined constructs, inconsistent operationalization)
- No human response data to anchor comparison

**How to avoid:**
1. **Dual-direction comparison (already implemented in v1.1 evaluation)**: Compare A→B and B→A, then average (mitigates position bias)
2. **Standardized comparison prompt**: Lock prompt template, disable chain-of-thought for consistency
3. **Multi-dimensional scoring**: Don't reduce to single similarity score — report correspondence, distinctiveness, semantic overlap, facet alignment separately
4. **Benchmark against known relationships**: Test comparison on instruments with established nomological network (e.g., NEO-IPIP facets) to validate comparison accuracy
5. **Show comparison reasoning**: Display LLM's chain-of-thought so users can assess logic quality
6. **Comparison confidence score**: Flag comparisons with high prompt sensitivity (run 3x with minor prompt variations; if scores vary >15%, mark LOW confidence)

**Warning signs:**
- Comparison scores flip when order reversed (>10% delta)
- All comparisons score 7.5-8.5 regardless of construct distance
- Comparison reasoning contains generic phrases ("both measure psychological traits")
- Users report: "Our pilot data shows weak correlation but MAPIG says strong match"
- Comparison changes significantly with minor prompt rewording

**Phase to address:**
Phase 3 (Cross-Construct Comparison) — Add dual-direction scoring and benchmark validation

---

### Pitfall 4: GPT-5.2 Reasoning Token Cost Explosion

**What goes wrong:**
GPT-5.2 thinking mode generates internal reasoning tokens (invisible via API) billed as output tokens ($14/1M). A 500-token visible response may consume 2000+ total tokens (4x cost multiplier). Running validation agent with thinking mode on 50 items × 3 retries = $5-15 per run vs. current $0.50-2.00. Monthly costs explode from $50-200 to $500-3000 for moderate usage. Users don't see cost increase until bill arrives.

**Why it happens:**
- Reasoning tokens are hidden but billable (no API visibility into internal chain-of-thought length)
- "High" thinking mode (default recommendation) maximizes reasoning tokens for accuracy
- Multiple validation attempts multiply reasoning overhead
- No real-time cost feedback in current UI
- Thinking effort scales non-linearly with task complexity (50-item validation may trigger 10x reasoning vs. 5-item)

**How to avoid:**
1. **Thinking mode selector in UI**: Low/Medium/High dropdown with cost multiplier warning ("High mode: ~4-6x cost")
2. **Budget caps per run**: Set max thinking tokens allowed (e.g., 50k tokens = $0.70), abort if exceeded
3. **Adaptive thinking allocation**: Use "Low" for initial drafts, "Medium" for revision, "High" only for final validation
4. **Real-time cost estimation**: Show projected cost BEFORE starting generation ("Estimated: $1.50-3.00 with High thinking")
5. **Fallback to non-reasoning models**: If run exceeds budget, switch to Claude Sonnet (no reasoning tokens)
6. **Post-run cost breakdown**: Display thinking vs. output tokens separately in audit metadata
7. **Cache reasoning outputs**: Store thinking paths for identical validation scenarios (Vercel KV or Redis)

**Warning signs:**
- Actual cost 5-10x higher than projected cost
- OpenAI usage dashboard shows output tokens >> visible response length
- Validation timeouts despite Vercel 300s limit (reasoning tokens slow generation)
- User complaints: "Why did this cost $8 when the quote said $1?"
- Monthly bill jumps 10x after enabling GPT-5.2 thinking

**Phase to address:**
Phase 4 (GPT-5.2 Integration) — Build cost controls BEFORE enabling reasoning models

---

### Pitfall 5: Serverless Timeout with Multi-Step Correlation Analysis

**What goes wrong:**
Vercel serverless functions timeout at 300s (Pro plan) or 800s (Fluid Compute). Synthetic correlation analysis requires N×(N-1)/2 pairwise comparisons: 50 items = 1,225 comparisons. At 200ms per LLM call (item pair → correlation estimate), total time = 245s (sequential) or 25s (10-parallel workers). Add dynamic literature search (10-30s), item generation (20-40s), validation (10-20s), reviews (15-25s), and total exceeds 300s. Cold start adds 3-8s. Function times out, user loses entire session (MemorySaver is ephemeral).

**Why it happens:**
- Correlation analysis added to existing 60-120s workflow pushes total over timeout
- LangGraph sequential execution for some nodes (can't parallelize correlation matrix computation safely)
- No persistent checkpointing beyond function lifetime (MemorySaver limitation)
- Thinking tokens slow GPT-5.2 calls to 500-1000ms each
- No queue-based architecture for long-running tasks

**How to avoid:**
1. **Streaming correlation computation**: Return partial correlation matrix via SSE as computed (user sees progress, can resume if timeout)
2. **Persistent checkpointing (Vercel Postgres + PostgresSaver)**: Store LangGraph state in database so cold-start resumption works
3. **Correlation caching**: For identical item pairs, cache correlation estimates (Redis/Vercel KV) to avoid redundant LLM calls
4. **Hybrid execution**: Run correlation agent as separate endpoint (`/v1/compute-correlations`) invoked AFTER item generation completes
5. **Timeout warning UI**: If item count > 30, show "Correlation analysis may timeout. Consider reducing item count or splitting into batches."
6. **Fluid Compute upgrade**: Document in deployment guide that correlation feature requires 800s timeout (paid feature)
7. **Fallback to approximate correlations**: If timeout approaching, switch to correlation estimation for subset (e.g., 10 representative items) instead of full matrix

**Warning signs:**
- Runs with >30 items frequently timeout
- SSE stream cuts off mid-correlation computation
- Users report: "Clicked generate, waited 4 minutes, got 504 error"
- Vercel logs show "Function invocation exceeded maximum duration"
- Cold start happens during active session (indicates timeout/restart cycle)

**Phase to address:**
Phase 1 (Correlation Agent Design) AND Phase 5 (Integration & UI) — Architecture decisions in Phase 1, deployment config in Phase 5

---

### Pitfall 6: Replacing Hardcoded Nearest Neighbors Without Validation Strategy

**What goes wrong:**
Current content reviewer uses hardcoded organizational psychology neighbors (job satisfaction, work engagement, commitment, etc.). Replacing with dynamic literature-based neighbors risks retrieving irrelevant constructs (e.g., clinical constructs for workplace assessment), missing domain-specific competitors, or retrieving too many neighbors (15+ constructs) that dilute distinctiveness evaluation. LLM picks constructs based on semantic similarity without psychometric logic.

**Why it happens:**
- Semantic similarity ≠ psychometric competitor (e.g., "stress" semantically similar to "burnout" but measuring different facets)
- Literature search returns broad construct landscape, not narrow competitor set
- No validation that dynamic neighbors match expert judgment
- Hardcoded defaults are psychometrically informed (based on meta-analytic evidence of construct overlap)

**How to avoid:**
1. **Hybrid approach**: Dynamic neighbors as supplement, not replacement — keep hardcoded defaults + add literature-based neighbors
2. **Neighbor filtering criteria**: Limit to 5-8 neighbors max, ranked by: (1) same domain (work/clinical/social), (2) empirical correlation >0.3, (3) cited in same nomological network
3. **Validation benchmark**: Compare dynamic neighbors vs. expert-curated neighbors for 10 test constructs; if agreement <70%, flag for review
4. **User override**: Allow users to provide custom neighbor constructs in UI (advanced mode)
5. **Neighbor provenance**: Display WHERE dynamic neighbors came from ("Based on Smith et al. 2023 meta-analysis") so users can assess credibility
6. **Fallback to defaults**: If literature search returns 0 relevant neighbors, use hardcoded defaults instead of leaving blank

**Warning signs:**
- Content reviewer identifies 15+ neighbor constructs for single assessment
- Neighbors span multiple unrelated domains (workplace + clinical + educational)
- Dynamic neighbors have zero semantic overlap with target construct
- Distinctiveness scores drop significantly after enabling dynamic neighbors (suggests contamination from irrelevant competitors)
- User feedback: "Why is 'schizophrenia' listed as competitor for 'team cohesion'?"

**Phase to address:**
Phase 2 (Dynamic Literature Search) — Validate neighbor selection logic before deprecating hardcoded defaults

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use GPT-5.2 thinking mode for all agents | Higher accuracy, simpler architecture | 4-10x cost increase, slower generation, budget unpredictability | NEVER — restrict to validation/critic only |
| Skip dual-direction comparison for cross-construct scoring | 50% fewer API calls, faster results | Position bias inflates scores by 10-25%, unreliable comparisons | Never for production — only acceptable for internal testing |
| Cache correlation estimates indefinitely | Faster repeat runs, cost savings | Stale estimates as models improve, no expiration = gradual drift | Acceptable with 30-day TTL and version tagging |
| Store retrieved instrument items in database | Easier comparison, faster lookup | Copyright violation risk, potential DMCA claims | NEVER — metadata only |
| Use MemorySaver instead of PostgresSaver | Simpler deployment, no database setup | Session loss on cold start, no resumption after timeout | Acceptable for MVP if runs stay <120s |
| Hardcode thinking mode to "low" globally | Predictable costs, faster execution | Lower validation accuracy, more manual review needed | Acceptable if validated empirically vs. High mode |
| Sequential correlation computation | Simpler implementation, easier debugging | N² time complexity, timeout risk for >30 items | Never for production — only acceptable for <15 items |
| Single LLM provider for correlation ensemble | Lower API complexity, faster setup | Narrow distribution, training data contamination risk | Acceptable if paired with strong validation benchmarks |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GPT-5.2 Reasoning API | Assume visible tokens = billed tokens | Track `usage.completion_tokens` (includes reasoning) separately from output; display both in audit |
| Perplexity Academic Search | Use default domain filter (all academic sites) | Restrict to public-domain sources: `doi.org/10.1371` (PLOS), `arxiv.org`, `nih.gov`, EXCLUDE `doi.org/10.1037` (APA PsycTests) |
| PostgresSaver Checkpointing | Deploy without connection pooling | Use PgBouncer or Vercel Postgres connection pooling (serverless functions exhaust connections) |
| LangGraph Parallel Nodes | Run correlation agent in parallel with reviewers | Correlation agent must run AFTER item finalization (needs stable item set) — add to `finalize_node` or separate endpoint |
| Correlation Matrix Caching | Cache by item text only | Cache key = `hash(item_text + model_provider + thinking_mode + version)` to prevent stale data |
| Dynamic Neighbor Retrieval | Retrieve neighbors synchronously during validation | Pre-fetch neighbors in `retrieve_node` (parallel with evidence retrieval) to avoid blocking validation |
| SSE Streaming for Correlations | Stream raw correlation values as computed | Stream progress percentage + partial matrix (user can render heatmap incrementally) |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| N² Correlation API Calls | Linear item count increase causes exponential cost/time growth | Use correlation caching + batch API calls (50 pairs per request if model supports) | >30 items (1,225+ comparisons) |
| Reasoning Token Amplification | Expected $1 run costs $8, no visibility into why | Add thinking token budget caps + real-time cost tracking with abort threshold | First GPT-5.2 run with thinking mode enabled |
| Cold Start During Correlation | 3-8s cold start mid-run resets in-memory correlation cache | Use persistent cache (Redis/Vercel KV) instead of in-memory dict | Every cold start with >10 items |
| Literature Search Timeout | Perplexity API takes 15-40s for complex queries, blocking workflow | Run literature search in parallel with local retrieval, set 20s timeout with fallback to local-only | Constructs with broad literature (e.g., "personality") |
| Checkpoint Size Explosion | GraphState with 50 items + 1,225 correlations + literature results = 2-5MB, Postgres INSERT slow | Compress correlation matrix (store upper triangle only), use JSONB column with GIN index | >50 items or >20 literature results |
| Validation Retry Loop | 3 validation attempts × 50 items × GPT-5.2 reasoning = 150+ slow calls | Use smart validation (already implemented) + adaptive thinking mode (Low → Medium → High across retries) | First retry with thinking mode on High |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing copyrighted instrument items in logs/checkpoints | DMCA claims, licensing violations, legal liability | Redact item text from logs; store only hash fingerprints for comparison |
| Exposing Perplexity API key in client-side code | Key theft, API quota exhaustion, cost abuse | Keep all API keys server-side; use environment variables only |
| No rate limiting on correlation endpoint | API cost abuse (user generates 1000-item scale × 499,500 comparisons) | Add rate limit: max 100 items per request, 10 requests per hour per IP |
| Caching correlation estimates without user isolation | User A sees User B's private construct correlations | Use cache key with user_id or thread_id prefix (or disable caching for multi-tenant) |
| Allowing user-provided LLM prompts for comparison | Prompt injection to extract copyrighted items or manipulate scores | Use fixed prompt templates only; sanitize user input to remove prompt delimiters |
| No validation on literature search domain filter | User adds `doi.org/10.1037` to retrieve copyrighted APA tests | Server-side validation of domain filter against blocklist before Perplexity call |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Displaying correlation heatmap with no confidence intervals | Users treat estimates as validated data | Show correlation ± 95% CI (from ensemble spread); label "LLM-estimated" |
| No cost warning before enabling GPT-5.2 thinking mode | Bill shock when user enables High thinking globally | Modal dialog: "High thinking mode increases cost 4-6x. Estimated: $X-Y. Continue?" |
| Literature comparison shows "8.2/10 similarity" with no context | Users think generated items are psychometrically equivalent to validated scale | Multi-dimensional breakdown: Correspondence 7.5, Distinctiveness 8.0, Facet Alignment 9.0 — explain meaning |
| Correlation matrix for 50 items is overwhelming (50×50 grid) | Users can't identify patterns or actionable insights | Show summary statistics: mean inter-item r, Cronbach's α, flag problematic items (r<0.2 or r>0.9) |
| Dynamic neighbors change between runs for same construct | Inconsistent feedback confuses users ("Why was 'burnout' a competitor yesterday but not today?") | Cache neighbor set per construct for 30 days; show "Updated: 2026-03-10" timestamp |
| Timeout happens at 290s with no partial results | User loses 5 minutes of work and all progress | Stream partial results continuously; display "Computation interrupted. Showing 35/50 items completed." |
| Copyright disclaimer buried in footer | Users unknowingly violate copyright by using comparison feature for commercial instruments | Prominent warning card on comparison UI: "Public-domain instruments only. Do not upload copyrighted tests." |

---

## "Looks Done But Isn't" Checklist

- [ ] **Correlation Feature:** Often missing confidence intervals — verify ensemble approach provides spread, not just point estimates
- [ ] **Literature Search:** Often missing copyright safeguards — verify publisher blocklist AND plagiarism detection active
- [ ] **Cross-Construct Comparison:** Often missing dual-direction scoring — verify A→B and B→A both computed and averaged
- [ ] **GPT-5.2 Integration:** Often missing cost cap enforcement — verify budget exceeded triggers abort, not silent cost explosion
- [ ] **Persistent Checkpointing:** Often missing connection pooling — verify PgBouncer or equivalent prevents connection exhaustion
- [ ] **Correlation Caching:** Often missing invalidation strategy — verify TTL set and version-tagged keys prevent stale data
- [ ] **Thinking Mode Selector:** Often missing cost multiplier display — verify UI shows "$X-Y (4-6x with High mode)" BEFORE user submits
- [ ] **Timeout Handling:** Often missing partial result streaming — verify SSE emits progress events during correlation computation
- [ ] **Neighbor Validation:** Often missing fallback to defaults — verify empty literature search doesn't leave neighbor set blank
- [ ] **Audit Trail:** Often missing thinking token breakdown — verify `audit.reasoning_tokens` tracked separately from `output_tokens`

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Copyright infringement complaint | HIGH (legal fees, settlement, code removal) | 1. Remove copyrighted content immediately; 2. Audit all literature sources for publisher; 3. Implement blocklist; 4. Add plagiarism check; 5. Legal review before re-launch |
| Reasoning token cost explosion | MEDIUM (refund users, rewrite cost logic) | 1. Add retrospective cost cap (abort if exceeded); 2. Refund overcharged users; 3. Implement budget warnings; 4. Switch to adaptive thinking mode |
| Serverless timeout with no resumption | LOW (user retries with fewer items) | 1. Enable PostgresSaver checkpointing; 2. Add timeout warning in UI; 3. Document Fluid Compute upgrade path; 4. Implement streaming partial results |
| Invalid correlation estimates (failed validation) | MEDIUM (disable feature, retrain ensemble) | 1. Disable correlation UI; 2. Run benchmark validation on known scales; 3. Tune ensemble weights or prompt; 4. Re-enable with confidence scores |
| Position bias in comparison scores | LOW (re-run comparisons with dual-direction) | 1. Add dual-direction scoring (already in v1.1 eval); 2. Re-compute affected comparisons; 3. Update audit to log both directions |
| Dynamic neighbors include irrelevant constructs | LOW (rollback to hardcoded defaults) | 1. Revert to hardcoded defaults; 2. Add domain filtering to literature search; 3. Validate neighbor selection on benchmark; 4. Re-enable with filtering |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Synthetic correlation validity (Pitfall 1) | Phase 1: Correlation Agent Design | Test on 5 benchmark scales with published correlation matrices; agreement >0.6 required |
| Copyright infringement (Pitfall 2) | Phase 2: Dynamic Literature Search | Manual review of 20 literature search results; zero copyrighted items retrieved |
| Invalid cross-construct comparison (Pitfall 3) | Phase 3: Cross-Construct Comparison | Dual-direction scoring delta <10% on 10 test comparisons |
| Reasoning token cost explosion (Pitfall 4) | Phase 4: GPT-5.2 Integration | Cost estimate vs. actual cost delta <20% on 10 test runs |
| Serverless timeout (Pitfall 5) | Phase 1 (architecture) + Phase 5 (deployment) | 50-item correlation analysis completes in <240s on 3 consecutive runs |
| Invalid dynamic neighbors (Pitfall 6) | Phase 2: Dynamic Literature Search | Expert review of neighbors for 10 constructs; agreement >70% with hardcoded defaults |
| All integration pitfalls | Phase 5: Integration & UI | End-to-end test with 30 items, literature search, correlation, comparison — completes without errors |
| All UX pitfalls | Phase 6: Documentation & Testing | User testing with 5 non-expert users; 4/5 understand correlation limitations and cost warnings |

---

## Sources

**Psychometric Validity & LLM Limitations:**
- [LLM Psychometric Personality Assessment](https://www.emergentmind.com/topics/psychometric-personality-assessment-in-llms)
- [A psychometric framework for evaluating and shaping personality traits in large language models - Nature Machine Intelligence](https://www.nature.com/articles/s42256-025-01115-6)
- [Large Language Model Psychometrics: A Systematic Review](https://arxiv.org/html/2505.08245v1)
- [Psychometric Item Validation Using Virtual Respondents](https://arxiv.org/html/2507.05890)
- [Leveraging LLM Respondents for Item Evaluation: A Psychometric Analysis](https://bera-journals.onlinelibrary.wiley.com/doi/10.1111/bjet.13570?af=R)
- [AI can outperform humans in predicting correlations between personality items](https://www.nature.com/articles/s44271-025-00205-w)

**Construct Validity & LLM Benchmarks:**
- [Measuring what Matters: Construct Validity in Large Language Model Benchmarks](https://arxiv.org/pdf/2511.04703)
- [Medical Large Language Model Benchmarks Should Prioritize Construct Validity](https://arxiv.org/html/2503.10694v1)

**Copyright & Psychometric Instruments:**
- [Psychometric scales, copyright protection and translation - UCL Copyright Queries](https://blogs.ucl.ac.uk/copyright/2017/11/17/psychometric-scales-copyright-protection-and-translation/)
- [Copyright and Tests - Health Sciences Library System](https://hsls.libguides.com/tests-measures/copyright)
- [Commentary: Copyright Restrictions versus Open Access to Survey Instruments](https://pmc.ncbi.nlm.nih.gov/articles/PMC5766425/)

**GPT-5.2 Reasoning Model Pricing:**
- [GPT-5.2 Model | OpenAI API](https://platform.openai.com/docs/models/gpt-5.2)
- [OpenAI API Pricing 2026](https://devtk.ai/en/blog/openai-api-pricing-guide-2026/)
- [OpenAI O3 Model Pricing Drops 80%](https://apidog.com/blog/o3-api-pricing/)
- [OpenAI for Developers in 2025](https://developers.openai.com/blog/openai-for-developers-2025/)

**Serverless & LangGraph Architecture:**
- [Unlocking AI Resilience: Mastering State Persistence with LangGraph and PostgreSQL](https://dev.to/programmingcentral/unlocking-ai-resilience-mastering-state-persistence-with-langgraph-and-postgresql-50h0)
- [Mastering LangGraph Checkpointing: Best Practices for 2025](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)
- [Serverless 2026: The next frontier of cold-start optimization and persistent state](https://medium.com/@naeemulhaq/serverless-2026-the-next-frontier-of-cold-start-optimization-and-persistent-state-4e1c3fdc5cec)
- [What can I do about Vercel Functions timing out?](https://vercel.com/kb/guide/what-can-i-do-about-vercel-serverless-functions-timing-out)
- [Stop Losing LangGraph Progress to 429 Errors](https://www.ezthrottle.network/blog/stop-losing-langgraph-progress)

---

*Pitfalls research for: MAPIG v2.0 Psychometric Rigor milestone*
*Researched: 2026-03-14*
*Confidence: HIGH (Context7 unavailable, but official docs + recent 2025-2026 research papers provide strong evidence)*
