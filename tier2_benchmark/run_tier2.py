import sys, json
sys.path.insert(0, "/home/ldb/projects/mapig")
import numpy as np
import logging
logging.basicConfig(level=logging.WARNING)

from scipy.optimize import linear_sum_assignment
from backend.schemas import DraftItem, FacetDefinition, FacetMapperResponse
from backend.agents.pfa_estimator import run_pfa, tuckers_congruence

DATA = "/home/ldb/projects/mapig/tier2_benchmark/instruments.json"


def load_instruments(path=DATA):
    return json.load(open(path))["instruments"]


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
    facets = []
    for f in inst["factors"]:
        facets.append(FacetDefinition(
            facet_name=f,
            facet_description=f"Published facet: {f}",
            exclusions="None (benchmark ground-truth)",
            target_item_count=sum(1 for it in inst["items"] if inst["factors"][it["factor"]] == f),
        ))
    return FacetMapperResponse(
        is_unidimensional=(len(facets) == 1),
        facets=facets,
        theoretical_basis=inst["citation"],
    )


def align_factors(loadings, parent_factor, n_factors):
    """Return column permutation so recovered factors match expected factors.

    Uses Hungarian assignment on summed |loadings| per expected factor.
    perm[i] = recovered factor index assigned to expected factor i.
    """
    if n_factors == 1:
        return [0]
    parent = np.array(parent_factor)
    cost = np.zeros((n_factors, n_factors))
    for i in range(n_factors):
        mask = parent == i
        for j in range(n_factors):
            cost[i, j] = -np.abs(loadings[mask, j]).sum()
    row_ind, col_ind = linear_sum_assignment(cost)
    perm = [0] * n_factors
    for r, c in zip(row_ind, col_ind):
        perm[r] = c
    return perm


def main():
    results = []
    for inst in load_instruments():
        items = build_items(inst)
        fm = build_facet_mapping(inst)
        pfa = run_pfa(items, facet_mapping=fm, n_factors=inst["n_factors"])

        if not pfa.loadings:
            print(f"\n=== {inst['name']} — PFA NOT ESTIMABLE ===")
            results.append({"id": inst["id"], "accuracy": None})
            continue

        n_factors = inst["n_factors"]
        loadings = np.array([fl.loadings for fl in pfa.loadings])
        parent = [fl.parent_factor for fl in pfa.loadings]
        total = len(pfa.loadings)

        perm = align_factors(loadings, parent, n_factors)
        aligned = loadings[:, perm]          # aligned[:, i] = expected factor i
        aligned_primary = aligned.argmax(axis=1)
        correct = int((aligned_primary == np.array(parent)).sum())
        accuracy = correct / total

        # MAPIG's own (unaligned) internal metrics for contrast
        mapig_rec = pfa.factor_recovery_rate
        mapig_cong = [round(c, 3) for c in pfa.tuckers_congruence]

        # Tucker congruence of aligned recovered loadings vs one-hot expected pattern
        expected_onehot = np.zeros((total, n_factors))
        expected_onehot[np.arange(total), parent] = 1.0
        cong_aligned = [round(c, 3) for c in tuckers_congruence(aligned, expected_onehot)]

        print(f"\n=== {inst['name']} | {n_factors} factors | {total} items ===")
        print(f"Permutation recovered->expected: {perm}")
        print(f"Item->factor accuracy (AFTER alignment): {correct}/{total} = {accuracy:.1%}")
        print(f"Tucker congruence (aligned, vs one-hot expected): {cong_aligned}")
        print(f"MAPIG internal (unaligned): recovery={mapig_rec}, congruence={mapig_cong}")
        print(f"fit_verdict={pfa.fit_verdict} rmsr={pfa.rmsr} caf={pfa.caf}")
        print("Aligned loadings (expected factor columns):")
        for fl, p in zip(pfa.loadings, parent):
            ld = [round(x, 2) for x in aligned[fl.item_index]]
            mark = "" if aligned_primary[fl.item_index] == p else "  <-- MISMATCH"
            print(f"  [{p}] {ld}  {fl.item_text[:52]}{mark}")

        results.append({
            "id": inst["id"], "n_factors": n_factors, "n_items": total,
            "accuracy": round(accuracy, 3), "congruence": cong_aligned,
        })

    print("\n\n=== SUMMARY (factor-aligned) ===")
    for r in results:
        print(f"{r['id']}: {r['n_items']} items / {r['n_factors']} factors -> "
              f"accuracy={r['accuracy']}, congruence={r['congruence']}")


if __name__ == "__main__":
    main()
