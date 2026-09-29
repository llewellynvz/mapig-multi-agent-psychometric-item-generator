"""End-to-end verification of the factor-order alignment fix.

Feeds the 19 published CBI items (with facet + polarity tags) into the repo's
own `run_pfa` and prints the INTERNAL factor_recovery_rate and Tucker congruence.
Before the fix, CBI read 0.0 recovery because oblimin returned the three factors
in permuted order; after `_align_factor_order`, the internal metrics must agree
with the known-good structure (~94.7% recovery, item 13 the only reverse-keyed miss).
"""

import json

from backend.agents.pfa_estimator import run_pfa
from backend.schemas import DraftItem, FacetDefinition, FacetMapperResponse

with open("tier2_benchmark/instruments.json") as f:
    data = json.load(f)

cbi = next(i for i in data["instruments"] if i["id"] == "cbi")

facets = [
    FacetDefinition(
        facet_name=n,
        facet_description=f"{n} items (Copenhagen Burnout Inventory)",
        exclusions="not applicable for benchmark",
        target_item_count=6,
    )
    for n in cbi["factors"]
]
mapping = FacetMapperResponse(
    is_unidimensional=False,
    facets=facets,
    theoretical_basis="Kristensen et al. (2005)",
)

items = [
    DraftItem(
        item_text=it["text"],
        construct_name="Burnout",
        rationale="published CBI item",
        facet_name=cbi["factors"][it["factor"]],
        polarity=it["polarity"],
    )
    for it in cbi["items"]
]

res = run_pfa(items, facet_mapping=mapping)
print("n_items              =", res.n_items)
print("n_factors            =", res.n_factors)
print("factor_labels        =", res.factor_labels)
print("factor_recovery_rate =", res.factor_recovery_rate)
print("tuckers_congruence   =", [round(c, 3) for c in res.tuckers_congruence])
print("fit_verdict          =", res.fit_verdict)
print("solver               =", res.solver)

# The regression this fixes: without alignment this printed 0.0 for CBI.
assert res.factor_recovery_rate is not None
assert res.factor_recovery_rate >= 0.9, (
    f"Expected CBI recovery >= 0.9 after alignment, got {res.factor_recovery_rate}"
)
print("\nPASS: factor-order alignment fix verified on CBI.")
