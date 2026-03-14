# Validation Methods for LLM-Generated Psychometric Items

**Domain:** Construct Validation for Psychometric Assessment
**Researched:** 2026-03-08
**Overall confidence:** MEDIUM-HIGH

## Executive Summary

Construct validation ensures psychometric items truly measure their intended psychological constructs. For LLM-generated items, validation requires both classical psychometric approaches (convergent/discriminant validity, factor analysis, internal consistency) and modern LLM-as-judge methods. The SurveyBot3000 paper demonstrates embedding-based validation achieving r=0.59-0.84 accuracy, but LLM-as-judge offers superior transparency through explicit reasoning and multi-dimensional scoring. Best practices include: (1) chain-of-thought prompting for transparent scoring, (2) multi-dimensional rubrics assessing correspondence, distinctiveness, and clarity, (3) categorical integer scales (0-4 or 1-10) with clear criterion definitions, and (4) validation thresholds based on established psychometric standards (item-total r>0.30, factor loadings>0.55, convergent r>0.50, discriminant r<0.70).

## Table Stakes: Classical Validation Methods

Methods researchers expect. Missing = validation incomplete.

| Method | Purpose | Threshold | Complexity | Evidence Source |
|--------|---------|-----------|------------|-----------------|
| **Convergent Validity** | Items measuring same construct correlate highly | r > 0.50, AVE > 0.50 | Medium | [Cambridge BJPsych](https://www.cambridge.org/core/journals/bjpsych-advances/article/development-validation-and-translation-of-psychological-tests/AEF9DDD6701AFB46895B86C45CF52EFE) |
| **Discriminant Validity** | Items measuring different constructs correlate weakly | r < 0.70 (distinct), r < 0.85 (similar) | Medium | [Springer APJM](https://link.springer.com/article/10.1007/s10490-023-09871-y) |
| **Content Validity** | Items correspond to construct definition | Expert consensus, I-CVI > 0.78 | Low-Medium | [PMC Best Practices](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/) |
| **Internal Consistency** | Items within scale correlate | Cronbach's α > 0.70, item-total r > 0.30 | Low | [ResearchGate](https://www.researchgate.net/post/What-is-considered-to-be-a-good-item-total-correlation-item-discrimination-value-for-a-Likert-scale) |
| **Factor Analysis** | Items load on intended construct | Factor loading > 0.55 (good), > 0.71 (excellent) | High | [MRC-CBU](https://imaging.mrc-cbu.cam.ac.uk/statswiki/FAQ/thresholds) |

**Implementation Notes:**
- Convergent validity: Compare generated items to validated scales measuring same construct
- Discriminant validity: Ensure generated items don't correlate with unrelated constructs
- Content validity: Expert review against construct definition (can be LLM-assisted)
- Internal consistency: Calculate after scale aggregation, not item-by-item
- Factor analysis: Requires empirical data collection (200+ participants minimum)

## Modern Approaches: LLM-Based Validation

Validation methods leveraging LLM capabilities.

| Method | Mechanism | Accuracy | Advantages | Limitations | Source |
|--------|-----------|----------|------------|-------------|---------|
| **Embedding Similarity** | Cosine similarity in vector space | r=0.59-0.71 (items), r=0.84-0.89 (scales) | Fast, scalable, no prompting needed | Misses nuance (e.g., negation), bias toward positive correlations | [SurveyBot3000](synthetic.pdf) |
| **LLM-as-Judge (Pointwise)** | Rate each item individually on criteria | 80% agreement with humans | Transparent reasoning, explicit scores, multi-dimensional | Cost, potential bias, requires careful prompting | [Label Your Data](https://labelyourdata.com/articles/llm-as-a-judge) |
| **LLM-as-Judge (Pairwise)** | Compare two items, select better | <60% accuracy vs. humans | Direct comparison, useful for A/B testing | Lower accuracy than pointwise, doesn't provide absolute scores | [Evidently AI](https://www.evidentlyai.com/llm-guide/llm-as-a-judge) |
| **Chain-of-Thought Validation** | Explicit reasoning before scoring | 17.9% accuracy improvement | Reduces hallucination, auditable logic | Longer inference time, higher token cost | [Prompt Engineering Guide](https://www.promptingguide.ai/techniques/cot) |
| **Self-Consistency** | Sample multiple reasoning paths, majority vote | 17.9% improvement on GSM8K | Higher reliability, reduces variance | 5-10x cost multiplier, slower inference | [Comet CoT Guide](https://www.comet.com/site/blog/chain-of-thought-prompting/) |
| **Chain of Verification** | Generate answer, verify, revise | Reduces hallucinations | Self-correcting, iterative refinement | Multiple inference passes, complex prompting | [Medium CoVe](https://moazharu.medium.com/chain-of-verification-the-prompting-pattern-that-makes-llm-answers-check-themselves-f9563ea9e960) |

**Confidence Assessment:**
- Embedding similarity: MEDIUM (validated in SurveyBot3000 but struggles with negation, domain-dependent accuracy)
- LLM-as-judge pointwise: MEDIUM-HIGH (80% human agreement, transparent, but requires validation against empirical data)
- LLM-as-judge pairwise: LOW-MEDIUM (<60% accuracy, useful for relative comparisons only)
- Chain-of-thought: MEDIUM-HIGH (established technique, improves reasoning but adds complexity)

## LLM-as-Judge Implementation Guide

### Scoring Scale Design

**Recommended: Categorical Integer Scale (1-10)**

```
Score 1-2: Item does not measure the construct
- No conceptual overlap with construct definition
- Measures a clearly different psychological trait
- Example: "I enjoy social gatherings" for Depression construct

Score 3-4: Minimal construct correspondence
- Tangentially related but not directly measuring construct
- Confounded with other traits
- Example: "I avoid conflict" for Extraversion (measures Agreeableness)

Score 5-6: Moderate construct correspondence
- Partially measures construct but lacks precision
- Acceptable item but not optimal
- Example: "I sometimes feel sad" for Depression (too vague, lacks intensity)

Score 7-8: Strong construct correspondence
- Clearly measures intended construct
- Minor improvements possible (clarity, specificity)
- Example: "I feel persistently sad most days" for Depression

Score 9-10: Excellent construct correspondence
- Precisely measures construct as defined
- Clear, unambiguous, unidimensional
- Example: "I have lost interest in activities I used to enjoy" for Depression
```

**Why this scale:**
- Categorical integers outperform continuous scales for LLM judgment ([Confident AI](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation))
- 1-10 provides granularity while maintaining clarity
- Clear criterion definitions reduce subjectivity
- Aligns with common psychometric conventions

**Alternative: Likert 0-4 Scale** (for faster inference)

```
0 = Does not measure construct
1 = Minimal correspondence
2 = Moderate correspondence
3 = Strong correspondence
4 = Excellent correspondence
```

### Multi-Dimensional Scoring Rubric

**Dimensions for Construct Validation:**

| Dimension | Definition | Why It Matters | Scoring Criteria (1-10) |
|-----------|------------|----------------|------------------------|
| **Correspondence** | Does item measure intended construct? | Core validity question | 1-2: Wrong construct<br>3-4: Tangential<br>5-6: Partial<br>7-8: Strong<br>9-10: Perfect |
| **Distinctiveness** | Is item unidimensional (measures only one construct)? | Prevents confounding | 1-2: Multiple constructs<br>3-4: Substantial confound<br>5-6: Minor confound<br>7-8: Mostly distinct<br>9-10: Purely unidimensional |
| **Clarity** | Is item unambiguous and easily understood? | Ensures reliable responses | 1-2: Very confusing<br>3-4: Ambiguous<br>5-6: Somewhat clear<br>7-8: Clear<br>9-10: Perfectly clear |
| **Specificity** | Does item provide discriminating information? | Avoids ceiling/floor effects | 1-2: Too vague/general<br>3-4: Limited discrimination<br>5-6: Adequate<br>7-8: Good discrimination<br>9-10: Excellent precision |

**Aggregation Strategy:**

```
Overall Score = (Correspondence × 0.50) + (Distinctiveness × 0.25) + (Clarity × 0.15) + (Specificity × 0.10)
```

**Weights rationale:**
- Correspondence (50%): Primary validation concern
- Distinctiveness (25%): Prevents construct confounding
- Clarity (15%): Ensures measurement quality
- Specificity (10%): Optimizes psychometric properties

**Source:** Based on rubric best practices from [Northern Illinois CITL](https://www.niu.edu/citl/resources/guides/instructional-guide/rubrics-for-assessment.shtml) and psychometric validation principles from [NCBI Psychometrics](https://www.ncbi.nlm.nih.gov/books/NBK581902/)

### Prompt Engineering for Validation

**Template 1: Chain-of-Thought with Multi-Dimensional Scoring**

```
You are an expert psychometrician evaluating whether a psychometric item measures its intended construct.

CONSTRUCT DEFINITION:
{construct_name}: {detailed_definition}

ITEM TO EVALUATE:
"{item_text}"

INSTRUCTIONS:
1. Analyze the item step-by-step across four dimensions:
   - Correspondence: Does it measure the construct?
   - Distinctiveness: Is it unidimensional?
   - Clarity: Is it unambiguous?
   - Specificity: Does it discriminate well?

2. For each dimension, provide:
   - Reasoning (2-3 sentences explaining your assessment)
   - Score (1-10 scale where 1-2=poor, 3-4=fair, 5-6=adequate, 7-8=good, 9-10=excellent)

3. Calculate overall score: (Correspondence × 0.50) + (Distinctiveness × 0.25) + (Clarity × 0.15) + (Specificity × 0.10)

4. Provide ACCEPT/REVISE/REJECT recommendation:
   - ACCEPT: Overall score ≥ 7.0
   - REVISE: Overall score 4.0-6.9
   - REJECT: Overall score < 4.0

OUTPUT FORMAT:
{
  "correspondence": {
    "reasoning": "...",
    "score": X
  },
  "distinctiveness": {
    "reasoning": "...",
    "score": X
  },
  "clarity": {
    "reasoning": "...",
    "score": X
  },
  "specificity": {
    "reasoning": "...",
    "score": X
  },
  "overall_score": X.XX,
  "recommendation": "ACCEPT|REVISE|REJECT",
  "revision_suggestions": "..." (if REVISE)
}
```

**Template 2: Self-Consistency Validation** (for higher reliability)

```
Sample N=5 responses using temperature=0.7, then:

1. Extract scores from each response
2. Calculate median score per dimension
3. Flag if standard deviation > 2.0 (indicates uncertainty)
4. Use majority vote for ACCEPT/REVISE/REJECT

Cost: 5x base inference, ~20 seconds @ Claude Opus 4.6
Benefit: Reduces variance, catches edge cases
```

**Source:** Based on [IBM Chain-of-Thought](https://www.ibm.com/think/topics/chain-of-thoughts) and [Lakera Prompt Engineering Guide](https://www.lakera.ai/blog/prompt-engineering-guide)

## Validation Thresholds and Decision Criteria

### Item-Level Acceptance Criteria

| Criterion | Accept | Revise | Reject | Source |
|-----------|--------|--------|--------|--------|
| **LLM-as-Judge Overall Score** | ≥ 7.0 | 4.0-6.9 | < 4.0 | Derived from factor loading standards |
| **Correspondence Score** | ≥ 7 | 4-6 | < 4 | Core validity requirement |
| **Item-Total Correlation** (empirical) | > 0.30 | 0.20-0.30 | < 0.20 | [Frontiers Psychology](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1494261/full) |
| **Factor Loading** (empirical) | > 0.55 | 0.40-0.55 | < 0.40 | [Comrey & Lee 1992](https://imaging.mrc-cbu.cam.ac.uk/statswiki/FAQ/thresholds) |

### Scale-Level Acceptance Criteria

| Criterion | Acceptable | Questionable | Unacceptable | Source |
|-----------|------------|--------------|--------------|--------|
| **Cronbach's Alpha** | ≥ 0.70 | 0.60-0.69 | < 0.60 | Standard psychometric threshold |
| **Average Variance Extracted (AVE)** | ≥ 0.50 | 0.40-0.49 | < 0.40 | [Springer APJM](https://link.springer.com/article/10.1007/s10490-023-09871-y) |
| **Convergent Validity** (with related scale) | r > 0.50 | r = 0.30-0.50 | r < 0.30 | Moderate-high correlation expected |
| **Discriminant Validity** (with unrelated scale) | r < 0.70 | r = 0.70-0.85 | r > 0.85 | [QuantUX Blog](https://quantuxblog.com/convergent-and-discriminant-validity) |
| **Percentage Items Accepted** | ≥ 80% | 60-79% | < 60% | Practical threshold for scale viability |

### Retry Logic

**Recommended strategy (from PROJECT.md):**

```
For each item:
1. Generate item
2. LLM-as-judge validation
3. If score < 7.0:
   - Attempt 1: Regenerate with feedback
   - Attempt 2: Regenerate with stricter constraints
   - Attempt 3: Regenerate with alternative phrasing
4. After 3 attempts, accept best-scoring version if score ≥ 4.0
5. Flag for human review if all attempts score < 4.0

Max 3 retry attempts balances quality vs. cost/time
```

**Confidence:** HIGH (aligns with standard psychometric thresholds and practical constraints)

## Comparison: Validation Method Trade-offs

| Method | Speed | Cost | Transparency | Accuracy | When to Use |
|--------|-------|------|--------------|----------|-------------|
| **Embedding Similarity** | Very Fast | Very Low | Low (black box) | Medium (r=0.59-0.71) | Initial filtering, large-scale screening |
| **LLM-as-Judge (No CoT)** | Fast | Medium | Medium | Medium (80% agreement) | Quick validation, limited budget |
| **LLM-as-Judge (CoT)** | Medium | Medium-High | High | Medium-High | Production validation, audit trail needed |
| **LLM + Self-Consistency** | Slow | High | High | High | Critical items, high-stakes assessment |
| **Empirical Validation** | Very Slow | Very High | Highest | Highest (gold standard) | Final validation, publication |

**Recommendations by Use Case:**

1. **Development Phase:** Embedding similarity (fast iteration)
2. **Pre-Review Phase:** LLM-as-judge with CoT (transparent scoring)
3. **Production Phase:** Empirical validation with 200+ participants
4. **Continuous Monitoring:** LLM-as-judge + periodic empirical checks

**Source:** Synthesized from [Evidently AI LLM Evaluation](https://www.evidentlyai.com/llm-guide/llm-evaluation-metrics) and SurveyBot3000 findings

## Validation Against Construct Definitions

### Strategy 1: Definition-Based Scoring

**Approach:**
```
1. Provide LLM with:
   - Formal construct definition (from literature)
   - Theoretical framework (e.g., Big Five for personality)
   - Example items from validated scales
   - Anti-examples (items measuring different constructs)

2. Ask LLM to:
   - Identify conceptual overlap between item and definition
   - Flag conceptual divergence
   - Compare to example items (convergent evidence)
   - Compare to anti-examples (discriminant evidence)

3. Score based on:
   - Semantic alignment with definition (0-10)
   - Similarity to validated examples (0-10)
   - Dissimilarity to anti-examples (0-10)
```

**Prompt Template:**
```
CONSTRUCT: {name}
DEFINITION: {formal_definition}
THEORETICAL FRAMEWORK: {framework}

VALIDATED EXAMPLES:
1. {example_item_1}
2. {example_item_2}
3. {example_item_3}

ANTI-EXAMPLES (different constructs):
1. {anti_example_1} (measures {other_construct})
2. {anti_example_2} (measures {other_construct})

ITEM TO EVALUATE: "{new_item}"

TASK:
1. Semantic alignment: How well does this item capture the construct definition? (0-10)
2. Convergent evidence: How similar is this item to the validated examples? (0-10)
3. Discriminant evidence: How different is this item from the anti-examples? (0-10)

Provide reasoning for each score, then calculate: (Alignment × 0.50) + (Convergent × 0.30) + (Discriminant × 0.20)
```

**Confidence:** MEDIUM-HIGH (leverages existing validated scales, but depends on LLM's semantic understanding)

### Strategy 2: Facet-Based Validation

For multi-faceted constructs (e.g., Depression has cognitive, affective, somatic facets):

```
1. Break construct into facets (from theory)
2. Score item on each facet (0-10): "Does this item measure [facet]?"
3. Identify primary facet (highest score)
4. Validate item maps to intended facet
5. Flag if item spans multiple facets (distinctiveness concern)

Accept if:
- Primary facet score ≥ 7
- Intended facet matches primary facet
- Secondary facet scores < 5 (unidimensional)
```

**Example: Depression (Beck Depression Inventory facets)**
- Cognitive: Pessimism, worthlessness, self-criticism
- Affective: Sadness, loss of pleasure, crying
- Somatic: Fatigue, sleep disturbance, appetite changes

Item: "I feel tired all the time"
- Cognitive: 2/10 (not about thoughts)
- Affective: 3/10 (minimal emotional content)
- Somatic: 9/10 (directly measures fatigue)
- Primary: Somatic ✓
- Distinctiveness: Good (one facet dominant)
- Decision: ACCEPT for somatic depression

**Source:** Based on construct validity principles from [Test Partnership](https://www.testpartnership.com/academy/construct-validity.html)

## Practical Implementation Workflow

### Phase 1: Development (Pre-Validation)

```
1. Generate items (Item Writer agent)
2. Embedding similarity filter:
   - Compare to validated scale items (convergent > 0.50)
   - Compare to anti-construct items (discriminant < 0.30)
   - Filter out items failing thresholds
3. Pass filtered items to Phase 2
```

**Rationale:** Fast initial filter, removes obviously incorrect items
**Cost:** ~$0.001 per item (embedding generation)
**Confidence:** MEDIUM (catches gross errors, misses nuanced issues)

### Phase 2: LLM-as-Judge Validation

```
1. For each item:
   a. LLM-as-judge with CoT (multi-dimensional scoring)
   b. If overall score < 7.0: regenerate with feedback
   c. Max 3 regeneration attempts
   d. Accept if score ≥ 7.0, flag for review if < 4.0

2. Track validation metadata:
   - All scores (correspondence, distinctiveness, clarity, specificity)
   - Reasoning (for audit trail)
   - Regeneration attempts
   - Final decision (ACCEPT/REVISE/REJECT)

3. Export validation scores for results UI
```

**Rationale:** Transparent, explainable validation before human review
**Cost:** ~$0.01-0.05 per item (Claude Opus with CoT)
**Confidence:** MEDIUM-HIGH (80% agreement with humans, explicit reasoning)

### Phase 3: Human Review (Optional)

```
1. Review items flagged as REVISE (score 4.0-6.9)
2. Review items with high variance across dimensions
3. Spot-check 10% of ACCEPT items for quality
4. Final approval before empirical testing
```

**Rationale:** Human oversight for edge cases, quality assurance
**Cost:** Researcher time (~2-5 min per item)
**Confidence:** HIGHEST (human expert judgment)

### Phase 4: Empirical Validation (Production)

```
1. Administer items to 200+ participants
2. Calculate item-total correlations (threshold > 0.30)
3. Conduct factor analysis (loadings > 0.55)
4. Assess internal consistency (alpha > 0.70)
5. Test convergent validity (r > 0.50 with related scales)
6. Test discriminant validity (r < 0.70 with unrelated scales)
7. Remove/revise items failing thresholds
8. Iterate until all criteria met
```

**Rationale:** Gold standard validation, required for publication
**Cost:** Participant fees + researcher time (~$500-2000)
**Confidence:** HIGHEST (empirical evidence)

**Source:** Workflow synthesized from [Oasis LMS Psychometric Test Development](https://oasis-lms.com/post/psychometric-test-development-a-complete-guide-for-certification-credentialing-programs-in-2026) and project requirements

## Avoiding Common Pitfalls

### Pitfall 1: Over-Reliance on LLM Judgment

**What goes wrong:** LLMs can exhibit biases (e.g., preference for longer items, recency bias in training data)

**Prevention:**
- Always validate LLM judgments against empirical data (correlation with item-total r, factor loadings)
- Use multiple LLMs (Claude, GPT-4) and average scores (ensemble validation)
- Include human expert review for final approval

**Detection:** Compare LLM scores to empirical psychometric indices; flag if correlation < 0.50

**Confidence:** HIGH (documented in LLM-as-judge literature: [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/))

### Pitfall 2: Ignoring Embedding Limitations

**What goes wrong:** Embeddings miss semantic nuance (e.g., "Restart device before calling support" vs. "Call support before restarting device" have similar embeddings but opposite meaning)

**Prevention:**
- Use embeddings for initial filtering only, not final validation
- Follow up with LLM-as-judge for semantic analysis
- Test embedding approach on known item pairs first

**Detection:** Manually review high-similarity items with different intended meanings

**Confidence:** MEDIUM-HIGH (documented in [Emergent Mind SemScore](https://www.emergentmind.com/papers/2401.17072))

### Pitfall 3: Circular Validation

**What goes wrong:** Using same LLM to generate and validate items creates circularity (model validates its own output)

**Prevention:**
- Use different models for generation (GPT-4o) and validation (Claude Opus)
- Include human-written items in validation set as anchors
- Validate against empirical data (ultimate ground truth)

**Detection:** Compare validation scores for LLM-generated vs. human-written items; flag if significantly different

**Confidence:** MEDIUM (common sense principle, not extensively documented)

### Pitfall 4: Single-Dimensional Scoring

**What goes wrong:** Overall score conflates distinct issues (e.g., item may have perfect correspondence but poor clarity)

**Prevention:**
- Use multi-dimensional rubric (correspondence, distinctiveness, clarity, specificity)
- Report all dimension scores, not just overall
- Flag items with discrepant dimension scores (e.g., high correspondence but low clarity)

**Detection:** Standard deviation across dimensions > 3.0 indicates inconsistency

**Confidence:** HIGH (established rubric design principle: [Rubric Best Practices](https://awardforce.com/blog/articles/rubric-best-practices-for-creating-a-fair-and-balanced-assessment/))

### Pitfall 5: Threshold Sensitivity

**What goes wrong:** Arbitrary thresholds (e.g., "score must be exactly 7.0") create false precision

**Prevention:**
- Use threshold ranges (ACCEPT ≥7.0, REVISE 4.0-6.9, REJECT <4.0)
- Report confidence intervals for scores (if using self-consistency)
- Allow human override for borderline cases

**Detection:** Items clustered at threshold boundaries indicate arbitrary cutoff

**Confidence:** MEDIUM (practical consideration, not extensively documented)

## Open Questions and Research Gaps

**Gap 1: Optimal LLM-as-Judge Prompts for Psychometrics**
- Current templates adapted from general LLM-as-judge literature
- Need empirical testing: Which prompt variants maximize correlation with empirical validation?
- Suggested research: A/B test 5-10 prompt variants on validated item sets

**Gap 2: Cross-Model Validation Reliability**
- Unknown: Do Claude, GPT-4, Gemini produce consistent validation scores?
- Need: Inter-rater reliability study (treat each model as a rater)
- Expected: Moderate agreement (r=0.60-0.80) based on general LLM-as-judge findings

**Gap 3: Domain-Specific Validation Accuracy**
- SurveyBot3000 shows accuracy varies by domain (attitudes: r=0.34, occupational: r=0.75)
- Unknown: Which psychometric domains are most/least amenable to LLM validation?
- Suggested research: Test LLM-as-judge on personality, clinical, cognitive ability, attitudes separately

**Gap 4: Validation for Reverse-Scored Items**
- Embeddings struggle with negation (documented in SurveyBot3000)
- Unknown: Do LLM-as-judge prompts handle reverse-scored items better?
- Suggested research: Test on matched pairs (forward/reverse) with known correlations

**Confidence:** All gaps are LOW confidence areas requiring additional research

## Sources

### Classical Psychometric Validation

- [NCBI: Principles for Evaluating Psychometric Tests](https://www.ncbi.nlm.nih.gov/books/NBK581902/)
- [Cambridge BJPsych: Development, Validation and Translation of Psychological Tests](https://www.cambridge.org/core/journals/bjpsych-advances/article/development-validation-and-translation-of-psychological-tests/AEF9DDD6701AFB46895B86C45CF52EFE)
- [PMC: Best Practices for Developing and Validating Scales](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/)
- [Test Partnership: Construct Validity](https://www.testpartnership.com/academy/construct-validity.html)
- [Oasis LMS: Psychometric Test Development Guide 2026](https://oasis-lms.com/post/psychometric-test-development-a-complete-guide-for-certification-credentialing-programs-in-2026)

### Validation Thresholds

- [Springer APJM: Convergent and Discriminant Validity with SEM](https://link.springer.com/article/10.1007/s10490-023-09871-y)
- [QuantUX Blog: Convergent and Discriminant Validity](https://quantuxblog.com/convergent-and-discriminant-validity)
- [ReCentering Psych Stats: Psychometric Validity](https://lhbikos.github.io/ReC_Psychometrics/rxy.html)
- [MRC-CBU: Factor Loading Cutoffs](https://imaging.mrc-cbu.cam.ac.uk/statswiki/FAQ/thresholds)
- [Frontiers Psychology: Psychometric Validation Guidelines](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1494261/full)

### LLM-as-Judge Methods

- [Label Your Data: LLM as a Judge Guide 2026](https://labelyourdata.com/articles/llm-as-a-judge)
- [Evidently AI: LLM-as-a-Judge Complete Guide](https://www.evidentlyai.com/llm-guide/llm-as-a-judge)
- [Langfuse: LLM-as-a-Judge Evaluation](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)
- [Eugene Yan: Evaluating LLM-Evaluators](https://eugeneyan.com/writing/llm-evaluators/)
- [Confident AI: LLM Evaluation Metrics](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation)

### Prompt Engineering

- [Prompt Engineering Guide: Chain-of-Thought](https://www.promptingguide.ai/techniques/cot)
- [Lakera: Ultimate Guide to Prompt Engineering 2026](https://www.lakera.ai/blog/prompt-engineering-guide)
- [Comet: Chain-of-Thought Prompting Guide](https://www.comet.com/site/blog/chain-of-thought-prompting/)
- [IBM: Chain of Thought](https://www.ibm.com/think/topics/chain-of-thoughts)
- [Medium: Chain of Verification](https://moazharu.medium.com/chain-of-verification-the-prompting-pattern-that-makes-llm-answers-check-themselves-f9563ea9e960)

### Embedding vs. LLM Comparison

- [Evidently AI: LLM Evaluation Metrics](https://www.evidentlyai.com/llm-guide/llm-evaluation-metrics)
- [Emergent Mind: SemScore](https://www.emergentmind.com/papers/2401.17072)
- [MDPI: Comprehensive Evaluation of Embedding Models and LLMs](https://www.mdpi.com/2504-2289/9/5/141)
- SurveyBot3000 paper (synthetic.pdf) - embedding-based validation achieving r=0.59-0.84

### Rubric Design

- [Awardforce: Rubric Best Practices](https://awardforce.com/blog/articles/rubric-best-practices-for-creating-a-fair-and-balanced-assessment/)
- [Northern Illinois CITL: Rubrics for Assessment](https://www.niu.edu/citl/resources/guides/instructional-guide/rubrics-for-assessment.shtml)
- [DePaul: Types of Rubrics](https://resources.depaul.edu/teaching-commons/teaching-guides/feedback-grading/rubrics/Pages/types-of-rubrics.aspx)
