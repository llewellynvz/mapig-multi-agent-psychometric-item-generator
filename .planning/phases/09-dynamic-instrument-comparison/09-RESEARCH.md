# Phase 9: Dynamic Instrument Comparison - Research

**Researched:** 2026-03-14
**Domain:** Psychometric validity assessment with LLM-based convergent/discriminant scoring
**Confidence:** MEDIUM-HIGH

## Summary

Phase 9 implements dynamic instrument discovery from academic literature for convergent and discriminant validity assessment. The phase builds on existing Perplexity Academic integration (web_surfer.py) with instrument-specific search queries, dual-direction LLM-as-judge scoring to mitigate position bias, and cosine similarity plagiarism detection.

**Key architectural decision:** Hybrid approach with search-first strategy falling back to hardcoded defaults ensures graceful degradation when Perplexity searches fail (no credits, timeout, no results). Instruments are metadata-only (no item text storage) with publisher blocklist enforced at search time.

**Primary recommendation:** Extend existing web_surfer.py with instrument search function (don't modify surf()), use established dual-direction scoring pattern from evaluation/item_comparison.py, leverage sentence-transformers for plagiarism detection, and follow Phase 8 collapsible panel UI pattern.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Retrieve exactly 2 instruments per generation: 1 convergent (same construct) and 1 discriminant (related-but-distinct construct)
- Search-first approach: try Perplexity Academic search, fall back to hardcoded defaults if search fails (no credits, timeout, no results)
- Hardcoded defaults span broad psychological domains (personality, clinical, organizational, social, cognitive) — not just org psych
- Instruments shown in results panel only after generation completes — no intermediate SSE events for discovery
- Existing Web Surfer Perplexity integration extended with instrument-specific query synthesis
- Single collapsible card (own section below CorrelationPanel, separate from it)
- Collapsed by default, matching Phase 8 progressive disclosure pattern
- Card has two sections: convergent instrument + discriminant instrument side-by-side
- Essential metadata per instrument: name, author + year, construct measured, APA citation, one-line similarity rationale
- Convergent validity shown as numeric score (0-1) with pass/warning threshold — no narrative rationale
- No dedicated export button — comparison data included in existing full JSON export
- Discriminant instrument displayed inline in the comparison card (not a separate panel)
- Warning badge (orange pill) when estimated correlation > 0.85 with related construct: "High overlap detected (r = X.XX)"
- One-line educational explanations for convergent and discriminant validity concepts (tooltip or subtitle)
- Dual-direction scoring (A→B and B→A) averaged — show only the averaged result, individual directions are implementation detail
- All validity flags are advisory/informational only — no blocking actions, consistent with Phase 8 pattern
- Hardcoded publisher blocklist for Perplexity searches: major test publisher domains (pearson.com, parinc.com, mhs.com, wpspublish.com, etc.)
- Metadata-only storage enforced at schema level (ComparisonInstrument has no item_text field — Phase 7 schema)
- Small disclaimer footer in comparison card: "Only instrument metadata is stored. No copyrighted item text is retrieved or displayed."
- Per-item warning badges on flagged items in results table when cosine similarity > 0.85 to retrieved instrument items
- Red/orange warning pill: "Potential similarity to [Instrument] item"
- Informational only — no auto-removal, no revision suggestions, no blocking
- Consistent with Phase 8 "advisory, not blocking" philosophy for LLM-estimated metrics

### Claude's Discretion
- Perplexity Academic query construction strategy for instrument discovery
- Cosine similarity implementation approach (LLM-based or sklearn)
- Hardcoded default instrument selection (specific scales per domain)
- Comparison score threshold values for pass/warning
- Convergent/discriminant scoring prompt engineering
- Publisher blocklist extent (specific domains beyond the obvious ones)
- Card styling details, badge colors, tooltip content

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INST-01 | System dynamically searches for validated comparison instruments via Perplexity Academic based on user's construct definition | Perplexity Academic API with search_mode="academic" supports targeted scholarly search; query synthesis patterns established in web_surfer.py |
| INST-02 | System replaces hardcoded org psych nearest neighbor constructs with literature-grounded search results | Research shows IPIP and public domain scales cover personality, clinical, organizational, social, cognitive domains; hybrid search-first + fallback pattern ensures robustness |
| INST-03 | System uses hybrid approach for neighbor constructs (hardcoded defaults + literature supplements, fallback to defaults if search fails) | Perplexity search returns metadata including URLs, snippets; fallback pattern already established in web_surfer.py for evidence retrieval |
| INST-04 | System provides convergent validity evidence by comparing generated items to instruments measuring the same construct | LLM-as-judge proven effective for psychometric assessment; dual-direction scoring mitigates position bias (~40% bias in GPT-4); averaging technique validated in recent research |
| INST-05 | System enforces copyright safeguards (public-domain allowlist, publisher blocklist, metadata-only storage, never store copyrighted item text) | Publisher blocklist can be configured in settings.py; ComparisonInstrument schema (Phase 7) has no item_text field; Perplexity domain_filter supports blocklist |
| INST-06 | System detects potential plagiarism by flagging generated items with cosine similarity > 0.85 to retrieved instrument items | Sentence-transformers (all-mpnet-base-v2) with cosine similarity is standard for plagiarism detection; 0.85 threshold widely used for high similarity flagging |
| XCON-01 | System assesses discriminant validity by comparing generated items against instruments measuring related-but-distinct constructs | Same LLM-as-judge approach as convergent validity; research shows LLMs can assess discriminant validity with proper prompting |
| XCON-02 | System uses dual-direction LLM-as-judge scoring (A to B and B to A averaged) to mitigate position bias in cross-construct comparisons | Position bias mitigation via dual-direction scoring validated in recent LLM-as-judge research; averaging reduces ~40% position bias |
| XCON-03 | System provides automated validity flagging (correlation > 0.85 with related construct = discriminant validity concern) | Convergent validity threshold is 0.70 in psychology; discriminant validity typically ±0.20, but 0.85 is conservative threshold for "high overlap" warning |
| XCON-04 | System identifies related-but-distinct constructs for comparison using dynamic neighbor discovery (validated against expert-curated at > 70% agreement) | Perplexity Academic can retrieve "related constructs" via targeted queries; hardcoded defaults provide validation baseline |
| UI-02 | User can view psychometric analytics panel below results showing correlation matrix, comparison instruments, and cross-construct analysis | Phase 8 established collapsible panel pattern with CorrelationPanel; same pattern applies to comparison display |
| UI-03 | User can view comparison display card showing matched validated instruments with source citations | Radix UI Collapsible + shadcn Card pattern established; metadata fields defined in ComparisonInstrument schema |
| UI-04 | User can view cross-construct comparison table with discriminant validity assessments | CrossConstructComparison schema (Phase 7) supports construct pairs with estimated correlations and validity flags |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Perplexity API | 2.0 | Academic instrument search | Already integrated in web_surfer.py with domain filtering; supports search_mode="academic" for scholarly sources |
| sentence-transformers | 3.3+ | Plagiarism detection via cosine similarity | Industry standard for semantic similarity; all-mpnet-base-v2 model optimized for sentence-level embeddings |
| langchain-openai | 0.2+ | GPT-5.2 for validity scoring | Already integrated in llm_factory.py; supports reasoning config for analytics tasks |
| langchain-anthropic | 0.2+ | Claude Opus for dual-direction scoring | Already integrated; used for validation in item_comparison.py pattern |
| scikit-learn | 1.8+ | Cosine similarity computation | Standard ML library; cosine_similarity function for vector comparison |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28+ | Perplexity API calls | Already used in web_surfer.py for HTTP requests with timeout support |
| Radix UI Collapsible | Latest | Progressive disclosure UI | Phase 8 pattern: collapsible panels for analytics below results table |
| shadcn/ui Badge | Latest | Warning pills for plagiarism | Established in Phase 8 CorrelationSummaryCard for status indicators |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sentence-transformers | LLM-based similarity (Claude/GPT) | LLM approach: more semantic depth but 10-20x cost and 5-10x latency; transformers: faster, cheaper, deterministic |
| Perplexity Academic | Semantic Scholar API | Semantic Scholar: free, comprehensive metadata; Perplexity: already integrated, better LLM synthesis |
| GPT-5.2 for scoring | Claude Opus only | GPT-5.2: reasoning tokens for complex validity assessment; Opus: proven in item_comparison.py, cheaper |

**Installation:**
```bash
# Backend dependencies (add to pyproject.toml)
sentence-transformers = "^3.3.0"
# scikit-learn already installed for omega calculation (Phase 8)
# httpx, langchain-openai, langchain-anthropic already installed

# Frontend dependencies (already installed)
# @radix-ui/react-collapsible via shadcn/ui
# Badge/Pill components already in ui/
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── agents/
│   ├── instrument_searcher.py    # New: Perplexity instrument search
│   ├── validity_scorer.py         # New: Convergent/discriminant LLM scoring
│   └── plagiarism_detector.py     # New: Cosine similarity flagging
├── analytics/
│   └── similarity_calculator.py   # New: sentence-transformers wrapper
├── settings.py                     # Add publisher blocklist, defaults
└── graph.py                        # Wire comparison_node, cross_construct_node

src/
├── components/
│   ├── ComparisonPanel.tsx         # New: Main comparison display card
│   ├── InstrumentCard.tsx          # New: Convergent/discriminant instrument display
│   └── PlagiarismBadge.tsx         # New: Warning pill for flagged items
└── lib/
    └── types.ts                    # ComparisonInstrument, CrossConstructComparison already defined
```

### Pattern 1: Hybrid Search-First with Fallback
**What:** Try Perplexity Academic search for instruments, fall back to hardcoded defaults on failure
**When to use:** Any external API call with reliability constraints (credits, timeouts, rate limits)
**Example:**
```python
# Source: Established in web_surfer.py retrieve_node pattern
def search_comparison_instruments(construct_name: str) -> list[ComparisonInstrument]:
    """Search for instruments with graceful fallback."""
    try:
        # Search-first: Perplexity Academic
        results = _search_perplexity_instruments(construct_name)
        if results:
            logger.info(f"Found {len(results)} instruments via Perplexity")
            return results
    except Exception as e:
        logger.warning(f"Perplexity search failed: {e}")

    # Fallback: Hardcoded defaults by domain
    defaults = _get_hardcoded_defaults(construct_name)
    logger.info(f"Using {len(defaults)} hardcoded default instruments")
    return defaults
```

### Pattern 2: Dual-Direction Scoring with Averaging
**What:** Score A→B and B→A, average results to mitigate LLM position bias
**When to use:** Any LLM-as-judge comparison task prone to position bias
**Example:**
```python
# Source: backend/evaluation/item_comparison.py (Phase 6)
def score_convergent_validity(generated_items: list[str], instrument_name: str) -> float:
    """Score convergent validity with position bias mitigation."""
    # Forward direction: generated → published
    forward_score = _score_single_direction(generated_items, instrument_name, "gen_to_pub")

    # Reverse direction: published → generated
    reverse_score = _score_single_direction(instrument_name, generated_items, "pub_to_gen")

    # Average to mitigate ~40% position bias
    averaged = (forward_score + reverse_score) / 2.0
    logger.info(f"Convergent validity: {averaged:.3f} (forward={forward_score:.3f}, reverse={reverse_score:.3f})")
    return averaged
```

### Pattern 3: Metadata-Only Instrument Storage
**What:** Store instrument metadata (name, citation, construct) but never item text
**When to use:** Copyright-protected content that requires metadata for comparison but not full text
**Example:**
```python
# Source: backend/schemas.py ComparisonInstrument (Phase 7)
# Schema enforces metadata-only — no item_text field exists
comparison_instrument = ComparisonInstrument(
    name="Rosenberg Self-Esteem Scale",
    construct="Self-Esteem",
    source_citation="Rosenberg, M. (1965). Society and the adolescent self-image. Princeton, NJ: Princeton University Press.",
    publication_year=1965,
    sample_items_count=10,
    psychometric_properties="α = 0.88, test-retest r = 0.82 (Blascovich & Tomaka, 1991)",
    similarity_rationale="Both measure global self-esteem in adult populations"
    # NO item_text field — enforced at schema level
)
```

### Pattern 4: Progressive Disclosure with Collapsible Card
**What:** Display analytics in collapsible card below main results, collapsed by default
**When to use:** Secondary analytics that enhance understanding but aren't primary workflow
**Example:**
```typescript
// Source: src/components/CorrelationPanel.tsx (Phase 8)
export function ComparisonPanel({ instruments, crossConstruct }: Props) {
  const [isExpanded, setIsExpanded] = React.useState(false); // Collapsed by default

  return (
    <SurfaceCard className="mt-4">
      <CardHeader
        className="cursor-pointer border-b hover:bg-surface-2/50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <CardTitle className="flex items-center gap-2">
          {isExpanded ? <ChevronDown /> : <ChevronRight />}
          Instrument Comparison
        </CardTitle>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-5">
          {/* Convergent + Discriminant instruments side-by-side */}
        </CardContent>
      )}
    </SurfaceCard>
  );
}
```

### Anti-Patterns to Avoid
- **Storing copyrighted item text:** Never add item_text field to ComparisonInstrument; use metadata only
- **Single-direction LLM scoring:** Always use dual-direction averaging to mitigate ~40% position bias
- **Blocking on plagiarism flags:** Phase 8 pattern: advisory warnings, not workflow blockers
- **Inline SSE events for instrument search:** User decision: show instruments only after generation completes
- **Separate export for comparison data:** User decision: include in full JSON export, no dedicated button

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Semantic similarity | Custom word embeddings, TF-IDF vectors | sentence-transformers (all-mpnet-base-v2) | Pre-trained on 1B+ sentence pairs; handles synonyms, paraphrasing, semantic drift; SOTA performance |
| Position bias in LLM judges | Ad-hoc randomization, single scoring | Dual-direction averaging (established pattern) | Validated in research: ~40% bias reduction; simple to implement; already proven in item_comparison.py |
| Publisher blocklist | Manual URL filtering in code | Perplexity domain_filter + settings.py config | Perplexity API supports domain exclusion natively; centralized config in settings.py for maintainability |
| Hardcoded instrument defaults | Inline dictionaries in functions | Structured JSON in data/ directory or settings.py | Maintainable, versionable, testable; supports domain-based lookup (personality, clinical, org, social, cognitive) |
| Plagiarism threshold tuning | Magic numbers in code | Configuration in settings.py with validation | User may want to adjust 0.85 threshold; centralized config enables A/B testing |

**Key insight:** Plagiarism detection is a solved problem in NLP (sentence-transformers + cosine similarity), LLM position bias has validated mitigation strategies (dual-direction scoring), and instrument metadata is copyright-safe (no need for custom solutions).

## Common Pitfalls

### Pitfall 1: Perplexity Search Returns Abstracts, Not Full Metadata
**What goes wrong:** Perplexity Academic search may return paper abstracts instead of structured instrument metadata (name, items, psychometrics)
**Why it happens:** Perplexity optimizes for passage retrieval, not structured data extraction; instruments may be mentioned in abstracts without full details
**How to avoid:**
- Include explicit metadata instructions in Perplexity query: "Return instrument name, author, year, construct measured, and sample item count"
- Use hardcoded defaults as primary source for well-known instruments (RSES, PHQ-9, etc.)
- Treat Perplexity results as supplementary, not replacement
**Warning signs:** Search returns citations but missing key fields like publication_year or sample_items_count

### Pitfall 2: LLM-Based Cosine Similarity is Too Slow/Expensive
**What goes wrong:** Using Claude/GPT to score item similarity instead of sentence-transformers adds 5-10x latency and 10-20x cost
**Why it happens:** LLMs can assess semantic similarity, but not optimized for pairwise comparison at scale
**How to avoid:** Use sentence-transformers for cosine similarity (deterministic, <100ms per comparison), reserve LLMs for convergent/discriminant validity scoring (higher-level assessment)
**Warning signs:** Plagiarism detection takes >5 seconds for 10 items, API costs spike with item count

### Pitfall 3: Single-Direction LLM Scoring Produces Inconsistent Results
**What goes wrong:** "Compare A to B" gives score of 8.5, "Compare B to A" gives 6.0 for same pair
**Why it happens:** LLMs exhibit ~40% position bias — preference for first-presented option
**How to avoid:** Always use dual-direction scoring with averaging (established in item_comparison.py), never present single-direction scores to users
**Warning signs:** Validity scores change when item order changes; users report "inconsistent" assessments

### Pitfall 4: Convergent/Discriminant Thresholds Too Strict
**What goes wrong:** Flagging convergent validity as "warning" for r < 0.70 even though 0.50-0.70 is acceptable for complex constructs
**Why it happens:** Psychology literature uses 0.70 as "ideal" but not "minimum"; context matters (broad vs narrow constructs)
**How to avoid:**
- Use tiered thresholds: r >= 0.70 = Pass (green), 0.50-0.69 = Acceptable (yellow), < 0.50 = Warning (orange)
- For discriminant validity: r < 0.20 = Pass, 0.20-0.85 = Acceptable, > 0.85 = High Overlap Warning
- Make thresholds configurable in settings.py for domain-specific tuning
**Warning signs:** All instruments show "warning" status; users complain about false positives

### Pitfall 5: Plagiarism Flags on Semantically Similar but Non-Plagiarized Items
**What goes wrong:** Flagging "I feel confident in my abilities" as plagiarism of "I believe in my capabilities" (0.88 similarity) when both are valid phrasings
**Why it happens:** 0.85 cosine similarity threshold captures semantic similarity, not verbatim copying
**How to avoid:**
- Frame as "high similarity" not "plagiarism" in UI (user decision: "Potential similarity to [Instrument] item")
- Use informational warnings (orange pill), not blocking errors (red)
- Document in UI: "LLM-estimated similarity, not legal determination"
**Warning signs:** Many false positive flags; users ignore warnings due to low precision

### Pitfall 6: Publisher Blocklist Too Narrow or Too Broad
**What goes wrong:**
- Too narrow: Perplexity returns MMPI or WAIS items (major copyright violations)
- Too broad: Blocking all .com domains excludes legitimate open-access repositories
**Why it happens:** Test publishers use varied domains; public-domain scales hosted on .org, .edu, and .com
**How to avoid:**
- Start with major publishers: pearson.com, parinc.com, mhs.com, wpspublish.com, hogrefe.com
- Use domain-level blocking (not URL-level) for efficiency
- Supplement with public-domain allowlist (IPIP, PsyToolkit, Psychology Tools)
**Warning signs:** Perplexity search returns no results (blocklist too broad), or returns copyrighted instruments (too narrow)

## Code Examples

Verified patterns from official sources and existing codebase:

### Example 1: Perplexity Instrument Search with Publisher Blocklist
```python
# Source: Extend web_surfer.py pattern with instrument-specific queries
import httpx
from backend.settings import settings
from backend.schemas import ComparisonInstrument

PUBLISHER_BLOCKLIST = [
    "pearson.com", "parinc.com", "mhs.com", "wpspublish.com",
    "hogrefe.com", "proedinc.com", "mindgarden.com"
]

def search_comparison_instrument(
    construct_name: str,
    search_type: str = "convergent"  # convergent | discriminant
) -> list[ComparisonInstrument]:
    """Search Perplexity Academic for comparison instruments."""
    if search_type == "convergent":
        query = f"Find validated psychometric instruments that measure {construct_name}. Include instrument name, author, year, construct measured, and number of items."
    else:
        query = f"Find validated instruments that measure constructs related to but distinct from {construct_name} (e.g., neighboring constructs in nomological network)."

    # Domain filter: academic allowlist + publisher blocklist
    academic_domains = settings.perplexity_domains()
    blocked_domains = PUBLISHER_BLOCKLIST

    payload = {
        "model": settings.PERPLEXITY_MODEL,
        "messages": [
            {"role": "system", "content": "You are a psychometric expert. Return structured instrument metadata."},
            {"role": "user", "content": query}
        ],
        "temperature": 0,
        "web_search_options": {
            "search_mode": "academic",
            "num_search_results": 10,
            "search_domain_filter": academic_domains,
            # Note: Perplexity doesn't support exclude_domains, so we filter results post-retrieval
        }
    }

    url = f"{settings.PERPLEXITY_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Parse and filter results
    instruments = _parse_instrument_metadata(data)
    filtered = [i for i in instruments if not _is_blocked_publisher(i.source_citation, blocked_domains)]

    return filtered[:2]  # User constraint: exactly 2 instruments (1 convergent, 1 discriminant)
```

### Example 2: Dual-Direction Convergent Validity Scoring
```python
# Source: Adapt item_comparison.py pattern for instrument-level scoring
from langchain_core.messages import HumanMessage, SystemMessage
from backend.agents.llm_factory import get_gpt52_analytics_model
from pydantic import BaseModel

class ConvergentValidityScore(BaseModel):
    score: float  # 0.0-1.0
    reasoning: str

def score_convergent_validity(
    generated_items: list[str],
    instrument_name: str,
    construct_name: str
) -> float:
    """Score convergent validity with position bias mitigation."""
    # Forward: generated items vs published instrument
    forward = _score_single_direction(
        generated_items, instrument_name, construct_name, "generated_to_published"
    )

    # Reverse: published instrument vs generated items
    reverse = _score_single_direction(
        instrument_name, generated_items, construct_name, "published_to_generated"
    )

    # Average to mitigate position bias
    averaged = (forward.score + reverse.score) / 2.0
    return averaged

def _score_single_direction(
    candidate: list[str] | str,
    reference: str | list[str],
    construct_name: str,
    direction: str
) -> ConvergentValidityScore:
    """Score one direction of convergent validity."""
    model = get_gpt52_analytics_model()

    system_prompt = """You are a psychometric expert assessing convergent validity.
    Score how well two instruments measure the same construct (0.0 = unrelated, 1.0 = identical).
    Consider: construct fidelity, item content overlap, measurement approach similarity."""

    user_prompt = f"""Construct: {construct_name}

CANDIDATE items:
{candidate if isinstance(candidate, str) else chr(10).join(f"{i+1}. {item}" for i, item in enumerate(candidate))}

REFERENCE instrument: {reference if isinstance(reference, str) else chr(10).join(f"{i+1}. {item}" for i, item in enumerate(reference))}

Provide convergent validity score (0.0-1.0) and brief reasoning."""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    runnable = model.with_structured_output(ConvergentValidityScore, strict=False)
    result = runnable.invoke(messages)

    return result
```

### Example 3: Cosine Similarity Plagiarism Detection
```python
# Source: sentence-transformers documentation + scikit-learn
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class PlagiarismDetector:
    """Detect high similarity between generated items and published items."""

    def __init__(self, threshold: float = 0.85):
        # all-mpnet-base-v2: 768-dim embeddings, SOTA for semantic similarity
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.threshold = threshold

    def detect_plagiarism(
        self,
        generated_items: list[str],
        published_items: list[str],
        instrument_name: str
    ) -> dict[int, str]:
        """Return dict of {item_index: warning_message} for flagged items."""
        # Encode all items to vectors
        gen_embeddings = self.model.encode(generated_items, convert_to_tensor=False)
        pub_embeddings = self.model.encode(published_items, convert_to_tensor=False)

        # Compute pairwise cosine similarities
        similarities = cosine_similarity(gen_embeddings, pub_embeddings)

        # Flag items exceeding threshold
        flagged = {}
        for i, gen_sims in enumerate(similarities):
            max_similarity = np.max(gen_sims)
            if max_similarity >= self.threshold:
                flagged[i] = f"Potential similarity to {instrument_name} item (r = {max_similarity:.2f})"

        return flagged

# Usage in comparison_node
detector = PlagiarismDetector(threshold=0.85)
flagged_items = detector.detect_plagiarism(
    generated_items=[item.item_text for item in final_items],
    published_items=comparison_instrument_items,
    instrument_name=comparison_instrument.name
)
# Store flagged_items for frontend display in GeneratedItemsTable
```

### Example 4: ComparisonPanel UI Component
```typescript
// Source: Adapt CorrelationPanel.tsx (Phase 8) for instrument comparison
"use client";

import * as React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Pill } from "@/components/ui/pill";
import type { ComparisonInstrument, CrossConstructComparison } from "@/lib/types";

interface ComparisonPanelProps {
  convergentInstrument: ComparisonInstrument;
  discriminantInstrument: ComparisonInstrument;
  convergentScore: number;
  discriminantCorrelation: number;
}

export function ComparisonPanel({
  convergentInstrument,
  discriminantInstrument,
  convergentScore,
  discriminantCorrelation
}: ComparisonPanelProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // Convergent validity status
  const convergentStatus = convergentScore >= 0.70
    ? { label: 'Pass', className: 'bg-green-500/20 text-green-400' }
    : { label: 'Warning', className: 'bg-amber-500/20 text-amber-400' };

  // Discriminant validity warning
  const showDiscriminantWarning = discriminantCorrelation > 0.85;

  return (
    <SurfaceCard className="mt-4">
      <CardHeader
        className="cursor-pointer border-b hover:bg-surface-2/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <CardTitle className="flex items-center gap-2 text-base">
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          Instrument Comparison
        </CardTitle>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-5">
          {/* Educational one-liner */}
          <p className="text-xs text-muted-foreground mb-4">
            Convergent validity: Items measure the same construct. Discriminant validity: Items distinguish from related constructs.
          </p>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Convergent Instrument */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold">Convergent Validity</h3>
                <Pill className={convergentStatus.className}>{convergentStatus.label}</Pill>
              </div>
              <p className="text-lg font-bold">{convergentScore.toFixed(2)}</p>
              <div className="text-xs space-y-1">
                <p className="font-medium">{convergentInstrument.name}</p>
                <p className="text-muted-foreground">{convergentInstrument.source_citation}</p>
                <p className="text-muted-foreground">{convergentInstrument.similarity_rationale}</p>
              </div>
            </div>

            {/* Discriminant Instrument */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold">Discriminant Validity</h3>
              {showDiscriminantWarning && (
                <Pill className="bg-amber-500/20 text-amber-400">
                  High overlap detected (r = {discriminantCorrelation.toFixed(2)})
                </Pill>
              )}
              <div className="text-xs space-y-1">
                <p className="font-medium">{discriminantInstrument.name}</p>
                <p className="text-muted-foreground">{discriminantInstrument.source_citation}</p>
                <p className="text-muted-foreground">{discriminantInstrument.similarity_rationale}</p>
              </div>
            </div>
          </div>

          {/* Copyright disclaimer */}
          <div className="mt-4 border-t border-border/40 pt-4">
            <p className="text-xs italic text-muted-foreground">
              Only instrument metadata is stored. No copyrighted item text is retrieved or displayed.
            </p>
          </div>
        </CardContent>
      )}
    </SurfaceCard>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded instrument lists only | Hybrid: Perplexity Academic search + hardcoded fallback | 2026 (Phase 9) | Dynamic discovery enables domain-agnostic instrument matching; fallback ensures robustness |
| Single-direction LLM scoring | Dual-direction averaging for position bias mitigation | 2025-2026 research | ~40% reduction in position bias; more reliable validity assessments |
| Manual similarity scoring | sentence-transformers (all-mpnet-base-v2) for plagiarism | 2023-2024 (SOTA model) | 10-20x faster, deterministic, proven for plagiarism detection |
| TF-IDF or word2vec for similarity | Transformer-based embeddings | 2023+ | Better semantic understanding; handles paraphrasing, synonyms |
| Blocking on low validity scores | Advisory flags only (Phase 8 pattern) | 2026 (Phase 8) | User maintains control; LLM estimates are guidance, not gatekeepers |

**Deprecated/outdated:**
- Manual instrument search via Google Scholar (replaced by Perplexity Academic API)
- Single-direction LLM-as-judge (replaced by dual-direction averaging)
- Word2vec/FastText for similarity (replaced by sentence-transformers with SOTA models)

## Open Questions

1. **Perplexity retrieval quality for instruments**
   - What we know: Perplexity Academic can retrieve metadata (titles, authors, citations)
   - What's unclear: Whether it consistently extracts item counts, psychometric properties, or just abstracts
   - Recommendation: Test on 10-20 known constructs (self-esteem, depression, burnout) before production; supplement with hardcoded defaults for well-known instruments

2. **Cosine similarity threshold precision**
   - What we know: 0.85 is standard for "high similarity" in plagiarism detection
   - What's unclear: False positive rate for psychometric items (which naturally overlap in phrasing)
   - Recommendation: Start with 0.85, monitor user feedback, make threshold configurable in settings.py for tuning

3. **Convergent validity threshold strictness**
   - What we know: 0.70 is "ideal" in psychology, but 0.50-0.70 acceptable for broad constructs
   - What's unclear: Whether single threshold or tiered thresholds (pass/acceptable/warning) better UX
   - Recommendation: Use tiered approach: >= 0.70 = Pass (green), 0.50-0.69 = Acceptable (yellow), < 0.50 = Warning (orange)

4. **GPT-5.2 vs Claude Opus for validity scoring**
   - What we know: GPT-5.2 has reasoning tokens for complex analytics, Opus proven in item_comparison.py
   - What's unclear: Which model produces more reliable validity scores
   - Recommendation: Phase 9 use GPT-5.2 (aligns with Phase 10 analytics optimization), track accuracy vs Opus in Phase 10

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ + Vitest 3.0+ |
| Config file | pytest.ini (backend), vitest.config.ts (frontend) |
| Quick run command | `pytest tests/test_instrument_searcher.py tests/test_plagiarism_detector.py -x` |
| Full suite command | `pytest tests/ --cov=backend` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INST-01 | Perplexity instrument search with domain filter | integration | `pytest tests/test_instrument_searcher.py::test_search_convergent_instrument -x` | ❌ Wave 0 |
| INST-02 | Hardcoded defaults by domain (personality, clinical, org, social, cognitive) | unit | `pytest tests/test_instrument_searcher.py::test_hardcoded_defaults_coverage -x` | ❌ Wave 0 |
| INST-03 | Hybrid search-first with fallback to defaults | integration | `pytest tests/test_instrument_searcher.py::test_search_fallback_on_failure -x` | ❌ Wave 0 |
| INST-04 | Dual-direction convergent validity scoring | unit | `pytest tests/test_validity_scorer.py::test_dual_direction_averaging -x` | ❌ Wave 0 |
| INST-05 | Publisher blocklist filters results | unit | `pytest tests/test_instrument_searcher.py::test_publisher_blocklist -x` | ❌ Wave 0 |
| INST-06 | Cosine similarity plagiarism detection (> 0.85) | unit | `pytest tests/test_plagiarism_detector.py::test_similarity_threshold -x` | ❌ Wave 0 |
| XCON-01 | Discriminant instrument search (related-but-distinct) | integration | `pytest tests/test_instrument_searcher.py::test_search_discriminant_instrument -x` | ❌ Wave 0 |
| XCON-02 | Dual-direction discriminant validity scoring | unit | `pytest tests/test_validity_scorer.py::test_discriminant_dual_direction -x` | ❌ Wave 0 |
| XCON-03 | High overlap warning (r > 0.85) | unit | `pytest tests/test_validity_scorer.py::test_high_overlap_flag -x` | ❌ Wave 0 |
| XCON-04 | Related construct identification from Perplexity | integration | `pytest tests/test_instrument_searcher.py::test_related_construct_discovery -x` | ❌ Wave 0 |
| UI-02 | ComparisonPanel renders with instruments | component | `npm test -- ComparisonPanel.test.tsx` | ❌ Wave 0 |
| UI-03 | InstrumentCard displays metadata and citation | component | `npm test -- InstrumentCard.test.tsx` | ❌ Wave 0 |
| UI-04 | Cross-construct table shows discriminant pairs | component | `npm test -- ComparisonPanel.test.tsx::discriminant_section` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_instrument_searcher.py tests/test_plagiarism_detector.py -x`
- **Per wave merge:** `pytest tests/ --cov=backend/agents/instrument_searcher.py --cov=backend/analytics/similarity_calculator.py`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_instrument_searcher.py` — covers INST-01, INST-02, INST-03, INST-05, XCON-01, XCON-04
- [ ] `tests/test_validity_scorer.py` — covers INST-04, XCON-02, XCON-03
- [ ] `tests/test_plagiarism_detector.py` — covers INST-06
- [ ] `src/components/__tests__/ComparisonPanel.test.tsx` — covers UI-02, UI-04
- [ ] `src/components/__tests__/InstrumentCard.test.tsx` — covers UI-03
- [ ] Framework install: `pip install pytest-asyncio pytest-mock sentence-transformers scikit-learn` — if not already installed

## Sources

### Primary (HIGH confidence)
- [Perplexity Academic API Documentation](https://docs.perplexity.ai/guides/academic-filter-guide) - Academic search mode and domain filtering
- [LangChain Documentation](https://docs.langchain.com/oss/python/langchain/test) - LangGraph testing patterns
- [sentence-transformers Documentation](https://www.sbert.net/) - Semantic similarity and plagiarism detection
- MAPIG codebase (backend/evaluation/item_comparison.py) - Dual-direction scoring pattern
- MAPIG codebase (src/components/CorrelationPanel.tsx) - Collapsible panel UI pattern

### Secondary (MEDIUM confidence)
- [Nature Machine Intelligence: Psychometric framework for LLMs](https://www.nature.com/articles/s42256-025-01115-6) - LLM-as-judge for psychometric assessment with convergent/discriminant validity
- [ScienceDirect: LLMs as raters in assessments](https://www.sciencedirect.com/science/article/pii/S2666920X25001213) - Reliability and validity of LLM-based scoring
- [ArXiv: Position bias in LLM-as-a-Judge](https://arxiv.org/html/2406.07791v9) - Dual-direction mitigation showing ~40% bias reduction
- [Scribbr: Convergent Validity](https://www.scribbr.com/methodology/convergent-validity/) - 0.70 threshold for convergent validity in psychology
- [ResearchGate: Construct validity standards](https://www.researchgate.net/post/Are_there_any_threshold_standards_for_Construct_validity_checks_when_using_Pearsons_r) - Convergent (0.70) and discriminant (±0.20) thresholds
- [International Personality Item Pool](https://ipip.ori.org/) - Public domain personality scales covering Big Five domains
- [shadcn/ui Collapsible Documentation](https://ui.shadcn.com/docs/components/radix/collapsible) - Radix UI collapsible patterns

### Tertiary (LOW confidence)
- [Pinecone: Plagiarism Detection with Transformers](https://www.pinecone.io/learn/plagiarism-detection/) - Cosine similarity threshold guidance
- [PMC: Copyright restrictions vs open access](https://pmc.ncbi.nlm.nih.gov/articles/PMC5766425/) - Test instrument copyright concerns
- [Vitest Component Testing Guide](https://vitest.dev/guide/browser/component-testing) - React component testing patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already integrated or proven SOTA (sentence-transformers, Perplexity, LangChain)
- Architecture: HIGH - Extends existing patterns (web_surfer.py, item_comparison.py, CorrelationPanel.tsx)
- Pitfalls: MEDIUM - Based on research findings and codebase patterns, but Phase 9-specific issues untested
- Validation: MEDIUM - Test patterns established, but Phase 9 test files don't exist yet (Wave 0 gap)

**Research date:** 2026-03-14
**Valid until:** 60 days (stable domain - psychometric standards evolve slowly; LLM APIs stable)
