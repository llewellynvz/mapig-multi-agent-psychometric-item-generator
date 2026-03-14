# Psychometric Item Writing Standards

**Domain:** Likert-type psychometric item construction for psychological assessments
**Researched:** 2026-03-08
**Confidence:** HIGH

## Executive Summary

This document synthesizes established psychometric principles and current best practices (2024-2026) for writing high-quality assessment items. It is designed to optimize MAPIG's 7-agent workflow by providing explicit, actionable guidance grounded in test development literature and addressing LLM-specific challenges in automated item generation.

Psychometric item writing is both art and science. While comprehensive guidelines exist in the literature, recent empirical research reveals nuanced findings: some traditional rules (avoiding vague quantifiers, maintaining stem clarity) remain critical, while others (strict homogeneity, context uniformity) show more complex effects on measurement quality. For LLM-based item generation, the key challenges are ensuring construct validity, avoiding semantic redundancy, managing acquiescence bias, and preventing construct contamination—areas where explicit prompting and multi-agent review offer significant advantages.

This guide prioritizes current standards from AERA/APA/NCME (2014 Standards for Educational and Psychological Testing), empirical findings from 2024-2025 psychometric literature, and emerging research on LLM-generated assessment quality.

---

## Core Principles for Item Construction

### Principle 1: Construct Correspondence (What Does This Item Measure?)

**Standard:** Each item must demonstrably measure the target construct and only the target construct.

**Why It Matters:**
Construct validity is the foundational validity evidence for psychological assessment. An item that measures something other than the intended construct introduces systematic error and compromises interpretation of scale scores.

**Operationalization:**
- **Direct correspondence:** Item content reflects a specific behavioral indicator, cognitive process, or affective state that theoretically represents the construct.
- **Distinctiveness:** Item does NOT simultaneously tap overlapping constructs (e.g., "I enjoy meeting new people and feel energized at parties" conflates sociability with affect regulation).
- **Facet mapping:** For multidimensional constructs, each item maps to ONE facet with clear theoretical rationale.

**Evaluation Questions:**
1. If I presented this item to 5 independent construct experts, would they agree on which construct it measures?
2. Does this item capture a construct-relevant manifestation or merely a correlated behavior?
3. Could a respondent score high on this item for reasons unrelated to the target construct?

**Common Violations:**
- Items that measure consequences rather than the construct itself (e.g., "People consider me friendly" measures *reputation*, not extraversion)
- Items contaminated by social desirability (e.g., "I never lie" conflates honesty with impression management)
- Items requiring context-specific knowledge that varies across populations (e.g., "I thrive in open-plan offices" for workplace belonging)

**Reference:** AERA/APA/NCME Standards (2014), Chapter 1 on Validity; Constructing Validity: New Developments in Creating Objective Measuring Instruments (PMC6754793)

---

### Principle 2: Unidimensionality (One Idea Per Item)

**Standard:** Each item assesses a single attribute. Items asking about multiple attributes simultaneously (double-barreled questions) cannot be interpreted.

**Why It Matters:**
When an item contains multiple ideas, a respondent's answer is ambiguous. Agreement could reflect endorsement of component A, component B, both, or neither. This violates the assumption that item responses reflect a single latent dimension.

**Examples:**

**VIOLATION:**
- "I enjoy collecting and analyzing data" (two behaviors: collecting AND analyzing)
- "I feel calm and relaxed in social situations" (affective state AND context)
- "My team values my contributions and seeks my input" (perceived value AND consultation frequency)

**COMPLIANT:**
- "I enjoy analyzing data"
- "I feel calm in social situations"
- "My team seeks my input on important decisions"

**Detection Rules:**
- Presence of conjunctions (and, or, but) within the predicate
- Multiple verbs describing distinct actions
- Compound predicates with separable components

**LLM-Specific Challenge:**
LLMs often generate semantically rich, elaborative stems that inadvertently combine multiple ideas. Item Writer agents must be explicitly instructed to generate single-predicate statements and Linguistic Reviewers must flag compound structures.

**Reference:** Qualtrics (2024) Double-Barreled Question Guide; Kantar (2024) Double-Barrelled Questions; Wikipedia: Double-barreled question

---

### Principle 3: Clarity and Precision (No Ambiguity)

**Standard:** Items must be interpretable in only one way. Ambiguous referents, vague quantifiers, and imprecise language introduce construct-irrelevant variance.

#### 3a. Vague Quantifiers

**Traditional Guidance:** Avoid terms like "often," "sometimes," "frequently," "rarely" without operational definitions, as respondents interpret them idiosyncratically.

**Nuanced Evidence (2024):** Empirical studies (Robie & Risavy, 2020) found NO systematic degradation of psychometric properties from vague quantifiers in personality assessment. However, vague quantifiers remain problematic in contexts requiring objective thresholds (e.g., clinical assessment, performance evaluation).

**Recommendation for MAPIG:**
- **AVOID** vague quantifiers when measuring behavioral frequency or intensity where precision matters.
- **ACCEPTABLE** when measuring subjective states where absolute quantification is inappropriate (e.g., "I often feel overwhelmed" is acceptable for stress assessment).
- **ALWAYS DEFINE** quantifiers when used (e.g., "During the past month, how often have you felt... [response scale: Never, Rarely (1-2 times), Sometimes (3-5 times), Often (6-10 times), Very Often (>10 times)]").

#### 3b. Ambiguous Referents

**Standard:** Pronouns and referents must have clear antecedents. Avoid "it," "they," "this," "things" without explicit specification.

**Examples:**

**VIOLATION:**
- "They understand me" (Who is "they"?)
- "It makes me anxious" (What is "it"?)
- "I handle things well under pressure" (What "things"?)

**COMPLIANT:**
- "My colleagues understand me"
- "Public speaking makes me anxious"
- "I handle complex tasks well under pressure"

**LLM-Specific Challenge:**
LLMs generate contextually plausible pronouns that may lack explicit referents. Prompt engineering should specify: "Use concrete nouns, not pronouns. Every referent must be explicitly stated."

#### 3c. Abstract vs. Concrete Language

**Standard:** Prefer concrete, behavioral language over abstract constructs unless measuring metacognitive or philosophical constructs.

**Examples:**

**ABSTRACT (weaker):**
- "I am introspective"
- "I value authenticity"

**CONCRETE (stronger):**
- "I regularly reflect on my motivations"
- "I express my genuine opinions, even when they differ from others"

**Exception:** When the construct itself is abstract (e.g., existential meaning, spiritual transcendence), abstract language may be appropriate. Match language abstraction to construct abstraction.

**Reference:** European Journal of Psychological Assessment (2020) - "Not Very Powerful: The Influence of Negations and Vague Quantifiers on the Psychometric Properties of Questionnaires"; Frontiers in Psychology (2025) - Reverse-keyed items and linguistic clarity

---

### Principle 4: Reading Level Targeting

**Standard:** Items should be written at or below the reading level of the lowest-literacy members of the target population.

**Operationalization:**

| Target Population | Recommended Flesch-Kincaid Grade Level | Rationale |
|-------------------|---------------------------------------|-----------|
| General adult population (US) | ≤8th grade | Median adult reading level in US |
| Clinical/health populations | 5th-6th grade | USDHHS recommendation for health materials |
| Specialized professional populations | 10th-12th grade | Higher literacy assumed, domain vocabulary acceptable |
| Adolescent populations (ages 13-17) | 6th-8th grade | Developmental reading levels |

**Assessment Tools:**
- Flesch-Kincaid Grade Level (most widely used)
- Flesch Reading Ease Score (supplementary)
- Automated readability checks in MS Word, Hemingway Editor, or Readable.com

**Writing Strategies:**
- Use simple sentence structures (subject-verb-object)
- Minimize subordinate clauses
- Prefer common words over synonyms (e.g., "use" not "utilize")
- Avoid jargon unless target population shares specialized vocabulary
- Keep items under 20 words (15 preferred)

**LLM-Specific Challenge:**
LLMs default to sophisticated vocabulary and complex syntax. Explicit prompting required: "Write at 6th-8th grade reading level using simple, everyday language. Avoid complex sentences and academic vocabulary."

**Reference:** Flesch-Kincaid Readability Tests (Wikipedia); Readable.com - Flesch Reading Ease and Flesch-Kincaid Grade Level; PMC5063233 - Readability of Health-Related Quality-of-Life Instruments

---

### Principle 5: Bias Minimization and Fairness

**Standard:** Items must demonstrate measurement equivalence across demographic groups. Differential Item Functioning (DIF) indicates bias.

#### 5a. Types of Bias

**Uniform DIF:** Item difficulty differs consistently across groups matched on the latent trait.
- *Example:* "I feel comfortable speaking up in meetings" may be easier to endorse for Western respondents (individualistic culture) than East Asian respondents (collectivistic culture), independent of actual assertiveness.

**Nonuniform DIF:** Item discrimination varies across groups; the item-trait relationship differs.
- *Example:* "I take charge in group projects" may correlate with leadership for men but with conscientiousness for women due to gender role expectations.

**Benign vs. Adverse DIF:**
- **Benign:** Groups differ because the construct manifests differently in each group (e.g., "I pray regularly" for spirituality differs across religions).
- **Adverse:** Groups differ due to measurement artifacts (e.g., culturally specific idioms, socioeconomic assumptions).

#### 5b. Common Sources of Bias

**Cultural assumptions:**
- Western individualism (e.g., "I prioritize my own goals")
- Specific religious practices (e.g., "I attend religious services weekly")
- Idioms and colloquialisms (e.g., "I go the extra mile")

**Socioeconomic assumptions:**
- Access to resources (e.g., "I have a dedicated workspace at home")
- Specific work contexts (e.g., "I collaborate across time zones")

**Gender/demographic stereotypes:**
- Gendered language (e.g., "I am nurturing" for caregiving)
- Occupation-specific contexts (e.g., "I lead my team" assumes hierarchical role)

**Language complexity:**
- Vocabulary that differs in accessibility across education levels
- Syntax that is harder for non-native speakers

#### 5c. Bias Detection and Mitigation

**During item writing:**
- Avoid group-specific contexts (e.g., "in my office" assumes in-person work)
- Use inclusive language (e.g., "my partner" not "my spouse"; "my team" not "my subordinates")
- Pilot test with diverse demographic groups before finalizing scale

**During validation:**
- Conduct DIF analysis using IRT or Mantel-Haenszel procedures
- Compare item functioning across gender, race/ethnicity, age, education, geographic region
- Flag items with adverse DIF for revision or removal

**LLM-Specific Challenge:**
LLMs trained on Western, English-language corpora reproduce cultural biases. Bias Reviewer agents must explicitly check for:
- Cultural assumptions embedded in examples
- Language complexity that disadvantages non-native speakers
- Context-specific references that exclude segments of the population

**Reference:** PMC2262284 - Item response theory detects differential item functioning; Wikipedia: Differential item functioning; Understanding DIF and DTF (Journal of the Society for Social Work Research, 2017)

---

### Principle 6: Response Scale Alignment

**Standard:** Item stems must align semantically with response anchors. Misalignment introduces response error.

#### 6a. Agreement Scales

**Appropriate for:** Attitudinal statements, beliefs, values

**Stem structure:** Declarative statements in first person
- "I enjoy working on complex problems"
- "I value work-life balance"

**Response anchors (5-point):**
- Strongly Disagree | Disagree | Neither Agree nor Disagree | Agree | Strongly Agree

**Common mistake:** Using agreement scales for behavioral frequency
- **WRONG:** "I arrive on time for meetings" [Strongly Disagree ... Strongly Agree]
- **RIGHT:** "I arrive on time for meetings" [Never ... Always]

#### 6b. Frequency Scales

**Appropriate for:** Behavioral frequency, event occurrence

**Stem structure:** Behavioral statements
- "I check my email outside work hours"
- "I seek feedback from colleagues"

**Response anchors (5-point):**
- Never | Rarely | Sometimes | Often | Always
- OR: Never | Rarely (1-2 times/month) | Sometimes (3-5 times/month) | Often (6-10 times/month) | Very Often (>10 times/month)

#### 6c. Intensity/Magnitude Scales

**Appropriate for:** Experiential states, emotional intensity

**Stem structure:** State descriptions
- "I feel energized when meeting new people"
- "I experience anxiety before presentations"

**Response anchors (5-point):**
- Not at all | Slightly | Moderately | Very | Extremely

#### 6d. Best Practices

- **Match scale type to construct:** Agreement for attitudes, frequency for behaviors, intensity for experiences
- **Maintain polarity consistency:** All scales should run in the same direction (low → high)
- **Use 5-7 response points:** Research shows diminishing returns beyond 7 points; fewer than 5 reduces variability
- **Balance response options:** Equal number of positive and negative options around neutral midpoint
- **Define anchors clearly:** Avoid ambiguous labels (e.g., "Somewhat agree" vs. "Moderately agree")

**LLM-Specific Challenge:**
LLMs may generate stems that mismatch the specified response scale. Item Writer agents must receive explicit examples of stem-scale alignment.

**Reference:** Sawtooth Software - Likert Scale Response Anchors; Cogn-IQ - Likert Scale Psychometric Theory Guide; Frontiers in Psychology (2024) - How does item wording affect participants' responses in Likert scale?

---

### Principle 7: Item Keying and Acquiescence Bias

**Standard:** Use positively keyed items only. Reverse-scored items introduce more problems than they solve.

#### 7a. The Acquiescence Bias Problem

**Acquiescence bias:** Tendency to agree with statements regardless of content ("yea-saying").

**Traditional solution:** Mix positively and negatively keyed items so acquiescence cancels out.

**Modern evidence (2020-2025):** Reverse-scored items create more problems:
- **Method effects:** Reverse items cluster together in factor analysis, creating spurious factors
- **Cognitive burden:** Respondents miss negations, especially under time pressure
- **Linguistic ambiguity:** Double negatives and complex syntax reduce clarity
- **Lower reliability:** Reverse items show lower item-total correlations

#### 7b. Recommended Approach

**For MAPIG:**
- **Use positively keyed items exclusively**
- **Control acquiescence through:**
  - Clear, unambiguous stems
  - Balanced response options
  - Explicit "Neither agree nor disagree" midpoint
  - Cognitive interview pre-testing to detect mindless responding

**Rationale:**
Negatively worded items were intended to detect inattentive responding, but they introduce construct-irrelevant cognitive load. Modern approaches (attention checks, response time monitoring) are more effective.

**Exception:**
If the construct definition includes negative behaviors as theoretically meaningful (e.g., "I avoid social situations" for social anxiety), these are NOT reverse-scored items—they are positively keyed indicators of the construct.

**Reference:** Wikipedia: Acquiescence bias; Cambridge Core (2023) - Heritability of Acquiescence Bias and Item Keying Response Style; PMC3618383 - Social desirability in personality inventories

---

### Principle 8: Semantic Diversity and Redundancy

**Standard:** Items within a facet should sample diverse behavioral manifestations, not paraphrase the same idea.

#### 8a. The Homogeneity-Redundancy Tension

**Internal consistency (α):** Measures inter-item correlation. High α (>.90) traditionally considered desirable.

**Redundancy problem:** High α may indicate excessive item similarity—essentially the same item rephrased multiple times.

**Modern perspective (Boyle, 1991; recent 2025 findings):**
- α close to 1.0 suggests redundancy, not superior measurement
- Ideal range: α = .70-.85 (sufficient consistency without redundancy)
- Item diversity enables broader construct sampling and cross-cultural validity

#### 8b. Operationalizing Semantic Diversity

**Example: Measuring "Workplace Belonging"**

**REDUNDANT (avoid):**
- "I feel like I belong at work"
- "I have a sense of belonging in my workplace"
- "I feel I am a part of my work community"

**DIVERSE (preferred):**
- "My colleagues include me in informal conversations"
- "I feel comfortable expressing my authentic self at work"
- "My contributions are valued by my team"
- "I have meaningful connections with coworkers"

**Why diversity matters:**
Each item samples a different behavioral/experiential facet of belonging: inclusion, authenticity, value recognition, social connection. This provides richer construct coverage.

#### 8c. Detection Methods

**Automated methods:**
- Embedding-based Semantic Analysis Approach (ESAA): Uses NLP to detect semantic similarity
- Cosine similarity between item embeddings (threshold: <0.85 for sufficient diversity)

**Human review:**
- Subject matter experts rate item uniqueness
- Check for mere synonym substitution (e.g., "I am cheerful" vs. "I am upbeat")

**LLM-Specific Challenge:**
LLMs excel at paraphrasing, which can inadvertently create redundant items. Item Writer prompts must specify: "Generate items that capture different behavioral manifestations of [construct], not paraphrases of the same behavior."

**Reference:** ResearchGate - Does item homogeneity indicate internal consistency or item redundancy?; Frontiers in Psychology (2025) - A transformer-based embedding approach to short-form measures; Nature Scientific Reports (2025) - Rethinking psychometrics through LLMs

---

### Principle 9: Facet Coverage and Balancing

**Standard:** For multidimensional constructs, ensure equal representation across facets to avoid construct under-representation.

#### 9a. Hierarchical Structure

**Construct → Domains → Facets → Items**

Example: Big Five Personality
- **Construct:** Personality
- **Domain:** Extraversion
- **Facets:** Sociability, Assertiveness, Energy Level, Positive Affect, Excitement-Seeking, Gregariousness
- **Items:** 4-10 items per facet

#### 9b. Item Allocation Guidelines

| Construct Complexity | Items per Facet | Total Scale Length | Rationale |
|---------------------|----------------|-------------------|-----------|
| Unidimensional | N/A | 5-10 items | Simple construct, high homogeneity acceptable |
| Multidimensional (2-3 facets) | 4-6 per facet | 8-18 items | Sufficient coverage, manageable length |
| Hierarchical (5+ facets) | 4-8 per facet | 20-50 items | Complex construct requires comprehensive sampling |

**Equal representation:**
When facets are theoretically equivalent components of the construct, allocate items equally across facets. Unequal allocation implies differential weighting.

**Example: IPIP-NEO-120**
- 5 domains × 6 facets per domain = 30 facets
- 30 facets × 4 items per facet = 120 items
- Equal representation ensures no facet dominates the domain score

#### 9c. Construct Coverage

**Construct deficiency:** Important facets of the construct are under-represented or absent.
- *Example:* Measuring "job satisfaction" only with items about pay and benefits, omitting work relationships, autonomy, and meaning.

**Construct saturation:** Items are redundant; no new construct variance captured.
- *Example:* 15 items all asking about "feeling happy at work" in slightly different words.

**Solution:** During construct definition phase, identify facets through:
- Literature review of established models
- Subject matter expert (SME) panels
- Cognitive interviews with target population

#### 9d. Facet Validation

**Confirmatory Factor Analysis (CFA):** Test whether items cluster into theorized facets.

**Bifactor models:** Separate general construct variance from facet-specific variance.

**Item Pool Visualization (IPV):** Graphical method to identify over-represented and under-represented construct regions.

**Reference:** PMC12689397 - Mapping the multifaceted resilience construct; Sage Journals (1993) - A Facet Analysis Approach to Content and Construct Validity; International Personality Item Pool (IPIP) - Multi-Construct Inventories

---

### Principle 10: Convergent and Discriminant Validity

**Standard:** Items should correlate highly with other measures of the SAME construct (convergent validity) and weakly with measures of DIFFERENT constructs (discriminant validity).

#### 10a. Convergent Validity

**Definition:** Items measuring the same construct should correlate positively.

**Operationalization:**
- Inter-item correlations within a scale: r = .30-.70 (Boyle, 1991)
- Item-total correlation: r ≥ .30 (below this threshold, item may not belong)
- Correlation with established measures of the construct: r ≥ .50

**Example:**
If developing a new "Workplace Autonomy" scale, items should correlate r ≥ .50 with existing autonomy measures (e.g., Work Design Questionnaire autonomy subscale).

#### 10b. Discriminant Validity

**Definition:** Items should NOT correlate highly with theoretically distinct constructs.

**Operationalization:**
- Correlation with unrelated constructs: r < .30
- Correlation with related-but-distinct constructs: r = .20-.40 (acceptable if constructs are in the same nomological network)

**Example:**
"Workplace Autonomy" items should NOT correlate r > .50 with "Job Satisfaction" (distinct construct), even though autonomy predicts satisfaction.

#### 10c. Construct Contamination

**Problem:** Item inadvertently measures multiple constructs, inflating correlations.

**Example:**
- Item: "I make my own decisions about how to complete my work and feel satisfied with this independence"
- Contamination: Measures autonomy AND satisfaction, conflating two constructs

**Detection:**
- Multitrait-multimethod (MTMM) matrix analysis
- Check item-total correlations with multiple scales
- SME review: "Could this item belong to multiple constructs?"

#### 10d. LLM-Specific Challenge

LLMs may generate items that are semantically rich but theoretically impure. Content Reviewer agents must explicitly evaluate:
- "Does this item measure ONLY the target construct, or does it tap related constructs?"
- "If I removed the construct label, could this item plausibly belong to a different scale?"

**Reference:** Questionmark - Understanding Convergent & Discriminant Validity; Wikipedia: Convergent validity; PMC6754793 - Constructing Validity: New Developments

---

## LLM-Specific Challenges in Item Generation

### Challenge 1: Prompt Sensitivity and Inconsistency

**Problem:** Trivial prompt perturbations (extra spaces, punctuation, example order) produce up to 76% variation in LLM output quality.

**Implications for MAPIG:**
- Item quality may vary across runs even with identical inputs
- Prompt engineering must be robust to minor variations

**Mitigation Strategies:**
1. **Structured prompts with explicit constraints:**
   - "Generate exactly 10 items. Each item must be a single sentence under 20 words."
   - "Use 6th-8th grade reading level. Avoid jargon and complex vocabulary."
   - "Each item measures [construct] and ONLY [construct]. Do not combine multiple ideas."

2. **Few-shot examples:**
   - Provide 3-5 high-quality example items that model desired characteristics
   - Examples should demonstrate diversity, clarity, construct alignment

3. **Temperature and sampling:**
   - Lower temperature (0.3-0.5) for more consistent output
   - Higher temperature (0.7-0.9) for more diverse item generation

4. **Iterative refinement:**
   - Generate 2x the needed items, select best items via validation agent
   - Multi-round generation with feedback loops

**Reference:** arXiv 2506.16697 - LLM VALIDITY 1; arXiv 2505.08245 - Large Language Model Psychometrics: A Systematic Review

---

### Challenge 2: Anthropomorphic Bias and "Agree Bias"

**Problem:** LLMs fine-tuned with RLHF exhibit systematic agreement bias—preferring socially desirable, agreeable responses.

**Implications for MAPIG:**
- Generated items may skew toward positively valenced, socially desirable content
- Items may lack psychological realism for negatively valenced constructs (e.g., neuroticism, psychopathology)

**Mitigation Strategies:**
1. **Explicit counter-instructions:**
   - "Generate items that measure [construct] realistically, including both socially desirable and undesirable manifestations."
   - "Avoid generating only positive or agreeable statements. Include items that capture the full range of [construct]."

2. **Construct-specific prompting:**
   - For neuroticism: "Generate items describing experiences of anxiety, worry, and emotional instability as they naturally occur, without minimizing or softening the language."

3. **Bias Reviewer agent:**
   - Explicitly check for social desirability bias
   - Flag items that are implausibly positive or self-aggrandizing

**Reference:** Nature Machine Intelligence (2025) - A psychometric framework for evaluating personality traits in LLMs; OpenReview (2024) - Quantifying AI Psychology

---

### Challenge 3: Lack of Psychometric Structural Validity

**Problem:** LLMs lack internal models of latent constructs. They generate items based on semantic similarity to training examples, not psychometric theory.

**Implications for MAPIG:**
- Items may be semantically plausible but psychometrically invalid
- Factor structure of LLM-generated items may not align with theoretical models

**Mitigation Strategies:**
1. **Theory-driven prompting:**
   - "Generate items based on the following facets of [construct]: [facet 1], [facet 2], [facet 3]."
   - "Each item must operationalize one specific facet. Distribute items evenly across facets."

2. **Post-generation validation:**
   - LLM-as-judge scoring for construct alignment (1-10 scale)
   - Automatic rejection and regeneration for items scoring <7
   - Human SME review before finalization

3. **Evidence-bounded generation:**
   - Ground item generation in academic literature and validated scales
   - Require citations to source material that inspired each item

**Reference:** British Journal of Educational Technology (2025) - Leveraging LLM respondents for item evaluation; arXiv 2507.05890 - Psychometric Item Validation Using Virtual Respondents

---

### Challenge 4: Semantic Redundancy through Paraphrasing

**Problem:** LLMs are optimized for paraphrasing. When asked to generate multiple items, they may produce semantic near-duplicates.

**Implications for MAPIG:**
- Item pools with high α (>.90) but low construct breadth
- Reduced external validity and generalizability

**Mitigation Strategies:**
1. **Explicit diversity instructions:**
   - "Generate items that capture DIFFERENT behavioral manifestations of [construct]. Do not paraphrase or reword the same idea."
   - "Each item should describe a unique aspect of [construct]. Avoid synonym substitution."

2. **Semantic similarity detection:**
   - Compute cosine similarity between item embeddings
   - Flag item pairs with similarity >0.85 for revision

3. **Facet-based generation:**
   - Generate items one facet at a time
   - Reduces within-generation redundancy

**Reference:** MDPI (2025) - An Embedding-Based Semantic Analysis Approach: Redundancy Detection; ResearchGate (1991) - Does item homogeneity indicate internal consistency or item redundancy?

---

### Challenge 5: Context Collapse and Overgeneralization

**Problem:** LLMs generate generic items that lack contextual specificity, or overly specific items that don't generalize.

**Implications for MAPIG:**
- Items may be too abstract ("I am successful") or too narrow ("I complete TPS reports on time")

**Mitigation Strategies:**
1. **Specify appropriate level of abstraction:**
   - For general personality: "Generate items that apply across contexts (work, social, personal)."
   - For workplace assessment: "Generate items specific to workplace behavior, but generalizable across industries and roles."

2. **Target population grounding:**
   - "Generate items appropriate for [target population]. Avoid context-specific references that exclude segments of this population."

3. **Concrete behavioral language:**
   - "Use specific, observable behaviors rather than abstract traits."
   - "Prefer 'I express my opinions in meetings' over 'I am assertive.'"

**Reference:** HiPeople - What Is a Psychometric Assessment?; PMC9265707 - Item-Level Psychometric Analysis in Workers

---

## Item Writing Workflow for MAPIG Agents

### Phase 1: Construct Specification (Human Input)

**Required inputs:**
1. **Construct name** (e.g., "Workplace Belonging")
2. **Construct definition** (theoretical, 2-3 sentences)
3. **Facets** (if multidimensional; with definitions)
4. **Construct boundaries** (what this is NOT; exclusions)
5. **Target population** (reading level, cultural context, domain)
6. **Response scale** (agreement, frequency, intensity + anchors)
7. **Item count** (total and per facet)

**Deliverable:** Comprehensive construct specification document that grounds all agents.

---

### Phase 2: Evidence Retrieval (Web Surfer Agent)

**Objective:** Ground item generation in peer-reviewed literature and validated measures.

**Search strategy:**
- Academic databases (PsycINFO, PubMed, Google Scholar)
- Keywords: [construct name] + "scale development", "measurement", "psychometric properties"
- Item examples from validated scales (for inspiration, NOT reproduction)

**Deliverables:**
1. **Theoretical models:** How is this construct conceptualized in the literature?
2. **Facet structures:** What dimensions/facets do established scales measure?
3. **Item exemplars:** What do high-quality items look like? (paraphrased, not copied)
4. **Boundary conditions:** What constructs are commonly confused with this one?
5. **Populations:** What populations have been studied? Any DIF concerns?

**Guardrails:**
- Never copy published items verbatim (copyright violation)
- Paraphrase examples for inspiration only
- Cite all sources for audit trail

---

### Phase 3: Item Generation (Item Writer Agent)

**Prompt structure:**

```
You are an expert psychometrician writing items for a [construct] scale targeting [population].

CONSTRUCT DEFINITION:
[from specification document]

FACETS:
1. [Facet 1]: [definition]
2. [Facet 2]: [definition]
...

EVIDENCE BASE:
[Summarized findings from Web Surfer]

RESPONSE SCALE:
[e.g., 5-point Likert: Strongly Disagree to Strongly Agree]

CONSTRAINTS:
- Reading level: [6th-8th grade / as specified]
- Item length: Maximum 20 words, prefer 10-15
- One idea per item (no double-barreled questions)
- Concrete, behavioral language (avoid abstractions)
- Positively keyed only
- No vague quantifiers without definitions
- No ambiguous referents (pronouns must have clear antecedents)
- Items must align semantically with response scale

DIVERSITY REQUIREMENTS:
- Generate items capturing DIFFERENT behavioral manifestations of each facet
- Avoid paraphrasing or synonym substitution
- Each item should be distinct and non-redundant

TASK:
Generate [N items per facet] for each facet, total [N] items.

For each item, provide:
1. Item text
2. Facet assignment
3. Rationale (why this item measures this facet)
4. Evidence citation (source that inspired this item)

EXAMPLE (for illustration only, generate new items):
- Item: "I seek feedback from colleagues after completing projects"
- Facet: Openness to Feedback
- Rationale: Operationalizes proactive feedback-seeking behavior
- Citation: Zhou & George (2001) - feedback-seeking as learning orientation
```

**Quality gates:**
- Auto-check reading level (Flesch-Kincaid)
- Auto-check item length
- Auto-check for banned phrases (double-barreled keywords, vague quantifiers)

---

### Phase 4: Multi-Agent Review

#### 4a. Content Reviewer Agent

**Objective:** Evaluate construct correspondence and distinctiveness.

**Review protocol:**

For each item:
1. **Construct alignment (1-10):** Does this item measure the target construct?
2. **Facet alignment (1-10):** Does this item measure the assigned facet?
3. **Distinctiveness (1-10):** Does this item measure ONLY the target construct, or does it tap related constructs?
4. **Contamination risk:** Could this item plausibly belong to a different construct? If yes, which one?

**Scoring rubric:**
- **9-10:** Perfect alignment, no ambiguity
- **7-8:** Strong alignment, minor refinement possible
- **5-6:** Moderate alignment, significant revision needed
- **1-4:** Poor alignment, reject and regenerate

**Rejection criteria:**
- Construct alignment <7
- Contamination with excluded constructs (from specification document)

**Feedback format:**
- Issue: [specific problem]
- Severity: [1-5 scale]
- Suggested edit: [concrete revision]

---

#### 4b. Linguistic Reviewer Agent

**Objective:** Evaluate clarity, precision, and readability.

**Review protocol:**

For each item:
1. **Clarity (binary):** Can this item be interpreted in only one way?
2. **Double-barreled (binary):** Does this item ask about multiple ideas?
3. **Vague quantifiers (binary):** Does this item use undefined frequency/intensity terms?
4. **Ambiguous referents (binary):** Do pronouns have clear antecedents?
5. **Reading level (Flesch-Kincaid):** Is this at target level?
6. **Word count:** Is this under 20 words?

**Flagged patterns:**
- Conjunctions in predicate (and/or/but)
- Pronouns without antecedents (it, they, this, things)
- Vague quantifiers (often, sometimes, rarely) without scale definition
- Complex syntax (multiple subordinate clauses)
- Jargon not appropriate for target population

**Feedback format:**
- Issue: "Double-barreled: combines 'seeking feedback' AND 'implementing suggestions'"
- Severity: 5 (blocking)
- Suggested edit: "I seek feedback from colleagues after completing projects" (remove second idea)

---

#### 4c. Bias Reviewer Agent

**Objective:** Detect construct-irrelevant variance due to demographic, cultural, or contextual assumptions.

**Review protocol:**

For each item:
1. **Cultural assumptions (binary):** Does this item assume Western individualism, specific cultural practices, or idioms?
2. **Socioeconomic assumptions (binary):** Does this item assume access to resources (e.g., dedicated workspace, technology)?
3. **Context specificity (binary):** Does this item assume a specific work arrangement (in-person, remote, managerial role)?
4. **Gendered language (binary):** Does this item use gendered terms or stereotypes?
5. **Language complexity (Flesch-Kincaid):** Is this accessible to non-native speakers?

**Flagged patterns:**
- Cultural idioms ("go the extra mile," "think outside the box")
- Religious/spiritual references (unless construct-relevant)
- Gendered pronouns or role assumptions
- Context requiring specific job features (e.g., "in my office," "during my commute")
- Assumptions about family structure, education, or resources

**Feedback format:**
- Issue: "Assumes in-person work context ('in my office')"
- Severity: 4 (high; excludes remote workers)
- Suggested edit: "I have a comfortable workspace"

---

### Phase 5: Meta Editor Agent (Revision)

**Objective:** Reconcile reviewer feedback and revise items while maintaining construct coverage.

**Revision protocol:**

1. **Triage feedback by severity:**
   - Severity 5: Blocking issues, must fix
   - Severity 3-4: High-priority revisions
   - Severity 1-2: Minor refinements

2. **Prioritize construct validity over all else:**
   - If clarity and construct alignment conflict, prioritize alignment (then revise for clarity)

3. **Maintain facet balance:**
   - If items are rejected, regenerate to maintain equal representation across facets

4. **Document changes:**
   - Original item, revised item, rationale for change, reviewer feedback addressed

**Revision strategies:**

| Issue | Strategy |
|-------|----------|
| Double-barreled | Split into two items OR select one idea |
| Vague quantifier | Remove quantifier OR add scale definition |
| Ambiguous referent | Replace pronoun with explicit noun |
| Reading level too high | Simplify vocabulary, shorten sentence |
| Cultural assumption | Use universal context, remove idiom |
| Construct contamination | Narrow item to single construct, remove conflated idea |

---

### Phase 6: Critic Agent (Decision)

**Objective:** Determine if item set is ready for finalization or requires another iteration.

**Decision criteria:**

**ACCEPT (finalize):**
- All items have construct alignment ≥7
- No blocking (severity 5) issues remain
- Facet balance achieved (equal items per facet ±1)
- Reading level targets met
- No DIF red flags identified

**REVISE (another iteration):**
- ≥20% of items have construct alignment <7
- ≥3 blocking issues remain
- Facet imbalance >2 items between facets

**STOP (max iterations reached):**
- After 3 revision cycles, accept best available items
- Flag remaining issues for human SME review

**NEEDS_HUMAN:**
- Conflicting reviewer feedback that cannot be algorithmically resolved
- Construct definition ambiguity
- Novel bias concerns requiring policy decision

---

### Phase 7: LLM-as-Judge Validation (NEW for MAPIG)

**Objective:** Numeric scoring of construct validity before human review.

**Validation protocol:**

For each item, LLM-as-judge (Claude Opus) rates:

1. **Construct correspondence (1-10):**
   - Prompt: "On a scale of 1-10, how well does this item measure [construct] as defined: [definition]? Consider: Does this item capture a specific, observable manifestation of the construct? Could a person high on this construct plausibly endorse this item?"

2. **Distinctiveness (1-10):**
   - Prompt: "On a scale of 1-10, how well does this item measure ONLY [construct] and not [excluded constructs]? Consider: Could this item plausibly belong to a different scale?"

3. **Clarity (1-10):**
   - Prompt: "On a scale of 1-10, how clear and unambiguous is this item? Consider: Can this be interpreted in only one way? Are all referents explicit?"

4. **Overall quality (1-10):**
   - Aggregate of above dimensions

**Automatic rejection:**
- Items scoring <7 on construct correspondence are automatically flagged for regeneration
- Maximum 3 regeneration attempts per item
- After 3 attempts, proceed with best-scoring items and flag for human review

**Advantages over embedding similarity:**
- Transparent reasoning (LLM provides justification for scores)
- Aligns with psychometric theory (construct validity, not just semantic similarity)
- Actionable feedback for revision

**Reference:** British Journal of Educational Technology (2025) - Leveraging LLM respondents for item evaluation

---

## Summary: Dos and Don'ts for MAPIG Agents

### DO:

✓ Write items at 6th-8th grade reading level for general populations
✓ Use concrete, behavioral language ("I seek feedback" not "I am open-minded")
✓ Write single-idea items (one behavior, one context, one construct)
✓ Use positively keyed items exclusively
✓ Match stem structure to response scale (declarative for agreement, behavioral for frequency)
✓ Generate semantically diverse items across facets (not paraphrases)
✓ Balance items equally across facets for multidimensional constructs
✓ Specify explicit referents (avoid pronouns without antecedents)
✓ Ground items in peer-reviewed literature and validated scales
✓ Pilot test with diverse demographic groups before finalizing
✓ Use LLM-as-judge validation with numeric scoring and automatic rejection
✓ Provide evidence citations for every item (audit trail)

### DON'T:

✗ Combine multiple ideas in one item (double-barreled questions)
✗ Use vague quantifiers without definitions ("often," "sometimes," "rarely")
✗ Include ambiguous referents ("it," "they," "things" without clear antecedents)
✗ Write reverse-scored items (use positively keyed only)
✗ Exceed target reading level (check Flesch-Kincaid)
✗ Paraphrase the same idea multiple times (avoid semantic redundancy)
✗ Assume specific cultural contexts, work arrangements, or resources
✗ Use gendered language or stereotypes
✗ Mix item types within a scale (e.g., attitudes + behaviors on same response scale)
✗ Generate items without evidence grounding (every item needs a source)
✗ Copy published items verbatim (copyright violation)
✗ Ignore facet balance (unequal representation biases domain scores)

---

## Confidence Assessment and Gaps

### HIGH Confidence

| Area | Confidence | Sources |
|------|------------|---------|
| Construct validity principles | HIGH | AERA/APA/NCME 2014 Standards, PMC6754793 |
| Double-barreled question avoidance | HIGH | Qualtrics 2024, Kantar 2024, Wikipedia |
| DIF and bias detection | HIGH | PMC2262284, Wikipedia DIF, SSWR 2017 |
| Reading level targeting | HIGH | Flesch-Kincaid literature, PMC5063233 |
| Likert scale best practices | HIGH | Cogn-IQ, Sawtooth, Frontiers 2024 |
| LLM-specific challenges | HIGH | arXiv 2025, Nature MI 2025, BJET 2025 |

### MEDIUM Confidence

| Area | Confidence | Sources |
|------|------------|---------|
| Vague quantifiers | MEDIUM | Empirical evidence (Robie & Risavy 2020) contradicts traditional guidance; context-dependent |
| Reverse-scored items | MEDIUM | Strong recent evidence against, but some fields still use; evolving consensus |
| Optimal items per facet | MEDIUM | No universal standard; depends on construct complexity |

### LOW Confidence / Gaps

| Area | Confidence | Notes |
|------|------------|-------|
| LLM prompt engineering for psychometrics | LOW | Emerging field; best practices still being established |
| Threshold for semantic redundancy | LOW | No consensus on cosine similarity cutoffs; needs empirical validation |
| Cross-cultural validity of LLM-generated items | LOW | Limited research on non-English, non-Western populations |

### Gaps to Address in Future Research

1. **Empirical validation of MAPIG-generated items:**
   - Pilot test with target populations
   - Compare psychometric properties to human-written items
   - Conduct DIF analysis across demographic groups

2. **Optimal LLM-as-judge thresholds:**
   - What score threshold (7? 8?) maximizes construct validity?
   - How many regeneration attempts are optimal?

3. **Prompt engineering benchmarks:**
   - Systematic evaluation of prompt variations
   - Few-shot example selection strategies

4. **Cross-cultural adaptation:**
   - Can LLMs generate culturally adapted items for non-Western populations?
   - How to detect subtle cultural bias in LLM outputs?

---

## Sources

### Psychometric Standards and Principles

- [Standards for Educational & Psychological Testing (AERA/APA/NCME 2014 Edition)](https://www.aera.net/publications/books/standards-for-educational-psychological-testing-2014-edition)
- [Frontiers in Psychology (2024): Psychological, psychiatric, and behavioral sciences measurement scales: best practice guidelines](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1494261/full)
- [Constructing Validity: New Developments in Creating Objective Measuring Instruments (PMC6754793)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6754793/)
- [Construct Validity: Advances in Theory and Methodology (PMC2739261)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2739261/)

### Item Writing Best Practices

- [PSI Services: Item Writing and Exam Assembly in Credentialing](https://www.psiexams.com/knowledge-hub/item-writing-and-exam-assembly-in-credentialing-importance-and-best-practices/)
- [PNCB Item Writing Manual and Style Guide (November 2024)](https://www.pncb.org/sites/default/files/resources/PNCB_Item_Writing_Manual.pdf)
- [Do item-writing flaws reduce examinations psychometric quality? (Springer 2016)](https://link.springer.com/article/10.1186/s13104-016-2202-4)

### Double-Barreled Questions

- [Qualtrics: The Dreaded Double-barreled Question & How to Avoid it](https://www.qualtrics.com/articles/strategy-research/double-barreled-question/)
- [Kantar: Double-barrelled questions](https://www.kantar.com/inspiration/research-services/double-barrelled-questions-pf)
- [Wikipedia: Double-barreled question](https://en.wikipedia.org/wiki/Double-barreled_question)

### Vague Quantifiers and Clarity

- [European Journal of Psychological Assessment (2020): Not Very Powerful: The Influence of Negations and Vague Quantifiers](https://econtent.hogrefe.com/doi/10.1027/1015-5759/a000539)
- [Frontiers in Psychology (2025): Advancing the psychometrics of reverse-keyed items](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1684612/full)
- [PMC11937031: Construct-irrelevant item attributes: a framework to classifying items](https://pmc.ncbi.nlm.nih.gov/articles/PMC11937031/)

### Reading Level and Readability

- [Readable.com: Flesch Reading Ease and Flesch Kincaid Grade Level](https://readable.com/readability/flesch-reading-ease-flesch-kincaid-grade-level/)
- [Wikipedia: Flesch–Kincaid readability tests](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)
- [PMC5063233: Readability of Common Health-Related Quality-of-Life Instruments](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063233/)

### DIF and Bias Detection

- [PMC2262284: Item response theory detects differential item functioning](https://pmc.ncbi.nlm.nih.gov/articles/PMC2262284/)
- [Wikipedia: Differential item functioning](https://en.wikipedia.org/wiki/Differential_item_functioning)
- [Journal of the Society for Social Work and Research (2017): Understanding DIF and DTF](https://www.journals.uchicago.edu/doi/full/10.1086/691525)
- [Columbia University Mailman School: Differential Item Functioning](https://www.publichealth.columbia.edu/research/population-health-methods/differential-item-functioning)

### Acquiescence Bias and Item Keying

- [Wikipedia: Acquiescence bias](https://en.wikipedia.org/wiki/Acquiescence_bias)
- [Cambridge Core (2023): Heritability of Acquiescence Bias and Item Keying Response Style](https://www.cambridge.org/core/journals/twin-research-and-human-genetics/article/heritability-of-acquiescence-bias-and-item-keying-response-style-associated-with-the-hexaco-personality-scale/098D31129EC9FEB89436E056E784C312)
- [PMC3618383: Social desirability in personality inventories](https://pmc.ncbi.nlm.nih.gov/articles/PMC3618383/)

### Likert Scale Construction

- [Cogn-IQ: Likert Scale Psychometric Theory Guide](https://www.cogn-iq.org/learn/theory/likert-scale/)
- [Sawtooth Software: Likert Scale Response Anchors](https://sawtoothsoftware.com/resources/knowledge-base/design-and-methodology-issues/likert-scale-response-anchors)
- [Frontiers in Psychology (2024): How does item wording affect participants' responses in Likert scale?](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1304870/full)

### Semantic Redundancy and Item Diversity

- [ResearchGate (1991): Does item homogeneity indicate internal consistency or item redundancy?](https://www.researchgate.net/publication/222466204_Does_item_homogeneity_indicate_internal_consistency_or_item_redundancy_in_psychometric_scales)
- [Frontiers in Psychology (2025): A transformer-based embedding approach to short-form measures](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1640864/full)
- [MDPI (2025): An Embedding-Based Semantic Analysis Approach: Redundancy Detection](https://www.mdpi.com/2079-3200/13/1/11)
- [Nature Scientific Reports (2025): Rethinking psychometrics through LLMs](https://www.nature.com/articles/s41598-025-21289-8)

### Facet Coverage and Construct Representation

- [PMC12689397: Mapping the multifaceted resilience construct: a facet-based approach](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689397/)
- [Sage Journals (1993): A Facet Analysis Approach to Content and Construct Validity](https://journals.sagepub.com/doi/10.1177/0013164493053002005)
- [Frontiers in Psychology (2015): Bifactor analysis and construct validity](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.00404/full)

### Convergent and Discriminant Validity

- [Conjointly: Convergent & Discriminant Validity](https://conjointly.com/kb/convergent-and-discriminant-validity/)
- [Questionmark: Understanding Convergent & Discriminant Validity](https://www.questionmark.com/resources/blog/understanding-convergent-discriminant-validity/)
- [Wikipedia: Convergent validity](https://en.wikipedia.org/wiki/Convergent_validity)

### LLM-Generated Items and Quality Challenges

- [British Journal of Educational Technology (2025): Leveraging LLM respondents for item evaluation](https://bera-journals.onlinelibrary.wiley.com/doi/full/10.1111/bjet.13570)
- [arXiv 2506.16697: LLM VALIDITY 1](https://arxiv.org/pdf/2506.16697)
- [arXiv 2505.08245: Large Language Model Psychometrics: A Systematic Review](https://arxiv.org/html/2505.08245v1)
- [arXiv 2507.05890: Psychometric Item Validation Using Virtual Respondents](https://arxiv.org/html/2507.05890)
- [Nature Machine Intelligence (2025): A psychometric framework for evaluating personality traits in LLMs](https://www.nature.com/articles/s42256-025-01115-6)
- [OpenReview (2024): Quantifying AI Psychology: A Psychometric Benchmark for LLMs](https://openreview.net/forum?id=31UkFGMy8t)

### Personality Assessment and IPIP

- [International Personality Item Pool (IPIP) Home](https://ipip.ori.org/)
- [PMC7871748: Assessing the Structure of the Five Factor Model (IPIP-NEO-120)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7871748/)
- [ResearchGate: A Test of the IPIP Representation of the Revised NEO Personality Inventory](https://www.researchgate.net/publication/263130460_A_Test_of_the_International_Personality_Item_Pool_Representation_of_the_Revised_NEO_Personality_Inventory_and_Development_of_a_120-Item_IPIP-Based_Measure_of_the_Five-Factor_Model)

### Context-Specific vs. General Assessment

- [HiPeople: What Is a Psychometric Assessment and How to Conduct It?](https://www.hipeople.io/glossary/psychometric-assessment)
- [PMC9265707: Item-Level Psychometric Analysis of the Psychosocial Processes at Work Scale](https://pmc.ncbi.nlm.nih.gov/articles/PMC9265707/)

### Subject Matter Expert Review

- [Assess.com: Subject Matter Experts in Exam Development](https://assess.com/subject-matter-experts-exam-development/)
- [Wikipedia: Subject-matter expert](https://en.wikipedia.org/wiki/Subject-matter_expert)
- [PSI Exams: Tests developed by psychometric experts](https://www.psiexams.com/test-owners/test-development/psychometrics/)

### LLM Prompt Engineering and Testing

- [Prompt Engineering Guide: LLM Evaluation](https://www.promptingguide.ai/prompts/evaluation)
- [Patronus AI: AI LLM Test Prompts Best Practices](https://www.patronus.ai/llm-testing/ai-llm-test-prompts)
- [Braintrust: A/B testing for LLM prompts](https://www.braintrust.dev/articles/ab-testing-llm-prompts)

---

*Research completed: 2026-03-08*
*Confidence: HIGH for established principles, MEDIUM for emerging LLM-specific best practices*
*Recommendation: Use this document to refine agent prompts, especially Item Writer, Content Reviewer, Linguistic Reviewer, and Bias Reviewer agents. Implement LLM-as-judge validation with automatic rejection threshold ≥7.*
