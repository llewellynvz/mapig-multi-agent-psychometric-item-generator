import sys, json, asyncio, logging, time
sys.path.insert(0, "/home/ldb/projects/mapig")
logging.basicConfig(level=logging.WARNING)

import numpy as np
from backend.graph import build_graph
from backend.checkpoint_config import create_checkpointer
from backend.schemas import UserRequest
from backend.agents.correlation_estimator import embed_items_sync, compute_cosine_similarity_matrix

OUT = "/home/ldb/projects/mapig/tier2_benchmark/gen_results_burnout_stability.jsonl"

BURNOUT = {
    "id": "burnout", "name": "Burnout", "item_count": 9, "is_unidimensional": False,
    "population": "Human-service and client-facing workers", "scale": "5-point frequency",
    "definition": "A state of prolonged physical and psychological exhaustion, comprising three facets: (1) Personal burnout, physical and psychological exhaustion experienced by the person generally, regardless of and not attributed to their work; (2) Work-related burnout, exhaustion that is perceived as related to the person's work; and (3) Client-related burnout, exhaustion that is perceived as related to the person's work with clients.",
}

N_RUNS = 2  # additional fresh runs (v2 already exists -> 3 data points total)


async def run_one(graph, c, run_idx):
    t0 = time.time()
    request = UserRequest(
        construct_name=c["name"], construct_definition=c["definition"],
        target_population=c["population"], response_scale=c["scale"],
        item_count=c["item_count"], is_unidimensional=c["is_unidimensional"],
        model_provider="claude",
    )
    state = await graph.ainvoke(
        {"user_request": request},
        config={"configurable": {"thread_id": f"tier2-burnout-stab-{run_idx}"}},
    )
    fo = state.get("final_output")
    pfa = state.get("pfa_pruning_result")
    items = [i for i in fo.final_items] if fo else []
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
        "run": run_idx, "elapsed_s": round(time.time() - t0, 1),
        "n_items": len(items), "per_facet": per_facet,
        "pfa_recovery": pfa.factor_recovery_rate if pfa else None,
        "congruence": [round(x, 3) for x in (pfa.tuckers_congruence or [])] if pfa else None,
        "redundancy": redundancy,
        "items": [it.item_text for it in items],
    }
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"[stab run {run_idx}] recovery={rec['pfa_recovery']} congruence={rec['congruence']} "
          f"per_facet={per_facet} max_cos={redundancy.get('max_cosine') if redundancy else None}")
    return rec


async def main():
    checkpointer = create_checkpointer()
    graph = build_graph(checkpointer=checkpointer)
    for i in range(1, N_RUNS + 1):
        try:
            await run_one(graph, BURNOUT, i)
        except Exception as e:
            print(f"[stab run {i}] FAILED: {e}")
            with open(OUT, "a") as f:
                f.write(json.dumps({"run": i, "error": str(e)}) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
