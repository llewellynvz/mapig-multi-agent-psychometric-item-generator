import sys, json
sys.path.insert(0, "/home/ldb/projects/mapig")
import numpy as np
import logging
logging.basicConfig(level=logging.WARNING)

from scipy.optimize import linear_sum_assignment
from backend.schemas import DraftItem, FacetDefinition, FacetMapperResponse
from backend.agents.pfa_estimator import run_pfa

DATA = "/home/ldb/projects/mapig/tier2_benchmark/instruments.json"
PUB = "/home/ldb/projects/mapig/tier2_benchmark/published_loadings.json"


def load_instruments():
    return json.load(open(DATA))["instruments"]


def load_published():
    return json.load(open(PUB))


def build_items(inst):
    items = []
    for it in inst["items"]:
        items.append(DraftItem(
            item_text=it["text"],
            construct_name=inst["name"],
            rationale="Published benchmark item (Tier 2 replication validation).",
            facet_name=inst["factors"][it["factor"]],
            polarity=it["polarity"],
        ))
    return items


def build_facet_mapping(inst):
    facets = [FacetDefinition(
        facet_name=f, facet_description=f"Published facet: {f}", exclusions="None (benchmark ground-truth)",
        target_item_count=sum(1 for it in inst["items"] if inst["factors"][it["factor"]] == f),
    ) for f in inst["factors"]]
    return FacetMapperResponse(is_unidimensional=len(facets) == 1, facets=facets, theoretical_basis=inst["citation"])


def align_permutation(loadings, parent, n_factors):
    if n_factors == 1:
        return [0]
    parent = np.array(parent)
    cost = np.zeros((n_factors, n_factors))
    for i in range(n_factors):
        for j in range(n_factors):
            cost[i, j] = -np.abs(loadings[parent == i, j]).sum()
    row, col = linear_sum_assignment(cost)
    perm = [0] * n_factors
    for r, c in zip(row, col):
        perm[r] = c
    return perm


def tucker_nan(a, b):
    """Tucker congruence between two loading vectors, ignoring NaN entries."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    mask = ~(np.isnan(a) | np.isnan(b))
    a, b = a[mask], b[mask]
    if len(a) < 2 or np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return np.nan
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    pub = load_published()
    for inst in load_instruments():
        pid = inst["id"]
        if pid not in pub:
            print(f"\n=== {inst['name']} — no published loadings available ===")
            continue

        items = build_items(inst)
        fm = build_facet_mapping(inst)
        pfa = run_pfa(items, facet_mapping=fm, n_factors=inst["n_factors"])
        if not pfa.loadings:
            continue

        n = inst["n_factors"]
        recovered = np.array([fl.loadings for fl in pfa.loadings])   # n_items x n_factors
        parent = [fl.parent_factor for fl in pfa.loadings]
        perm = align_permutation(recovered, parent, n)
        aligned = recovered[:, perm]

        # published matrix with NaN for missing (dropped) rows
        pub_raw = pub[pid]["loadings"]
        published = np.full((len(pub_raw), n), np.nan)
        for i, row in enumerate(pub_raw):
            if row is not None:
                published[i] = row

        cong = [tucker_nan(aligned[:, f], published[:, f]) for f in range(n)]

        print(f"\n=== {inst['name']} — Tucker congruence (MAPIG PFA vs published loadings) ===")
        print(f"Published source: {pub[pid]['citation']}")
        print(f"Per-factor congruence: {[round(c, 3) if not np.isnan(c) else 'n/a' for c in cong]}")
        valid = [c for c in cong if not np.isnan(c)]
        print(f"Mean: {round(float(np.mean(valid)), 3)}" if valid else "Mean: n/a")
        print(f"Factor names: {pub[pid]['factor_names']}")
        for i in range(len(items)):
            r = [round(float(x), 2) for x in aligned[i]]
            p = [round(float(x), 2) if not np.isnan(x) else None for x in published[i]]
            flag = "" if not np.any(np.isnan(published[i])) else "  (no published loading)"
            print(f"  {items[i].item_text[:48]:48s}  recovered={r}  published={p}{flag}")


if __name__ == "__main__":
    main()
