# Tier 3 Blinding & Administration Protocol

## Goal
Independent experts rate item quality without knowing whether each item is MAPIG-generated or human-written (published). The comparison — not a pass/fail of any single item — is the Tier 3 evidence.

## Item preparation (automated in `prepare_blinded.py`)
1. **Pool** all items: MAPIG-generated items + published items, per construct.
2. **Normalize formatting** to remove source fingerprints:
   - Strip trailing punctuation (periods).
   - Strip leading/trailing whitespace; collapse internal whitespace.
   - Sentence case only; no other rewording (keeps meaning intact).
   - Raters see *only* item text + assigned facet (no rationale, no metadata).
3. **Assign random IDs** (not revealing order or source).
4. **Shuffle** with a seeded RNG so MAPIG and published items are interleaved.
5. **Save the source key separately** (`pilot/key.csv`). Raters never see it.

## Administration
- One form per construct (or one combined form); include construct + facet definitions at the top (needed for D2/D3).
- Raters work **independently** — no discussion during rating.
- Self-paced; ~10–15 min per construct.
- Collect ratings as CSV (the form's rating grid) for direct analysis.

## Rater requirements
- Domain expertise in the construct (work engagement, burnout, personality, etc.).
- **3–5 independent raters**, blinded to source.
- **Co-authors may pilot the instrument but are NOT counted as independent raters.**

## Analysis
- **Per dimension:** MAPIG vs published mean ratings — report effect sizes (Cohen's d / Hedges' g) and Bayesian equivalents, not just p-values.
- **Composite:** MAPIG vs published (with the weighted composite from RUBRIC.md).
- **Detection:** accuracy vs chance, plus sensitivity/specificity (are AI items flagged more often than published?).
- **IRR:** as specified in RUBRIC.md.

## Conflict-of-interest note
Co-authors (including Leon) design and pilot the instrument but do not serve as the blinded panel. If a co-author's ratings are used at all, they are flagged as such and a sensitivity analysis (results with/without the co-author rater) is reported.

## Pilot (current stage)
Leon rates a small set against the rubric to (a) validate that anchors are unambiguous, (b) catch rating-scale problems, and (c) calibrate the composite threshold — before any independent expert is recruited.
