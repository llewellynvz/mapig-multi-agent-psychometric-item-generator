import sys, json, asyncio, logging, time
sys.path.insert(0, "/home/ldb/projects/mapig")
logging.basicConfig(level=logging.WARNING)

import numpy as np
from backend.graph import build_graph
from backend.checkpoint_config import create_checkpointer
from backend.schemas import UserRequest
from backend.agents.correlation_estimator import embed_items_sync, compute_cosine_similarity_matrix

OUT = "/home/ldb/projects/mapig/tier2_benchmark/gen_results.jsonl"

CONSTRUCTS = [
    {
        "id": "swls", "name": "Satisfaction with Life", "item_count": 5, "is_unidimensional": True,
        "population": "General adult population", "scale": "7-point Likert",
        "definition": "A global cognitive judgment of one's life as a whole, reflecting the degree to which a person evaluates their overall quality of life favorably.",
    },
    {
        "id": "grit", "name": "Grit", "item_count": 8, "is_unidimensional": False,
        "population": "Adults", "scale": "5-point Likert",
        "definition": "Perseverance and passion for long-term goals, comprising two facets: (1) Consistency of Interests, the tendency to maintain sustained interest in the same goals and projects over long periods rather than frequently changing focus; and (2) Perseverance of Effort, the tendency to sustain diligent effort and hard work despite setbacks, plateaus, and adversity.",
    },
    {
        "id": "uwes", "name": "Work Engagement", "item_count": 9, "is_unidimensional": False,
        "population": "Employees", "scale": "7-point frequency",
        "definition": "A positive, fulfilling, work-related state of mind characterized by three facets: (1) Vigor, high levels of energy and mental resilience while working; (2) Dedication, a sense of significance, enthusiasm, inspiration, and pride in one's work; and (3) Absorption, full concentration and happy immersion in one's work such that time passes quickly.",
    },
    {
        "id": "burnout", "name": "Burnout", "item_count": 9, "is_unidimensional": False,
        "population": "Human-service and client-facing workers", "scale": "5-point frequency",
        "definition": "A state of prolonged physical and psychological exhaustion, comprising three facets: (1) Personal burnout, physical and psychological exhaustion experienced by the person generally, regardless of and not attributed to their work; (2) Work-related burnout, exhaustion that is perceived as related to the person's work; and (3) Client-related burnout, exhaustion that is perceived as related to the person's work with clients.",
    },
]


async def run_one(graph, c):
    t0 = time.time()
    request = UserRequest(
        construct_name=c["name"],
        construct_definition=c["definition"],
        target_population=c["population"],
        response_scale=c["scale"],
        item_count=c["item_count"],
        is_unidimensional=c["is_unidimensional"],
        model_provider="claude",
    )
    state = await graph.ainvoke(
        {"user_request": request},
        config={"configurable": {"thread_id": f"tier2-gen-{c['id']}"}},
    )
    fo = state.get("final_output")
    fm = state.get("facet_mapping")
    pfa = state.get("pfa_pruning_result")
    audit = fo.audit if fo else None

    items = [i for i in fo.final_items] if fo else []
    facet_names = [f.facet_name for f in fm.facets] if fm and fm.facets else []
    # items per facet
    per_facet = {}
    for it in items:
        per_facet[it.facet_name or "(none)"] = per_facet.get(it.facet_name or "(none)", 0) + 1

    # redundancy: pairwise cosine of generated items
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
        "id": c["id"], "name": c["name"],
        "elapsed_s": round(time.time() - t0, 1),
        "facets_identified": facet_names,
        "n_items": len(items),
        "per_facet": per_facet,
        "items": [{"text": it.item_text, "facet": it.facet_name} for it in items],
        "pfa": {
            "recovery_rate": pfa.factor_recovery_rate if pfa else None,
            "tuckers_congruence": [round(x, 3) for x in (pfa.tuckers_congruence or [])] if pfa else None,
            "n_factors": pfa.n_factors if pfa else None,
        },
        "redundancy": redundancy,
        "audit": {
            "warnings": audit.warnings if audit else None,
            "total_cost_usd": audit.total_cost if audit else None,
            "iteration_count": audit.iteration_count if audit else None,
            "force_accepted_below_threshold": audit.force_accepted_below_threshold if audit else None,
            "stop_reason": audit.stop_reason if audit else None,
        },
    }
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"[{c['id']}] done in {rec['elapsed_s']}s | facets={facet_names} | per_facet={per_facet} | "
          f"pfa_recovery={rec['pfa']['recovery_rate']} | redundancy={redundancy} | cost=${rec['audit']['total_cost_usd']}")
    return rec


async def main():
    checkpointer = create_checkpointer()
    graph = build_graph(checkpointer=checkpointer)
    for c in CONSTRUCTS:
        try:
            await run_one(graph, c)
        except Exception as e:
            print(f"[{c['id']}] FAILED: {e}")
            with open(OUT, "a") as f:
                f.write(json.dumps({"id": c["id"], "error": str(e)}) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
