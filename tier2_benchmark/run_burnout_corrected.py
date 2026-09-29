import sys, json, asyncio, logging, time
sys.path.insert(0, "/home/ldb/projects/mapig")
logging.basicConfig(level=logging.WARNING)

import numpy as np
from backend.graph import build_graph
from backend.checkpoint_config import create_checkpointer
from backend.schemas import UserRequest
from backend.agents.correlation_estimator import embed_items_sync, compute_cosine_similarity_matrix

OUT = "/home/ldb/projects/mapig/tier2_benchmark/gen_results_burnout_v2.jsonl"

# CBI-faithful definition (Kristensen et al. 2005; Borritz & Kristensen 1999):
#   Personal  = exhaustion generally, NOT attributed to work
#   Work      = exhaustion perceived as related to work
#   Client    = exhaustion perceived as related to work with clients
BURNOUT = {
    "id": "burnout", "name": "Burnout", "item_count": 9, "is_unidimensional": False,
    "population": "Human-service and client-facing workers", "scale": "5-point frequency",
    "definition": "A state of prolonged physical and psychological exhaustion, comprising three facets: (1) Personal burnout, physical and psychological exhaustion experienced by the person generally, regardless of and not attributed to their work; (2) Work-related burnout, exhaustion that is perceived as related to the person's work; and (3) Client-related burnout, exhaustion that is perceived as related to the person's work with clients.",
}


async def run_one(graph, c):
    t0 = time.time()
    request = UserRequest(
        construct_name=c["name"], construct_definition=c["definition"],
        target_population=c["population"], response_scale=c["scale"],
        item_count=c["item_count"], is_unidimensional=c["is_unidimensional"],
        model_provider="claude",
    )
    state = await graph.ainvoke(
        {"user_request": request},
        config={"configurable": {"thread_id": "tier2-burnout-v2"}},
    )
    fo = state.get("final_output")
    fm = state.get("facet_mapping")
    pfa = state.get("pfa_pruning_result")
    audit = fo.audit if fo else None

    items = [i for i in fo.final_items] if fo else []
    facet_names = [f.facet_name for f in fm.facets] if fm and fm.facets else []
    per_facet = {}
    for it in items:
        per_facet[it.facet_name or "(none)"] = per_facet.get(it.facet_name or "(none)", 0) + 1

    redundancy = None
    if len(items) >= 2:
        try:
            embs = embed_items_sync([it.item_text for it in items])
            sim = compute_cosine_similarity_matrix(embs)
            np.fill_diagonal(sim, np.nan)
            off = sim[~np.eye(len(items), dtype=bool)]
            redundancy = {"mean_cosine": round(float(np.nanmean(off)), 3),
                          "max_cosine": round(float(np.nanmax(off)), 3)}
        except Exception as e:
            redundancy = {"error": str(e)}

    rec = {
        "id": c["id"], "name": c["name"], "elapsed_s": round(time.time() - t0, 1),
        "facets_identified": facet_names, "n_items": len(items), "per_facet": per_facet,
        "items": [{"text": it.item_text, "facet": it.facet_name} for it in items],
        "pfa": {
            "recovery_rate": pfa.factor_recovery_rate if pfa else None,
            "tuckers_congruence": [round(x, 3) for x in (pfa.tuckers_congruence or [])] if pfa else None,
            "n_factors": pfa.n_factors if pfa else None,
        },
        "redundancy": redundancy,
        "audit": {
            "warnings": audit.warnings if audit else None,
            "iteration_count": audit.iteration_count if audit else None,
            "force_accepted_below_threshold": audit.force_accepted_below_threshold if audit else None,
            "stop_reason": audit.stop_reason if audit else None,
        },
    }
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"[burnout-v2] done in {rec['elapsed_s']}s | facets={facet_names} | per_facet={per_facet} | "
          f"pfa_recovery={rec['pfa']['recovery_rate']} | redundancy={redundancy}")
    return rec


async def main():
    checkpointer = create_checkpointer()
    graph = build_graph(checkpointer=checkpointer)
    await run_one(graph, BURNOUT)


if __name__ == "__main__":
    asyncio.run(main())
