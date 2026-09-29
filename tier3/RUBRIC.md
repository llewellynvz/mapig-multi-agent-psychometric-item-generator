# Tier 3 Rating Rubric — MAPIG Item Quality

Independent, blinded expert judgment of item quality. Each item is rated on six psychometric dimensions (1–5), plus a holistic score and a source-attribution judgment.

## Rating scales (all 1–5)

### D1. Clarity
Is the item unambiguous, with a single natural interpretation?
- 5 — Immediately and unambiguously clear
- 4 — Clear
- 3 — Adequately clear; minor ambiguity
- 2 — Noticeably vague or confusing
- 1 — Confusing / open to multiple interpretations

### D2. Construct relevance
Does the item measure the target construct (not an adjacent construct)?
- 5 — Prototypical indicator of the construct
- 4 — Clearly relevant
- 3 — Partially relevant / tangential
- 2 — Mostly off-target
- 1 — Measures a different construct

### D3. Facet correspondence *(multi-facet constructs only)*
Does the item belong to its assigned facet?
- 5 — Uniquely and clearly belongs to the assigned facet
- 4 — Fits the assigned facet well
- 3 — Ambiguous between facets
- 2 — Better fits a different facet
- 1 — Clearly belongs to a different facet

### D4. Distinctiveness (non-redundancy)
Does the item add unique content, or duplicate another item in the set?
- 5 — Adds unique, non-overlapping content
- 4 — Distinct
- 3 — Some overlap with other items
- 2 — Largely overlaps another item
- 1 — Near-identical to another item (redundant)

### D5. Behavioral observability
Does the item reference concrete, observable behavior/experience rather than abstract self-characterization?
- 5 — Concrete, observable behavior or experience
- 4 — Mostly concrete
- 3 — Mixed
- 2 — Mostly abstract
- 1 — Abstract trait claim / self-characterization

### D6. Freedom from bias
Is the item free of leading, double-barreled, or socially-desirable phrasing?
- 5 — Neutral, single-barreled, no social desirability
- 4 — Mostly clean
- 3 — Minor issues
- 2 — Noticeably leading / double-barreled / socially desirable
- 1 — Strongly biased

### Overall quality (holistic)
Would you keep this item in the final scale?
- 5 — Definitely keep
- 4 — Keep with minor edits
- 3 — Borderline
- 2 — Revise substantially
- 1 — Reject

### Source attribution (forced choice)
- **H** — human-written · **A** — AI-generated · **C** — cannot tell

## Global ratings (once per item set)
- **Domain coverage** (1–5): does the set cover the construct domain comprehensively?
- **Overall scale quality** (1–5)

## Composite & threshold
`Composite = 0.25·D2 + 0.20·D1 + 0.15·D3 + 0.15·D4 + 0.15·D5 + 0.10·D6`

- Acceptable item: **composite ≥ 4.0 AND no dimension ≤ 2**
- For single-facet constructs, drop D3 and renormalize (D2 .30, D1 .24, D4 .18, D5 .18, D6 .10).
- Weights are tunable; treat as starting points, not gospel.

## Inter-rater reliability
- Quality dimensions (ordinal 1–5): **Krippendorff's α** (ordinal); acceptable **α ≥ 0.60**.
- Source attribution (nominal H/A/C): **Fleiss' κ**; compare detection accuracy to chance via binomial test (chance = 0.50 for forced H/A, or use the H/A/C base rates).
- If α < 0.60: raters recalibrate on a small anchor set, then re-rate the flagged items.
