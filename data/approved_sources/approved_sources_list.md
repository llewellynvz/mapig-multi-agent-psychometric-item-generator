# Approved sources (allowlisted evidence)

This project is restricted to approved sources only.
Evidence must come from either:
1) Local markdown sources in this folder (cited as local:<source_id>#<chunk>)
2) Web retrieval restricted to allowlisted domains (Perplexity domain allowlist)

## Local approved sources (present in this repo)
- local:item_writing_guidelines
- local:workplace_belonging
- local:lm_aig_paper_lee_son_jia_2025
- local:construct_validity_clark_watson_2019
- local:psychological_testing_assessment_cohen_schneider_tobin_2022
- local:psychological_testing_hogan_2019
- local:test_scales_loewenthal_2001
- local:cross_cultural_adaptation_hedrih_2020

## Web retrieval allowlist (Perplexity)
Allowlist domains (preferred as publisher subdomains, not root domains):
- doi.org
- psycnet.apa.org
- link.springer.com
- sciencedirect.com
- onlinelibrary.wiley.com
- tandfonline.com
- journals.sagepub.com
- academic.oup.com
- cambridge.org
- journals.plos.org
- frontiersin.org
- jstor.org

Web results must be discarded if their final source domain is not in the allowlist.

## Notes
- If SEARCH_PROVIDER=perplexity, local guidelines may not be cited unless hybrid retrieval is enabled.
- Prefer SEARCH_PROVIDER=hybrid so local psychometric rules are always available for citation.
