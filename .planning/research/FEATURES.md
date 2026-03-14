# Feature Landscape

**Domain:** Psychometric construct validation depth (synthetic correlations, instrument comparison, nomological network analysis)
**Researched:** 2026-03-14

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Inter-item correlation matrix display | Standard psychometric output for reliability assessment; users expect to see item-level relationships | Medium | Correlation matrices are core output in every psychometric software (ShinyItemAnalysis, jMetrik, Xcalibre) — absence signals incomplete analysis |
| Pearson correlation for generated items | Default correlation type for continuous/interval data; established baseline | Low | Computation straightforward with numerical data; MAPIG currently has no response data, needs synthetic estimation |
| Internal consistency metrics (Cronbach's alpha) | Fundamental reliability measure; minimum standard is α ≥ 0.70 for research | Low | Industry standard since Nunnally (1978); expected alongside any correlation matrix |
| Correlation significance indicators | Users need to distinguish meaningful vs chance correlations | Low | Standard statistical output (p-values, confidence intervals) |
| Convergent validity evidence | Demonstrates items measure the same construct; required for construct validation | Medium | Requires comparison with established instruments measuring same construct |
| Discriminant validity evidence | Demonstrates items don't measure unrelated constructs; required for construct validation | Medium | Requires comparison with instruments measuring different constructs |
| Validated instrument search capability | Replace hardcoded nearest neighbors; users expect dynamic literature-grounded comparisons | High | Current system has hardcoded org psych constructs (job satisfaction, engagement, commitment) — users expect broader, evidence-based comparisons |
| Correlation visualization (heatmap) | Visual display is standard in psychometric tools; raw matrices hard to interpret | Medium | All major tools (R psych, ShinyItemAnalysis, SPSS) include visual correlation displays |
| Export correlation matrices | Users need correlations for external analysis (factor analysis, SEM) | Low | Standard CSV/JSON export with labeled rows/columns |
| Model fit indices for factor structure | If claiming dimensionality, need RMSEA, CFI, TLI evidence | High | Standard validation requirement: RMSEA ≤ 0.06, CFI ≥ 0.95, TLI ≥ 0.95 |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| LLM-estimated synthetic correlations (SurveyBot3000 approach) | Generate correlation matrices WITHOUT response data; instant psychometric preview | High | Research-backed: r=0.75 in-sample, r=0.61 out-of-sample for 449 scales; semantic embeddings predict empirical correlations; **competitive advantage** — no other item generators offer this |
| Semantic similarity to empirical correlation mapping | Show WHY correlations are predicted; transparent AI reasoning | Medium | Nature Human Behaviour 2024: semantic embeddings predict psychometric properties; builds trust in synthetic estimates |
| Polychoric/tetrachoric correlation estimation | Correct correlation type for ordinal Likert data; more accurate than Pearson | Medium | Research shows polychoric yields less biased factor loadings; demonstrates psychometric sophistication |
| Dynamic instrument repository search | Auto-discover validated comparison instruments from PsycTESTS, MMH, ETS databases | High | Goes beyond hardcoded comparisons; **differentiator** — grounded in actual published instruments |
| Cross-construct comparison against published items | Compare generated items directly to gold-standard published instrument items | High | Unique capability: shows semantic alignment with established measures; builds credibility |
| Nomological network visualization | Graph showing construct relationships (convergent/discriminant patterns) | High | Modern SEM-style display; helps users understand construct positioning; **visual differentiator** |
| Position-bias-mitigated LLM comparisons | Dual-direction evaluation (A vs B, B vs A) with averaged scores | Medium | Already implemented in evaluation framework; extends to instrument comparison |
| Confidence intervals for synthetic correlations | Quantify uncertainty in LLM-estimated correlations | Medium | Critical for transparency: users know estimates ≠ empirical data; builds trust |
| Multi-model synthetic validation | Compare synthetic correlations from Claude + GPT 5.2 (thinking mode) | High | Model agreement = higher confidence; disagreement flags need for empirical validation |
| Factor structure prediction without data | LLM predicts factorial structure from item text alone | High | Research: r=0.76-0.85 correlation with human factor structure; pre-testing capability |
| Automated convergent/discriminant flagging | System identifies potential construct validity issues before data collection | Medium | Proactive quality control: "Your items correlate r=0.85 with [related construct] — may lack discriminant validity" |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Generating synthetic response data | LLMs as respondents have narrow variability, semantic drift issues, "AI-slop" contamination risk | Use semantic similarity to predict correlations; never claim to replace human responses |
| Causal claims from correlations | Correlation ≠ causation; fundamental misinterpretation risk | Display correlations with explicit disclaimers; focus on construct relationships, not causal inference |
| Single-source instrument comparisons | Overfitting to one validation instrument; non-generalizable | Require multiple comparison instruments; show convergent/discriminant patterns across instruments |
| Treating synthetic correlations as empirical | Synthetic estimates are predictions, not observations; claiming equivalence damages credibility | Always label as "LLM-estimated" or "synthetic"; provide confidence intervals; recommend empirical validation |
| Auto-accepting items based on synthetic metrics | Automation bias; semantic drift can produce plausible-but-invalid items | Synthetic correlations inform, don't replace validation gate; human review remains required |
| IRT parameter estimation without data | IRT requires response data; difficulty/discrimination estimates from text alone are unreliable | Stick to CTT-style correlations; defer IRT to empirical validation phase |
| Recursive AI training on generated items | "AI-slop" degrades training data; pollutes item pools with derivative content | Generated items are outputs, never training inputs; avoid feedback loops |
| Claiming construct validity from synthetic data alone | Construct validity requires multiple studies, empirical evidence, external validation | Position synthetic correlations as "early-stage psychometric preview"; require empirical validation for validity claims |
| Generating reverse-scored items for reliability | Research shows reverse-scored items reduce reliability, introduce method effects | Already implemented as anti-feature in Item Writer; maintain positive keying only |
| Providing correlation "cut-offs" as absolute rules | Context-dependent; e.g., convergent validity threshold varies by construct breadth | Provide guidance ranges, not hard thresholds; show comparison to published instruments |

## Feature Dependencies

```
Validated Instrument Search
  ├─> Cross-Construct Comparison (requires instruments to compare against)
  └─> Convergent/Discriminant Validity (requires related/unrelated instruments)

Synthetic Correlation Matrix
  ├─> Internal Consistency Metrics (Cronbach's alpha computed from correlations)
  ├─> Correlation Visualization (heatmap displays matrix)
  ├─> Factor Structure Prediction (correlations feed factor analysis)
  └─> Nomological Network Visualization (correlations define edges)

LLM-Estimated Correlations
  ├─> Confidence Intervals (quantify uncertainty)
  ├─> Multi-Model Validation (compare Claude vs GPT 5.2 estimates)
  └─> Semantic Similarity Mapping (explains correlation predictions)

Cross-Construct Comparison
  ├─> Semantic Similarity Scoring (compare item text to published items)
  └─> Convergent/Discriminant Flagging (automated validity warnings)

Existing MAPIG Agents
  ├─> Web Surfer: Already searches for theoretical definitions, frameworks, validated instrument NAMES
  │   └─> Enhancement needed: Search for and retrieve actual published instrument ITEMS
  ├─> Content Reviewer: Already has hardcoded org psych nearest neighbors
  │   └─> Enhancement needed: Replace hardcoded list with dynamic search results
  ├─> Validation Agent: Already does 4-dimensional LLM-as-judge scoring
  │   └─> Extension: Add synthetic correlation estimation module
  └─> Meta Editor: Already enforces facet balancing
      └─> Extension: Flag potential convergent/discriminant validity issues
```

## MVP Recommendation

Prioritize:
1. **LLM-estimated synthetic correlation matrix** (differentiator) — Core innovation; SurveyBot3000 research validates approach
2. **Correlation visualization heatmap** (table stakes) — Expected output; makes correlations interpretable
3. **Internal consistency metrics** (table stakes) — Cronbach's alpha computed from correlation matrix; minimum standard
4. **Validated instrument search** (table stakes) — Replace hardcoded nearest neighbors with literature-grounded search
5. **Convergent/discriminant validity evidence** (table stakes) — Core construct validation requirement
6. **Cross-construct comparison** (differentiator) — Unique capability; compare generated items to published items
7. **Confidence intervals for synthetic estimates** (differentiator) — Builds trust; transparent about uncertainty

Defer:
- **Polychoric/tetrachoric correlations**: Medium complexity, marginal benefit over Pearson for synthetic estimates (no actual ordinal response data)
- **Nomological network visualization**: High complexity graph display; correlation matrix provides same information in simpler format
- **Factor structure prediction**: High complexity; CFA requires structural equation modeling; defer to v3
- **Multi-model synthetic validation**: High complexity; requires managing multiple LLM providers; single-model (Claude) sufficient for MVP
- **Model fit indices (RMSEA, CFI, TLI)**: Requires factor analysis implementation; defer to v3 when adding CFA

## Implementation Notes

### Synthetic Correlation Estimation

**SurveyBot3000 approach** (validated in research):
1. Use sentence transformer embeddings to capture item semantic similarity
2. Map semantic similarity to predicted empirical correlations
3. Research validation: r=0.75 in-sample, r=0.61 out-of-sample for 449 scales

**Alternative LLM approach** (more aligned with MAPIG's existing architecture):
1. Use Claude/GPT to directly estimate item-pair correlations based on semantic content
2. Provide construct definition + item pairs + scale anchors → estimate correlation
3. Aggregate pairwise estimates into correlation matrix
4. Validate matrix properties (positive semi-definite, symmetric, diagonal = 1)

**MAPIG-specific implementation**:
- Add `SyntheticCorrelationAgent` after Meta Editor finalizes item set
- Input: Final item set + construct definition + user constraints
- Output: Correlation matrix + confidence intervals + Cronbach's alpha
- Integration: Display in Results UI as "Psychometric Preview" card

### Validated Instrument Search

**Enhancement to Web Surfer agent**:
- Current: Searches Perplexity for theoretical definitions, frameworks, validated instrument NAMES
- Enhanced: Search for actual published instrument ITEMS from:
  - PsycTESTS (APA repository with downloadable test instruments)
  - Mental Measurements Yearbook (2,000+ testing instruments)
  - ETS Test Collection (20,000 tests, early 1900s to present)
  - Open-access sources (published scales in journal articles)

**Content Reviewer enhancement**:
- Current: Hardcoded org psych nearest neighbors (job satisfaction, engagement, commitment)
- Enhanced: Dynamic search for related constructs based on user's construct definition
- Use search results to populate convergent/discriminant comparison sets

### Cross-Construct Comparison

**Semantic similarity scoring**:
1. Retrieve published instrument items for related constructs (convergent) and unrelated constructs (discriminant)
2. Compute semantic similarity between generated items and published items (sentence transformers or LLM-based)
3. Expected pattern:
   - High similarity to convergent instruments (related constructs)
   - Low similarity to discriminant instruments (unrelated constructs)
4. Flag validity issues: "Generated items show r=0.85 similarity to [unrelated construct] — potential discriminant validity concern"

**Display in Results UI**:
- Comparison table: Generated item | Most similar published item | Similarity score | Source instrument
- Convergent/discriminant summary: "Items show expected pattern: high convergence with [construct A] (r=0.78), low convergence with [construct B] (r=0.23)"

## Sources

### Synthetic Correlations & LLM Psychometrics
- [Leveraging LLM-Respondents for Item Evaluation: a Psychometric Analysis](https://arxiv.org/abs/2407.10899) — HIGH confidence: LLM respondents produce item parameters with r>0.8 correlation to human data (GPT-3.5)
- [A psychometric framework for evaluating and shaping personality traits in large language models](https://www.nature.com/articles/s42256-025-01115-6) — HIGH confidence: Inter-item correlations in LLMs range 0.048-0.35 (BFI), 0.22-0.31 (scenarios)
- [Rethinking psychometrics through LLMs: how item semantics shape measurement](https://www.nature.com/articles/s41598-025-21289-8) — HIGH confidence: Semantic similarity matrices correlate highly with empirical data; LLMs predict item correlations without observations
- [Language Models Accurately Infer Correlations Between Psychological Items](https://journals.sagepub.com/doi/10.1177/25152459251377093) — HIGH confidence: SurveyBot3000 validates synthetic predictions with r=0.75 in-sample, r=0.61 out-of-sample for 449 scales
- [Semantic embeddings reveal and address taxonomic incommensurability](https://www.nature.com/articles/s41562-024-02089-y) — HIGH confidence: Semantic embeddings predict psychometric properties; r=0.75 observed vs predicted internal consistency

### Validated Instrument Comparison & Repositories
- [PsycTESTS Database](https://guides.library.txstate.edu/c.php?g=184075&p=1215156) — HIGH confidence: APA repository with downloadable test instruments
- [Mental Measurements Yearbook](https://guides.nyu.edu/tests/finding-info) — HIGH confidence: Comprehensive guide to 2,000+ contemporary testing instruments (Buros Institute)
- [Implementation Outcomes Repository](https://implementationoutcomerepository.org/about-the-repository) — HIGH confidence: Instruments assessed with COSMIN checklist for methodological quality
- [Best Practices for Scale Development and Validation](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/) — HIGH confidence: CFA, RMSEA ≤0.06, CFI ≥0.95 standards

### Convergent/Discriminant Validity
- [Reporting reliability, convergent and discriminant validity with SEM](https://link.springer.com/article/10.1007/s10490-023-09871-y) — HIGH confidence: AVE >0.50, HTMT <0.85 thresholds; multiple criteria required
- [Convergent & Discriminant Validity](https://conjointly.com/kb/convergent-and-discriminant-validity/) — MEDIUM confidence: Both required for construct validity; neither alone sufficient
- [AI Dependency Scale 2026](https://www.tandfonline.com/doi/full/10.1080/10447318.2026.2629522) — HIGH confidence: AVE >0.50, HTMT <0.85 applied in practice

### Nomological Networks
- [Nomological Network: Construct Validity Guide](https://www.cogn-iq.org/learn/theory/nomological-network/) — MEDIUM confidence: Theoretically specified system linking construct, indicators, related constructs
- [The Nomological Network - Research Methods](https://conjointly.com/kb/nomological-network/) — MEDIUM confidence: Expresses expected correlations if test reflects intended construct
- [Repositioning Construct Validity Theory](https://pmc.ncbi.nlm.nih.gov/articles/PMC11881521/) — MEDIUM confidence: Modern nomological nets = structural equation models

### Correlation Methods
- [Semantic similarity prediction](https://arxiv.org/html/2309.12697v2) — HIGH confidence: Semantic similarity predicts item correlations; r=0.76-0.85 with factorial structure
- [Shortening Psychological Scales: Semantic Similarity Matters](https://pmc.ncbi.nlm.nih.gov/articles/PMC11851598/) — HIGH confidence: Semantic similarity enables scale development without response data
- [Polychoric correlation](https://en.wikipedia.org/wiki/Polychoric_correlation) — MEDIUM confidence: Estimates correlation between latent continuous variables from ordinal data
- [Polychoric Correlation With Ordinal Data](https://pmc.ncbi.nlm.nih.gov/articles/PMC9617753/) — HIGH confidence: Less biased factor loadings than Pearson for Likert data

### Psychometric Software Features
- [ShinyItemAnalysis](https://shinyitemanalysis.org/) — MEDIUM confidence: Standard features include correlation matrices, reliability, validity analysis, automatic HTML/PDF reports
- [Xcalibre - IRT analysis](https://assess.com/xcalibre/) — MEDIUM confidence: Auto-generates reports with correlation matrices, IRFs, model fit graphics
- [IPV: Item Pool Visualization](https://link.springer.com/article/10.3758/s13428-022-02052-7) — MEDIUM confidence: Bivariate correlation displays at multiple specificity levels

### Pitfalls & Limitations
- [Mini-review: impacts of AI on measurement scale development](https://www.frontiersin.org/journals/organizational-psychology/articles/10.3389/forgp.2026.1787155/full) — HIGH confidence: Semantic drift, AI-slop degradation, generalizability concerns with AI-generated items
- [Correlation vs Causation](https://www.scribbr.com/frequently-asked-questions/why-doesnt-correlation-imply-causation/) — MEDIUM confidence: Third variable problem, directionality problem; 76% of data scientists encounter confusion
- [Observed scale score comparisons misestimate true group differences](https://pmc.ncbi.nlm.nih.gov/articles/PMC11923020/) — HIGH confidence: Cohen's d misestimated in 33/70 cases by average 25% due to measurement error
- [Best Practices for Scale Development](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/) — HIGH confidence: Minimum α=0.70 standard; homogeneous samples during development handicap generalization
