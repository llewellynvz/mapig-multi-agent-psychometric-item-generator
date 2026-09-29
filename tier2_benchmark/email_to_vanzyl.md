Subject: MAPIG Tier 2 replication — results + GitHub updates needed

Hi Llewellyn,

I ran the Tier 2 replication benchmark we discussed — feeding the published items from SWLS, Grit-S, UWES-9 and the Copenhagen Burnout Inventory into MAPIG's PFA, plus a full-pipeline generation pass on all four construct definitions. The headline result is strong: 40/41 items (97.6%) recovered to their published factor, and Tucker congruence against published loading matrices runs .91–1.00 across all four instruments. That reproduces the Varrasi et al. ">.90" benchmark cleanly.

Running it end-to-end also surfaced a handful of concrete issues I'd like to see fixed on GitHub before we lock the Tier 2 section. In rough priority order:

1. PFA factor-order alignment. factor_recovery_rate and tuckers_congruence score recovered factors against the expected order, but oblique rotation returns factors in arbitrary order for 3+ factors. The CBI run recovered all three factors perfectly but in permuted order ({personal→1, work→2, client→0}), so the internal metrics reported recovery = 0.0 and congruence ≈ 0. Fix: align recovered factors to expected (Hungarian assignment on |loadings|, or the existing DAAL labels) before scoring.

2. Reverse-keyed sign handling. Reverse-keyed items recover with flipped sign (CBI item 13: −.38 vs published +.42). Worth checking that the polarity flip is applied consistently through the PFA.

3. is_unidimensional default. It defaults to true, which silently collapses multi-facet constructs to one undifferentiated pool — even when the construct definition explicitly names the facets (Grit and UWES both collapsed). Suggest auto-detecting dimensionality from the definition, or at minimum warning when the definition lists multiple facets but the flag is true.

4. Content-reviewer schema cap. ContentReviewResponse.comments[].issue is capped at 210 chars; Claude occasionally exceeds it, raising a Pydantic ValidationError, and the fallback parser then fails, crashing the run. Loosen the cap or truncate in the fallback.

5. Duplicate items. The pipeline can emit literal duplicates (saw "I'm satisfied with my job." twice). A string-similarity dedup before final output would close this.

6. Discriminant generation for overlapping facets. For semantically-close facets (personal vs work-related burnout), the generated items cross-contaminate — "personal burnout" items still mention "work" — and the PFA can't separate them. This matches the redundancy weakness already flagged in the repo's shipped eval_results.json.

7. Dependencies. requirements.txt pins langgraph-checkpoint==3.0.3 (doesn't exist on PyPI — jumps 3.0.1→4.0.0) and langchain-core==1.2.8 (conflicts with langchain-anthropic>=1.3.4). I had to comment the checkpoint pin and bump langchain-core to >=1.6.4,<2.0.0 to install.

8. Tests. The paper cites ~290 unit tests, but the repo has no Python tests and CI explicitly skips pytest when tests/ is absent. Either commit the test suite or soften that claim to "Tier 1 partial."

One methodological note worth agreeing on for the paper: UWES-9 (Schaufeli et al. 2006) and CBI (Kristensen et al. 2005) don't publish per-item loading matrices in the originals, so I sourced those from later validation studies (Sinval et al. 2018; Fiorilli et al. 2015). That makes factor-recovery the generalizable Tier 2 metric, with loading-congruence as a secondary check where published — worth a sentence in the method.

Full details — per-instrument tables, evidence for each issue, and the reproducible benchmark scripts — are in tier2_benchmark/FINDINGS.md in the repo. Happy to open GitHub issues for any of these if that's easier; just say the word.

Best,
Leon
