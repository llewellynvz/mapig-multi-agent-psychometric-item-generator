# Phase 2: Agent Architecture Optimization - Research

**Researched:** 2026-03-08
**Domain:** LLM-based psychometric item generation agent prompt optimization
**Confidence:** MEDIUM-HIGH

## Summary

This phase optimizes 7 agent prompts (Item Writer, Content Reviewer, Linguistic Reviewer, Bias Reviewer, Meta Editor, Critic, Web Surfer) using research-backed psychometric principles from established test development standards (AERA/APA/NCME 2014, ITC Guidelines) and recent LLM agent engineering best practices. The research reveals 10 core psychometric principles for Item Writer optimization, a 7-type bias taxonomy for Bias Reviewer enhancement, and adaptive threshold strategies for Critic routing decisions.

Key findings: (1) Recent 2026 research demonstrates LLM-generated items achieve human-equivalent validity when using structured prompting with quality control rules and chain-of-thought reasoning; (2) Intersectional DIF analysis detects 4-8x more bias than single-dimension approaches; (3) Positive keying only is increasingly recommended due to reverse-item complications; (4) Semantic diversity requirements prevent item redundancy while maintaining construct coverage.

**Primary recommendation:** Use structured prompt engineering with explicit psychometric checklists, chain-of-thought reasoning for complex decisions (Item Writer, Bias Reviewer), and severity-based adaptive routing in Critic. Implement multi-pass bias review with separate evaluations per bias type to capture intersectional effects.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Research Strategy:**
- Primary sources: AERA/APA/NCME Standards (2014), ITC Guidelines, canonical psychometric textbooks
- Extraction approach: Actionable, concrete principles as checklists (e.g., "avoid double-barreled items")
- Research focus: Deep treatment for Item Writer + Bias Reviewer (10 principles + 7 bias types). Lighter treatment for other 5 agents.
- Documentation format: Single consolidated RESEARCH.md (not separate per-agent files)

**Prompt Design Approach:**
- Principle embedding: Supplement existing Item Writer prompt structure (sections A-D) with missing psychometric principles. Keep what works, fill gaps.
- Examples: 1-2 examples only for complex concepts (semantic diversity, intersectional bias). Rely on instructions for straightforward principles.
- Reading level enforcement: Specify targets in prompts as guidelines (6th-8th general, 5th-6th clinical, 10th-12th specialized). No automated Flesch-Kincaid measurement—agent judgment only.
- Chain-of-thought reasoning: Required for Item Writer (explain facet targeting, wording choices) and Bias Reviewer (explain bias detection reasoning). Optional for other agents.

### Claude's Discretion

- Specific 10 psychometric principles to include in Item Writer
- Specific 7 bias types taxonomy structure for Bias Reviewer
- Whether to implement multi-pass bias review (separate evaluation per type) or single comprehensive pass
- How to structure Meta Editor's facet balancing guidance
- How to refine Critic's adaptive iteration thresholds
- Whether to A/B test 7→6 agent consolidation (AGT-11 optional requirement)

### Deferred Ideas (OUT OF SCOPE)

None—discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGT-01 | Refine Item Writer prompt with 10 core psychometric principles | Section: Standard Stack (10 Principles), Architecture Patterns (Prompt Structure) |
| AGT-02 | Add semantic diversity instructions to prevent over-paraphrasing | Section: Common Pitfalls (Item Redundancy), Code Examples (Semantic Diversity) |
| AGT-03 | Enforce reading level targeting (6th-8th general, 5th-6th clinical, 10th-12th specialized) | Section: Standard Stack (Flesch-Kincaid), Architecture Patterns (Reading Level Guidelines) |
| AGT-04 | Positive keying only (eliminate reverse-scored item generation) | Section: Don't Hand-Roll (Reverse Items), Common Pitfalls (Acquiescence Bias) |
| AGT-05 | Refine Content Reviewer with construct correspondence criteria | Section: Architecture Patterns (Content Reviewer Enhancement) |
| AGT-06 | Refine Linguistic Reviewer with vague quantifier context rules | Section: Common Pitfalls (Vague Quantifiers), Code Examples (Time Anchoring) |
| AGT-07 | Refine Bias Reviewer with 7-type taxonomy + intersectionality check | Section: Standard Stack (7 Bias Types), Architecture Patterns (Multi-Pass Review) |
| AGT-08 | Implement multi-pass bias review (separate evaluations per bias type) | Section: Architecture Patterns (Multi-Pass Review), Code Examples (Bias Detection) |
| AGT-09 | Update Meta Editor with facet balancing enforcement | Section: Architecture Patterns (Meta Editor Enhancement) |
| AGT-10 | Enhance Critic with adaptive iteration thresholds (severity-based routing) | Section: Architecture Patterns (Critic Enhancement), Code Examples (Adaptive Routing) |
| AGT-11 | Optional: A/B test Content + Bias reviewer consolidation (7→6 agents) | Section: Open Questions (Agent Consolidation) |

</phase_requirements>

## Standard Stack

### Core Psychometric Standards

| Source | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| AERA/APA/NCME Standards | 2014 (Open Access 2021) | Authoritative test development standards covering validity, fairness, bias | Joint publication by three major professional organizations; open access since 2021; defines fairness as "fundamental validity issue" |
| ITC Guidelines | 2022 (Technology-Based) | International best practices for test development, adaptation, administration | Multi-year collaboration with 100+ authors; covers digital assessment, validity, fairness, accessibility |
| Flesch-Kincaid Grade Level | Standard formula | Reading level assessment for item accessibility | Most widely used readability formula; appropriate for most writing; correlates with comprehension |

### Supporting Research

| Source | Publication | Purpose | When to Use |
|--------|-------------|---------|-------------|
| Creative Psychometric Item Generator (CPIG) | 2024 (arXiv) | LLM-based item generation framework with validation | LLM prompt engineering for item generation; quality control rules; selection strategies |
| Intersectional DIF Analysis | Russell & Kaplan 2021 (PARE) | Detecting bias across combined identity categories | Multi-dimensional bias detection; 4-8x more sensitive than single-dimension DIF |
| Reverse-Item Psychometrics | Frontiers Psychology 2025 | Linguistic and cognitive issues with reverse-keyed items | Understanding why positive keying is preferred; acquiescence response style |
| Generative AI Scale Development | Keane & McNaughton 2026 | AI-assisted psychometric scale development | Semantic diversity strategies; redundancy detection; automated quality checks |

### LLM Agent Engineering

| Tool/Pattern | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| Structured Outputs | Anthropic/OpenAI 2025 | Schema enforcement for agent responses | 100% adherence target; prevents schema drift; machine-parseable validation |
| Chain-of-Thought Prompting | Standard 2022+ | Explicit reasoning before decisions | Reduces hallucination frequency; improves complex reasoning; enables transparency |
| Multi-Agent Routing | 2025 patterns | Severity-based adaptive thresholds for workflow decisions | Dynamic resource allocation; priority-based routing; cost-efficient architectures |

**Installation:**

Existing dependencies already installed:
```bash
# Python backend (already in requirements.txt)
pip install anthropic openai pydantic langchain-core langgraph

# Testing (already installed: pytest 9.0.2)
pip install pytest
```

## Architecture Patterns

### Item Writer Prompt Structure (AGT-01, AGT-02, AGT-03, AGT-04)

**Current structure (keep):** Sections A-D format
- A: Construct fidelity and domain coverage
- B: Wording and comprehension
- C: Keying and polarity
- D: Bias minimization pre-check

**Add 10 core psychometric principles (consolidated from research):**

1. **Unidimensionality** (Section A): Each item measures single facet of construct; avoid double-barreled content
2. **Construct correspondence** (Section A): Item content directly reflects construct definition boundaries
3. **Distinctiveness** (Section A): Item clearly about target construct, not neighboring constructs
4. **Reading level control** (Section B): Target 6th-8th grade general, 5th-6th clinical, 10th-12th specialized
5. **Semantic diversity** (Section B): Vary wording across items while maintaining construct meaning; avoid redundancy
6. **Concrete language** (Section B): Short, simple, concrete sentences; avoid abstract inference-heavy phrasing
7. **Temporal clarity** (Section B): Anchor vague quantifiers ("often") with clear time windows or avoid them
8. **Positive keying only** (Section C): No reverse-scored items; eliminates acquiescence bias and linguistic complexity
9. **Cultural neutrality** (Section D): Avoid idioms, culture-specific references, socioeconomic assumptions
10. **Accessibility** (Section D): No assumptions about work arrangement, family structure, citizenship, resources

**Chain-of-thought requirement (AGT-01):**
```markdown
## Rationale Requirements

Each item rationale must explain:
1. **Facet targeting:** Which facet of the construct this item measures and why
2. **Wording choices:** How language reduces ambiguity (concrete vs abstract, temporal clarity)
3. **Distinctiveness:** Why this item measures target construct and not neighbors
4. **Bias pre-check:** How item avoids cultural/socioeconomic assumptions

Keep rationales technical and concise (2-4 sentences).
```

**Semantic diversity example (AGT-02):**
```markdown
## Semantic Diversity (avoid over-paraphrasing)

❌ BAD (redundant set):
- "I feel confident in my abilities"
- "I am confident in my capabilities"
- "I have confidence in my skills"

✓ GOOD (diverse facets):
- "I feel confident in my abilities" (self-efficacy)
- "I handle setbacks without losing confidence" (resilience)
- "I speak up even when my ideas differ" (assertiveness)

Vary wording while targeting different facets. Avoid near-synonyms that measure the same aspect.
```

**Reading level guidelines (AGT-03):**
```markdown
## Reading Level Targets

Use as agent judgment guidelines (no automated measurement):

- **General population:** 6th-8th grade
  - Avg sentence length: 15-20 words
  - Avg syllables per word: ≤2
  - Example: "I feel comfortable sharing my ideas with my team"

- **Clinical population:** 5th-6th grade
  - Avg sentence length: 12-15 words
  - Avoid medical jargon
  - Example: "I worry about things that might go wrong"

- **Specialized/professional:** 10th-12th grade
  - Avg sentence length: 20-25 words
  - Domain terminology acceptable
  - Example: "I proactively identify strategic opportunities that align with organizational priorities"

Apply guidelines during drafting. Prioritize clarity over rigid adherence.
```

### Bias Reviewer Enhancement (AGT-07, AGT-08)

**7 bias types taxonomy (from Standards 2014 + van de Vijver framework):**

1. **Construct bias:** Item assumes culture-bound meaning of construct; relies on norms varying across groups
2. **Linguistic bias:** Idioms, phrases, or words with differential familiarity across language/cultural groups
3. **Cultural reference bias:** Assumes knowledge of culture-specific practices, values, or contexts
4. **Socioeconomic bias:** Assumes resources, opportunities, or experiences not shared by all (transport, housing, family resources)
5. **Context access bias:** Assumes specific work arrangement (onsite vs remote), role level (manager vs IC), shift work
6. **Protected attribute bias:** References or stereotypes related to gender, race, ethnicity, religion, citizenship, disability
7. **Intersectional bias:** Combined identity effects where multiple protected attributes interact (e.g., race × gender × age)

**Multi-pass review recommendation (AGT-08):**

Research finding: Intersectional DIF analysis detects 4-8x more bias than single-dimension approaches (Russell & Kaplan 2021).

**Implementation approach:**
```markdown
## Bias Review Process

Perform 8 evaluation passes (7 types + 1 intersectional):

Pass 1: Construct bias check
- Does item assume construct meaning varies by culture?
- Flag items relying on culture-specific norms

Pass 2: Linguistic bias check
- Identify idioms, phrases with differential familiarity
- Flag complex vocabulary or culture-specific language

Pass 3: Cultural reference bias check
- Identify assumptions about practices, values, contexts
- Flag items requiring specific cultural knowledge

Pass 4: Socioeconomic bias check
- Identify resource/opportunity assumptions
- Flag items disadvantaging low SES respondents

Pass 5: Context access bias check
- Identify work arrangement/role assumptions
- Flag items requiring specific contexts

Pass 6: Protected attribute bias check
- Identify stereotypes or sensitive disclosures
- Flag items referencing protected attributes

Pass 7: Intersectional bias check
- Examine combined identity effects
- Flag items with compounding bias for multiple identities
- Example: "As a working mother balancing career and childcare"
  (intersectional: gender × parental status × work arrangement)

Pass 8: Aggregate and prioritize
- Identify items flagged in multiple passes
- Prioritize items with intersectional flags (severity +1)

Output format remains ReviewComment with severity 1-5.
Intersectional flags automatically receive severity ≥4 (major).
```

**Alternative: Single comprehensive pass**

If multi-pass proves too computationally expensive, use single pass with structured checklist:

```markdown
For each item, evaluate all 7 bias types:
1. [✓/✗] Construct bias: [brief note]
2. [✓/✗] Linguistic bias: [brief note]
3. [✓/✗] Cultural reference bias: [brief note]
4. [✓/✗] Socioeconomic bias: [brief note]
5. [✓/✗] Context access bias: [brief note]
6. [✓/✗] Protected attribute bias: [brief note]
7. [✓/✗] Intersectional bias: [brief note]

If ≥1 type flagged: generate ReviewComment with highest severity.
```

**Recommendation:** Start with single comprehensive pass (simpler, faster). Consider multi-pass if evaluation shows missed intersectional bias.

### Content Reviewer Enhancement (AGT-05)

**Current approach:** Simulates 5 naive judges rating correspondence (1-7) and distinctiveness (1-7).

**Research-backed enhancements:**

1. **Explicit construct definition anchoring:**
```markdown
Before rating, extract 3-5 key elements from construct definition:
- Element 1: [specific aspect]
- Element 2: [specific aspect]
- Element 3: [specific aspect]

For each item, check: Does item content directly reflect ≥1 key element?
If no: correspondence ≤3
If yes but vague: correspondence 4-5
If yes and clear: correspondence 6-7
```

2. **Competitor construct specification:**
```markdown
If construct_exclusions provided: use as competitor set
Otherwise: infer close neighbors from construct definition

For each item, ask: Could this plausibly measure [competitor]?
If strong competitor match: distinctiveness ≤4
If possible but unlikely: distinctiveness 5-6
If clearly target only: distinctiveness 7
```

3. **Facet coverage tracking:**
```markdown
Maintain running count of facets covered:
- Facet A: Items 1, 4, 7 (3 items)
- Facet B: Items 2, 5 (2 items)
- Facet C: Items 3, 6, 8, 9, 10 (5 items)

Flag medium issue if imbalance >2:1 ratio and facet is undercovered.
```

### Linguistic Reviewer Enhancement (AGT-06)

**Vague quantifier rules (research-backed):**

```markdown
## Vague Quantifier Detection

Category 1: Requires time anchoring
- "often", "sometimes", "rarely", "usually", "frequently"
- Fix: Add time window ("in the past month, I often...")
- Or: Remove quantifier ("I feel...")

Category 2: Avoid entirely
- "never", "always" (extreme absolutes)
- "many", "most", "few" (vague magnitude without referent)

Category 3: Context-dependent (may be acceptable)
- "typically", "generally" (acceptable if construct inherently dispositional)
- Example acceptable: "I typically approach conflicts calmly"
- Example problematic: "I typically work from the office" (context-specific)

Scoring:
- Mean rating <4.0 if vague quantifier without time anchor
- Mean rating ≥4.0 if quantifier inherently dispositional
```

**Additional clarity checks (preserve existing):**
- Ambiguous referents ("they", "it")
- Double-barreled structure
- Negative stems or double negatives
- Overly abstract terms forcing inference
- Unnecessary parentheticals

### Meta Editor Enhancement (AGT-09)

**Facet balancing guidance:**

```markdown
## Facet Coverage Enforcement

Before revising:
1. Infer primary facets from construct definition (typically 3-5 facets)
2. Map each current item to facet
3. Calculate facet distribution

Balancing rule:
- Target: Each facet covered by ≥20% of items
- Acceptable: Max 2:1 ratio between most/least covered facets
- Violation: >3:1 ratio or facet with <10% coverage

When replacing items:
- Prioritize undercovered facets
- Avoid collapsing all items onto same facet
- Maintain response scale consistency (no mixing frequency/agreement)

Include in revision_plan.summary:
"Facet balance: [facet A: X items, facet B: Y items, facet C: Z items]"
```

### Critic Enhancement (AGT-10)

**Adaptive iteration thresholds (research-backed from multi-agent routing):**

Current rule-based logic:
```python
# Step 2: Blockers (always revise)
if any(severity == 5): return "revise"
if any(bias_severity >= 4): return "revise"
if any(content_severity >= 4): return "revise"

# Step 3: Convergence
if max_severity > critic_max_severity_to_accept: return "revise"
if medium_plus_count >= 2: return "revise"
else: return "accept"
```

**Enhanced severity-based routing (AGT-10):**

```markdown
## Adaptive Thresholds by Iteration

Dynamic threshold adjustment based on iteration progress:

Early iterations (1-2):
- Stricter thresholds to catch major issues early
- Bias blocker: severity ≥4
- Content blocker: severity ≥4
- Accept threshold: max_severity ≤2

Mid iterations (3-4):
- Standard thresholds (current behavior)
- Bias blocker: severity ≥4
- Content blocker: severity ≥4
- Accept threshold: max_severity ≤critic_max_severity_to_accept

Late iterations (5+):
- Relaxed thresholds to prevent infinite loops
- Bias blocker: severity == 5 only
- Content blocker: severity == 5 only
- Accept threshold: max_severity ≤critic_max_severity_to_accept + 1

Reason string includes: "Iteration {N}/{max}: threshold mode {early|mid|late}"
```

**Priority-based routing (optional enhancement):**

If implementing request priority field:
```python
if request.priority == "high":
    # More aggressive acceptance to meet time constraints
    accept_threshold += 1

if request.priority == "research":
    # Stricter standards for research instruments
    accept_threshold -= 1
```

**Recommendation:** Implement adaptive thresholds by iteration. Defer priority-based routing until user feedback indicates need.

### Web Surfer Enhancement

**No changes recommended.** Current prompt effectively retrieves evidence and avoids copying items verbatim. Focus optimization efforts on Item Writer and Bias Reviewer per user guidance.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reverse-scored items for acquiescence control | Custom logic to generate negatively-keyed items | Positive keying only with semantic diversity | Recent research shows reverse items introduce linguistic complexity, cognitive load, and inconsistent acquiescence control. Semantic diversity achieves construct coverage without negation complications. |
| Automated Flesch-Kincaid scoring in validation | Custom readability scoring node | Agent judgment with guidelines | F-K formulas are approximations; agent judgment better handles domain terminology and construct-specific language. Guidelines in prompts achieve target without rigid automation. |
| Custom semantic similarity for redundancy detection | Embedding-based clustering | LLM-based facet mapping | CPIG research shows LLM judgment with constraint satisfaction (maximize originality, minimize similarity) outperforms pure embedding approaches. Simpler to implement in existing agent workflow. |
| Multi-model LLM ensemble for validation | Router selecting from 5+ models | Opus for validation, Sonnet for other agents | Smart model allocation pattern (Phase 1 decision) already implemented. Ensemble adds cost/complexity without proportional accuracy gains. |
| Custom DIF statistical analysis | IRT-based DIF detection | Multi-pass qualitative bias review | Statistical DIF requires empirical response data (Phase 6 scope). Current phase focuses on bias prevention during generation, not post-hoc detection. |
| Agent consolidation experimentation framework | A/B testing infrastructure for 7→6 agent comparison | Manual comparison on test constructs | AGT-11 is optional. If pursued, simple comparison on 3-5 test constructs (run both architectures, compare output quality) sufficient for decision. Avoid premature optimization infrastructure. |

**Key insight:** LLM-based agents with well-engineered prompts handle item quality, bias detection, and facet balancing more effectively than custom rule-based or statistical approaches at this stage. Defer empirical validation methods (DIF, factor analysis) to Phase 6 when response data exists.

## Common Pitfalls

### Pitfall 1: Over-Paraphrasing (Item Redundancy)

**What goes wrong:** Item Writer generates semantically identical items with minor wording variations, reducing construct coverage.

**Why it happens:** LLMs excel at paraphrasing; without explicit diversity guidance, agents default to synonym substitution rather than facet variation.

**How to avoid:**
- Add semantic diversity section to Item Writer prompt with examples
- Require rationale to specify which facet each item targets
- Meta Editor checks facet distribution and flags >3:1 imbalances

**Warning signs:**
- High inter-item correlations in evaluation data (Phase 6)
- Expert reviewers note items "all sound the same"
- Content Reviewer flags low distinctiveness but can't identify competitor construct

### Pitfall 2: Acquiescence Bias from Reverse Items

**What goes wrong:** Reverse-keyed items intended to control acquiescence actually introduce measurement error from linguistic complexity and respondent confusion.

**Why it happens:** Traditional psychometric guidance recommends balanced keying; however, recent 2025 research shows reverse items create "cognitive speedbumps" that inconsistently affect different respondents.

**How to avoid:**
- Explicitly prohibit reverse-keyed items in Item Writer prompt (Section C)
- Use positive keying only
- Achieve construct breadth through facet diversity, not item reversal

**Warning signs:**
- Lower reliability for reverse-keyed items
- Reverse items load on separate factor (method effect)
- Respondent confusion or data quality issues on negated items

### Pitfall 3: Vague Quantifiers Without Temporal Anchoring

**What goes wrong:** Items use frequency terms ("often", "sometimes") without time windows, causing differential interpretation across respondents.

**Why it happens:** Natural language includes many frequency terms; agents default to human-like phrasing patterns.

**How to avoid:**
- Linguistic Reviewer detects vague quantifiers and enforces time anchoring rules
- Item Writer guidelines specify acceptable quantifier use
- Prefer concrete temporal frames ("in the past week") or dispositional phrasing ("I am someone who...")

**Warning signs:**
- High response variability on items with vague quantifiers
- Lower test-retest reliability for frequency items
- Respondent questions about "how often is often?"

### Pitfall 4: Single-Pass Bias Review Misses Intersectional Effects

**What goes wrong:** Bias Reviewer evaluates items holistically, missing compounded bias from multiple identity categories.

**Why it happens:** Cognitive load from simultaneous evaluation of 7+ bias dimensions; intersectional effects are subtle and require dedicated attention.

**How to avoid:**
- Implement multi-pass bias review (separate evaluation per bias type)
- Explicitly prompt for intersectional bias detection in final pass
- Flag items with ≥2 bias types automatically for closer review

**Warning signs:**
- Items flagged by diverse respondent panels but not by agent
- Higher DIF statistics in empirical testing (Phase 6) than agent predicted
- Community feedback identifies missed bias patterns

### Pitfall 5: Adaptive Threshold Failure (Infinite Loops or Premature Acceptance)

**What goes wrong:** Fixed acceptance thresholds cause either infinite revision loops (threshold too strict) or premature acceptance of flawed items (threshold too loose).

**Why it happens:** Optimal threshold varies by construct complexity, iteration progress, and item quality trajectory.

**How to avoid:**
- Implement adaptive thresholds by iteration (stricter early, relaxed late)
- Max iteration limit prevents infinite loops
- Critic rationale includes threshold mode for transparency

**Warning signs:**
- Workflow frequently hits max iterations without convergence
- Accepted items still have medium-severity issues
- User feedback indicates quality inconsistency across runs

### Pitfall 6: Construct Drift from Over-Revision

**What goes wrong:** After multiple revision cycles, items shift away from original construct definition toward generic phrasing.

**Why it happens:** Cumulative effect of conservative edits removing specificity to address bias/clarity concerns.

**How to avoid:**
- Meta Editor explicitly checks revised items against construct definition
- Content Reviewer rechecks correspondence after each revision
- Validation agent (Phase 1) provides construct correspondence gate

**Warning signs:**
- Correspondence scores decrease across iterations
- Items become increasingly generic/vague
- Expert reviewers note "these could measure anything"

## Code Examples

Verified patterns from research and project context:

### Semantic Diversity in Item Generation

```python
# Source: Keane & McNaughton 2026 (Generative AI Scale Development)
# Pattern: Use facet-based generation with explicit diversity constraint

# In Item Writer prompt (add to Section A):
"""
Facet-Based Generation Strategy:

1. Identify 3-5 facets from construct definition
2. Generate items across facets with this distribution:
   - If item_count ≤ 10: At least 2 items per facet
   - If item_count > 10: At least 20% of items per facet

3. Within-facet diversity:
   - Vary sentence structure (simple declarative, compound)
   - Vary perspective (self-focused, situation-focused)
   - Vary temporal frame (present state, typical behavior)

4. Avoid near-synonyms:
   ❌ "confident" → "self-assured" → "believing in myself"
   ✓ "confident" (self-efficacy) → "voice opinions" (assertiveness) → "handle setbacks" (resilience)

5. Rationale must specify facet and explain how item differs from others in same facet.
"""
```

### Multi-Pass Bias Review Implementation

```python
# Source: Russell & Kaplan 2021 (Intersectional DIF)
# Pattern: Sequential evaluation with intersectional synthesis

# Option A: Multiple LLM calls (most thorough)
async def review_bias_multipass(items, construct_definition):
    """Execute 7 bias type passes + 1 intersectional pass."""

    bias_types = [
        "construct_bias",
        "linguistic_bias",
        "cultural_reference_bias",
        "socioeconomic_bias",
        "context_access_bias",
        "protected_attribute_bias"
    ]

    # Pass 1-6: Individual bias types
    type_results = {}
    for bias_type in bias_types:
        prompt = f"""
        Review items for {bias_type} only.

        Definition: {BIAS_DEFINITIONS[bias_type]}

        For each item, evaluate: Does this item exhibit {bias_type}?
        If yes: severity 1-5 and suggested edit
        If no: skip item
        """
        type_results[bias_type] = await llm_call(prompt, items)

    # Pass 7: Intersectional synthesis
    items_with_multiple_flags = [
        item for item in items
        if sum(item in results for results in type_results.values()) >= 2
    ]

    intersectional_prompt = f"""
    These items flagged in ≥2 bias types: {items_with_multiple_flags}

    Evaluate intersectional bias: Do multiple bias types compound for certain identities?
    Example: Item assumes office work (context access) AND white-collar role (socioeconomic)
    → Compounds for blue-collar, remote, or shift workers

    Flag items with intersectional effects. Severity automatically ≥4 (major).
    """
    intersectional_results = await llm_call(intersectional_prompt, items_with_multiple_flags)

    # Merge results
    return merge_bias_comments(type_results, intersectional_results)


# Option B: Single call with structured checklist (more efficient)
async def review_bias_singlepass(items, construct_definition):
    """Single LLM call with 7-part structured evaluation."""

    prompt = """
    For each item, evaluate all 7 bias types using this checklist:

    1. Construct bias: [✓/✗] [note if flagged]
    2. Linguistic bias: [✓/✗] [note if flagged]
    3. Cultural reference bias: [✓/✗] [note if flagged]
    4. Socioeconomic bias: [✓/✗] [note if flagged]
    5. Context access bias: [✓/✗] [note if flagged]
    6. Protected attribute bias: [✓/✗] [note if flagged]
    7. Intersectional bias: [✓/✗] [note if flagged]

    Intersectional check: If ≥2 types flagged, examine combined effect.

    Generate ReviewComment only if ≥1 type flagged:
    - Severity = highest individual type severity
    - If intersectional: severity automatically ≥4
    - Issue = describe bias type(s) and intersectional effect if any
    - Suggested_edit = rewritten item addressing all flagged types
    """

    return await llm_call(prompt, items)
```

### Adaptive Threshold Routing in Critic

```python
# Source: Adaptive Routing Protocols (arXiv 2025)
# Pattern: Dynamic threshold adjustment by iteration and priority

def get_adaptive_thresholds(iteration: int, max_iterations: int, priority: str = "normal"):
    """Calculate thresholds based on iteration progress."""

    # Iteration-based threshold progression
    if iteration <= 2:
        mode = "early"
        bias_blocker_threshold = 4
        content_blocker_threshold = 4
        accept_max_severity = 2
        accept_medium_plus_count = 0

    elif iteration <= 4:
        mode = "mid"
        bias_blocker_threshold = 4
        content_blocker_threshold = 4
        accept_max_severity = 3  # critic_max_severity_to_accept default
        accept_medium_plus_count = 2

    else:  # iteration >= 5
        mode = "late"
        bias_blocker_threshold = 5  # Only critical issues
        content_blocker_threshold = 5
        accept_max_severity = 4  # More lenient
        accept_medium_plus_count = 3

    # Priority-based adjustment (optional)
    if priority == "high":
        accept_max_severity += 1  # More lenient for time-sensitive
    elif priority == "research":
        accept_max_severity -= 1  # Stricter for research instruments

    return {
        "mode": mode,
        "bias_blocker_threshold": bias_blocker_threshold,
        "content_blocker_threshold": content_blocker_threshold,
        "accept_max_severity": accept_max_severity,
        "accept_medium_plus_count": accept_medium_plus_count
    }


def make_critic_decision(iteration, max_iterations, comments):
    """Enhanced critic with adaptive thresholds."""

    # Step 1: Check iteration limit
    if iteration >= max_iterations:
        return {
            "decision": "stop_max_iterations",
            "reason": f"Reached max_iterations ({max_iterations}); unresolved issues may remain."
        }

    # Get adaptive thresholds
    thresholds = get_adaptive_thresholds(iteration, max_iterations)

    # Step 2: Check blockers (iteration-adaptive)
    bias_comments = [c for c in comments if c.type == "bias"]
    content_comments = [c for c in comments if c.type == "content"]

    if any(c.severity == 5 for c in comments):
        return {
            "decision": "revise",
            "reason": f"Critical issues present. Iteration {iteration}/{max_iterations}: threshold mode {thresholds['mode']}"
        }

    if any(c.severity >= thresholds["bias_blocker_threshold"] for c in bias_comments):
        return {
            "decision": "revise",
            "reason": f"Bias issues ≥{thresholds['bias_blocker_threshold']}. Iteration {iteration}/{max_iterations}: threshold mode {thresholds['mode']}"
        }

    if any(c.severity >= thresholds["content_blocker_threshold"] for c in content_comments):
        return {
            "decision": "revise",
            "reason": f"Content issues ≥{thresholds['content_blocker_threshold']}. Iteration {iteration}/{max_iterations}: threshold mode {thresholds['mode']}"
        }

    # Step 3: Convergence check (iteration-adaptive)
    max_severity = max((c.severity for c in comments), default=0)
    medium_plus_count = sum(1 for c in comments if c.severity >= 3)

    if max_severity > thresholds["accept_max_severity"]:
        return {
            "decision": "revise",
            "reason": f"max_severity={max_severity} > threshold={thresholds['accept_max_severity']}, medium_plus_count={medium_plus_count}. Iteration {iteration}/{max_iterations}: threshold mode {thresholds['mode']}"
        }

    if medium_plus_count >= thresholds["accept_medium_plus_count"]:
        return {
            "decision": "revise",
            "reason": f"medium_plus_count={medium_plus_count} ≥ threshold={thresholds['accept_medium_plus_count']}, max_severity={max_severity}. Iteration {iteration}/{max_iterations}: threshold mode {thresholds['mode']}"
        }

    # Accept
    return {
        "decision": "accept",
        "reason": f"All issues minor (max_severity={max_severity}, medium_plus_count={medium_plus_count}). Iteration {iteration}/{max_iterations}: threshold mode {thresholds['mode']}"
    }
```

### Time Anchoring for Vague Quantifiers

```python
# Source: Item writing guidelines research
# Pattern: Detection and repair rules for linguistic reviewer

# In Linguistic Reviewer prompt:
"""
Vague Quantifier Detection and Repair:

CATEGORY 1: Requires time anchoring
Quantifiers: "often", "sometimes", "rarely", "usually", "frequently", "occasionally"

Detection: Item contains frequency term without temporal frame
Fix: Add time window OR remove quantifier

Examples:
❌ "I often feel stressed"
✓ "In the past month, I often felt stressed"
✓ "I feel stressed" (quantifier removed, item now about presence not frequency)

CATEGORY 2: Avoid entirely
Quantifiers: "never", "always", "all the time", "constantly"

Detection: Item contains absolute frequency term
Fix: Replace with bounded frequency or remove

Examples:
❌ "I always double-check my work"
✓ "I typically double-check my work"
✓ "I double-check my work" (dispositional statement)

CATEGORY 3: Context-dependent (evaluate case-by-case)
Quantifiers: "typically", "generally", "usually"

Acceptable: Dispositional constructs (personality traits)
✓ "I typically approach conflicts calmly" (trait agreeableness)

Problematic: Situation-specific constructs
❌ "I typically work from the office" (depends on job/policy)

Scoring rule:
- Mean rating <4.0 if Category 1 without time anchor OR Category 2 present
- Mean rating <4.0 if Category 3 used in situation-specific item
- Mean rating ≥4.0 if appropriately anchored or dispositional
"""
```

### Facet Balancing in Meta Editor

```python
# Source: Facet-based scale development best practices
# Pattern: Track and enforce facet distribution

# In Meta Editor prompt:
"""
Facet Coverage Enforcement:

Step 1: Infer facets from construct definition
Example: "Psychological safety: feeling able to take interpersonal risks without fear of negative consequences"
→ Facets:
  A) Willingness to take risks (behavioral)
  B) Absence of fear (affective)
  C) Interpersonal context (situational)

Step 2: Map current items to facets
Item 1: "I feel comfortable sharing unconventional ideas" → Facet A+B
Item 2: "I don't worry about being judged by my team" → Facet B
Item 3: "My team welcomes different perspectives" → Facet C
...

Step 3: Calculate distribution
Facet A: 4 items (40%)
Facet B: 5 items (50%)
Facet C: 1 item (10%)  ← UNDERCOVERED

Step 4: Apply balancing rules
Target: Each facet ≥20% of items
Maximum acceptable imbalance: 2:1 ratio
Current status: 5:1 ratio (B:C) → VIOLATION

Step 5: Prioritize undercovered facets in revisions
When replacing items:
- Prioritize Facet C (undercovered)
- Don't replace Facet C items unless severity ≥4
- If replacing Facet B item, consider shifting to Facet C if construct-appropriate

Step 6: Report in revision_plan.summary
"Facet balance after revision: A: 4 items (40%), B: 4 items (40%), C: 2 items (20%)"
"""

# Python implementation (for validation):
def check_facet_balance(items, construct_definition):
    """Validate facet distribution meets balance requirements."""

    # Infer facets (could be LLM call or manual specification)
    facets = infer_facets(construct_definition)  # Returns ["Facet A", "Facet B", "Facet C"]

    # Map items to facets
    item_facet_map = {}
    for i, item in enumerate(items):
        primary_facet = classify_item_facet(item, facets)
        item_facet_map[i] = primary_facet

    # Calculate distribution
    facet_counts = Counter(item_facet_map.values())
    total_items = len(items)
    facet_percentages = {f: (count/total_items)*100 for f, count in facet_counts.items()}

    # Check balance
    min_pct = min(facet_percentages.values())
    max_pct = max(facet_percentages.values())
    imbalance_ratio = max_pct / min_pct if min_pct > 0 else float('inf')

    issues = []

    # Target: Each facet ≥20%
    for facet, pct in facet_percentages.items():
        if pct < 20:
            issues.append(f"{facet} undercovered: {pct:.1f}% (target ≥20%)")

    # Maximum acceptable imbalance: 2:1
    if imbalance_ratio > 2.0:
        issues.append(f"Imbalance ratio {imbalance_ratio:.1f}:1 exceeds maximum 2:1")

    return {
        "balanced": len(issues) == 0,
        "facet_distribution": facet_percentages,
        "imbalance_ratio": imbalance_ratio,
        "issues": issues
    }
```

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None — using default pytest discovery |
| Quick run command | `pytest tests/test_validator.py tests/test_schemas.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGT-01 | Item Writer prompt includes 10 psychometric principles | unit | `pytest tests/test_prompts.py::test_item_writer_10_principles -x` | ❌ Wave 0 |
| AGT-02 | Item Writer prompt includes semantic diversity examples | unit | `pytest tests/test_prompts.py::test_item_writer_semantic_diversity -x` | ❌ Wave 0 |
| AGT-03 | Item Writer prompt specifies reading level targets | unit | `pytest tests/test_prompts.py::test_item_writer_reading_levels -x` | ❌ Wave 0 |
| AGT-04 | Item Writer prompt prohibits reverse-keyed items | unit | `pytest tests/test_prompts.py::test_item_writer_positive_keying -x` | ❌ Wave 0 |
| AGT-05 | Content Reviewer prompt includes correspondence criteria | unit | `pytest tests/test_prompts.py::test_content_reviewer_criteria -x` | ❌ Wave 0 |
| AGT-06 | Linguistic Reviewer prompt includes vague quantifier rules | unit | `pytest tests/test_prompts.py::test_linguistic_reviewer_quantifiers -x` | ❌ Wave 0 |
| AGT-07 | Bias Reviewer prompt defines 7 bias types | unit | `pytest tests/test_prompts.py::test_bias_reviewer_7_types -x` | ❌ Wave 0 |
| AGT-08 | Bias Reviewer implements multi-pass or structured checklist | integration | `pytest tests/test_bias_reviewer.py::test_multipass_detection -x` | ❌ Wave 0 |
| AGT-09 | Meta Editor prompt includes facet balancing rules | unit | `pytest tests/test_prompts.py::test_meta_editor_facet_balance -x` | ❌ Wave 0 |
| AGT-10 | Critic implements adaptive thresholds by iteration | unit | `pytest tests/test_critic.py::test_adaptive_thresholds -x` | ❌ Wave 0 |
| AGT-11 | Optional: 6-agent architecture comparison | manual-only | Manual comparison on 3-5 test constructs | N/A (optional) |

### Sampling Rate

- **Per task commit:** `pytest tests/test_prompts.py -x` (prompt content validation)
- **Per wave merge:** `pytest tests/ -v --ignore=tests/test_smoke.py` (all unit + integration except smoke)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_prompts.py` — covers AGT-01 through AGT-07, AGT-09 (prompt content validation)
- [ ] `tests/test_critic.py::test_adaptive_thresholds` — covers AGT-10 (critic logic validation)
- [ ] `tests/test_bias_reviewer.py::test_multipass_detection` — covers AGT-08 (multi-pass integration test)

*All tests verify prompt content or agent logic without requiring LLM calls (use mock responses or prompt file validation).*

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Reverse-keyed items for acquiescence control | Positive keying only with facet diversity | 2025 (Frontiers Psychology) | Eliminates linguistic complexity and measurement error from negation; achieves construct breadth through facet targeting |
| Single-dimension DIF analysis | Intersectional DIF for combined identity categories | 2021 (Russell & Kaplan) | Detects 4-8x more bias by examining compounded effects of multiple protected attributes |
| Manual item writing with slow iteration | LLM-assisted generation with automated quality checks | 2024-2026 (CPIG, Keane) | LLM items achieve human-equivalent validity; dramatically faster iteration; broader semantic diversity |
| Fixed acceptance thresholds in review workflows | Adaptive thresholds by iteration and priority | 2025 (Multi-agent routing) | Prevents infinite loops and premature acceptance; balances quality and convergence |
| Embedding-based semantic similarity | LLM-based facet mapping and constraint satisfaction | 2024 (CPIG) | Better handles domain-specific language; simpler integration with existing agent workflow |
| Global configuration only | Multi-scope configuration (global, project, local) | Ongoing | Enables team standards while allowing project-specific overrides |

**Deprecated/outdated:**
- **Reverse-keyed items:** Traditional guidance recommended balanced keying (50% positive, 50% reverse); current evidence shows reverse items introduce more problems than they solve
- **Rigid Flesch-Kincaid enforcement:** Automated scoring doesn't account for construct-appropriate terminology; agent judgment with guidelines more effective
- **Single-pass bias review:** Misses intersectional effects; multi-pass or structured checklist approach now preferred
- **Static acceptance thresholds:** Can cause workflow failures (infinite loops or premature acceptance); adaptive approaches now standard in multi-agent systems

## Open Questions

### 1. Multi-Pass vs. Single-Pass Bias Review (AGT-08)

**What we know:**
- Multi-pass: 8 separate LLM calls (7 bias types + 1 intersectional synthesis)
- Single-pass: 1 LLM call with structured 7-part checklist
- Research shows intersectional approach detects 4-8x more bias

**What's unclear:**
- Cost/latency tradeoff: Does 8x API calls provide >8x value?
- Do LLMs effectively simulate multi-pass evaluation in single call?
- Is intersectional bias detection quality-equivalent between approaches?

**Recommendation:**
- **Start with single-pass** (simpler, faster, lower cost)
- Implement structured checklist with explicit intersectional bias section
- Monitor output quality: Do items flagged by diverse users match agent predictions?
- **If evaluation shows missed intersectional bias:** Switch to multi-pass in Wave 2
- **If single-pass performs well:** Retain simpler approach and document in decision log

### 2. Agent Consolidation (AGT-11 Optional)

**What we know:**
- Current: 7 agents (Item Writer, Content Reviewer, Linguistic Reviewer, Bias Reviewer, Meta Editor, Critic, Web Surfer)
- Proposed: 6 agents (merge Content + Bias Reviewer into single "Quality Reviewer")
- Rationale: Content and Bias both evaluate item quality; consolidation could reduce latency

**What's unclear:**
- Would consolidated agent maintain separation of concerns?
- Would prompt become too complex (cognitive load)?
- What's the actual latency/cost impact of parallel execution?

**Recommendation:**
- **Defer unless Phase 3 evaluation shows latency problems**
- Current parallel execution (ThreadPoolExecutor) means Content + Bias run simultaneously
- Consolidation saves 1 LLM call but complicates prompt engineering
- **If pursued:** Manual comparison on 3-5 test constructs
  - Run both architectures
  - Compare output quality (do they catch same issues?)
  - Compare latency and cost
  - User experience assessment (is consolidated output clear?)
- **Avoid:** Premature optimization infrastructure for A/B testing

### 3. Chain-of-Thought Effectiveness for Agents Beyond Item Writer/Bias Reviewer

**What we know:**
- CoT reduces hallucination and improves complex reasoning
- Recent 2025 research shows diminishing returns for non-reasoning tasks
- User decision: Required for Item Writer and Bias Reviewer, optional for others

**What's unclear:**
- Would CoT improve Content Reviewer's correspondence/distinctiveness ratings?
- Would CoT help Meta Editor with facet balancing decisions?
- Cost/latency impact across all agents?

**Recommendation:**
- **Honor user decision:** CoT only for Item Writer and Bias Reviewer (Wave 0)
- **Monitor:** Do other agents produce inconsistent or low-quality outputs?
- **If quality issues emerge:** Add CoT to specific agents in targeted waves
- **Avoid:** Blanket application without evidence of benefit

### 4. Facet Inference: Manual Specification vs. LLM-Based

**What we know:**
- Meta Editor needs facet structure for balancing
- Could be: (A) LLM infers from construct definition, or (B) User specifies in request

**What's unclear:**
- Accuracy: Can LLM reliably infer facets from definition alone?
- User burden: Would facet specification add complexity?
- Validation: How to verify facet inference quality?

**Recommendation:**
- **Wave 0:** LLM infers facets from construct definition
  - Simpler user experience (no additional input required)
  - Meta Editor reports inferred facets in revision_plan.summary for transparency
- **Monitor:** Do inferred facets align with expert understanding?
- **If misalignment detected:** Add optional `facets` field to UserRequest schema (Phase 4 enhancement)

## Sources

### Primary (HIGH confidence)

- [AERA/APA/NCME Standards for Educational and Psychological Testing (2014)](https://www.testingstandards.net/uploads/7/6/6/4/76643089/standards_2014edition.pdf) - Fairness, validity, bias definitions
- [Standards for Educational & Psychological Testing (2014 Edition) - AERA](https://www.aera.net/publications/books/standards-for-educational-psychological-testing-2014-edition) - Official publication page
- [The creative psychometric item generator (CPIG) - arXiv 2024](https://arxiv.org/html/2409.00202v1) - LLM-based item generation framework with validation
- [An Intersectional Approach to Differential Item Functioning - Russell & Kaplan 2021](https://openpublishing.library.umass.edu/pare/article/1570/galley/1521/download/) - Intersectional DIF methodology

### Secondary (MEDIUM confidence)

- [Using Generative AI to Enhance Psychometric Scale Development - Keane & McNaughton 2026](https://journals.sagepub.com/doi/10.1177/14707853251384769) - AI-assisted scale development with semantic diversity
- [Advancing the psychometrics of reverse-keyed items - Frontiers Psychology 2025](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1684612/full) - Linguistic issues with reverse items
- [Adaptive routing protocols for AI multi-agent systems - arXiv 2025](https://arxiv.org/abs/2503.07686) - Priority and learning-enhanced routing
- [Best Practices for Developing and Validating Scales - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/) - Scale development procedures
- [Unidimensionality in Psychometrics - Cogn-IQ](https://www.cogn-iq.org/learn/theory/unidimensionality/) - Unidimensionality definition and assessment
- [Differential Item Functioning - Cogn-IQ](https://www.cogn-iq.org/learn/theory/differential-item-functioning/) - DIF overview and methods
- [Current Concepts in Validity and Reliability - 2025 Review](https://educationaldevelopment.uams.edu/wp-content/uploads/sites/57/2025/01/1-Current-Concepts-in-Validity-and-Reliability-for-Psychometric-Instruments.pdf) - Construct validity framework
- [The Ultimate Guide to Prompt Engineering in 2026 - Lakera](https://www.lakera.ai/blog/prompt-engineering-guide) - Structured outputs and validation
- [Agents At Work: 2026 Playbook - Prompt Engineering](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/) - Agentic workflow patterns
- [Most quantifiers have many meanings - Psychonomic Bulletin 2024](https://link.springer.com/article/10.3758/s13423-024-02502-7) - Vague quantifier interpretation
- [Rethinking psychometrics through LLMs - Scientific Reports 2025](https://www.nature.com/articles/s41598-025-21289-8) - Item semantics in LLM-based assessment
- [ITC Guidelines - International Test Commission](https://www.intestcom.org/) - International test development guidelines
- [Flesch-Kincaid Readability - Readable](https://readable.com/readability/flesch-reading-ease-flesch-kincaid-grade-level/) - Readability formula overview
- [Variation in Readability of Survey Items - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1693909/) - Within-survey readability variation
- [Psychometric Theory - Nunnally & Bernstein 1994](https://books.google.com/books/about/Psychometric_Theory.html?id=r0fuAAAAMAAJ) - Foundational psychometric text

### Tertiary (LOW confidence - marked for validation)

- [Double-Barreled Questions Guide - Lensym](https://lensym.com/blog/double-barreled-questions-guide) - Item writing best practices (non-peer-reviewed)
- [Chain-of-Thought Prompting Overview - SuperAnnotate](https://www.superannotate.com/blog/chain-of-thought-cot-prompting) - CoT tutorial (not research)
- [LLM Agents - Prompt Engineering Guide](https://www.promptingguide.ai/research/llm-agents) - Agent patterns overview
- [State of Agent Engineering - LangChain](https://www.langchain.com/state-of-agent-engineering) - Industry survey (not academic)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - AERA/APA/NCME Standards (2014) and ITC Guidelines are authoritative sources; CPIG research is peer-reviewed
- Architecture: MEDIUM-HIGH - Prompt engineering patterns verified from multiple 2025-2026 sources; some patterns extrapolated from research to application
- Pitfalls: MEDIUM - Based on established psychometric concerns (reverse items, vague quantifiers) and recent research (intersectional DIF); application to LLM context partially inferred
- Code examples: MEDIUM - Patterns derived from research findings and adapted to project architecture; not directly tested in production

**Research date:** 2026-03-08
**Valid until:** 60 days (2026-05-07) - Psychometric standards are stable; LLM agent engineering is fast-moving but major patterns established

**Note on validation:** All prompt content changes should be validated with expert review (human psychometrician) before production deployment. LLM-generated items showing human-equivalent validity in research (CPIG 2024) provides confidence, but project-specific validation recommended in Phase 6 (Comprehensive Evaluation Framework).
