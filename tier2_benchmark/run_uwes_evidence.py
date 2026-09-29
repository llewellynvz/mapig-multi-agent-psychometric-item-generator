import sys, json, asyncio, logging, time
sys.path.insert(0, "/home/ldb/projects/mapig")
logging.basicConfig(level=logging.WARNING)

import numpy as np
from backend.graph import build_graph
from backend.checkpoint_config import create_checkpointer
from backend.schemas import UserRequest
from backend.agents.correlation_estimator import embed_items_sync, compute_cosine_similarity_matrix


async def main():
    checkpointer = create_checkpointer()
    graph = build_graph(checkpointer=checkpointer)
    request = UserRequest(
        construct_name="Work Engagement",
        construct_definition=(
            "A positive, fulfilling, work-related state of mind characterized by three facets: "
            "(1) Vigor, high levels of energy and mental resilience while working; "
            "(2) Dedication, a sense of significance, enthusiasm, inspiration, and pride in one's work; "
            "(3) Absorption, full concentration and happy immersion in one's work such that time passes quickly."
        ),
        target_population="Employees",
        response_scale="7-point frequency",
        item_count=9,
        is_unidimensional=False,
        model_provider="claude",
    )
    t0 = time.time()
    state = await graph.ainvoke(
        {"user_request": request},
        config={"configurable": {"thread_id": "tier2-uwes-evidence"}},
    )
    fo = state.get("final_output")
    fm = state.get("facet_mapping")
    pfa = state.get("pfa_pruning_result")
    audit = fo.audit if fo else None
    items = [i for i in fo.final_items] if fo else []

    print(f"elapsed={time.time()-t0:.1f}s")
    print("state_keys=", sorted(state.keys()))
    ev = state.get("evidence", [])
    print(f"evidence_chunks={len(ev)}")
    print(f"facets={[f.facet_name for f in fm.facets] if fm and fm.facets else []}")
    print(f"n_items={len(items)}")
    per = {}
    for it in items:
        per[it.facet_name or "(none)"] = per.get(it.facet_name or "(none)", 0) + 1
    print(f"per_facet={per}")
    print("items=", json.dumps([it.item_text for it in items], indent=0))
    print(f"pfa_recovery={pfa.factor_recovery_rate if pfa else None}")
    print(f"pfa_congruence={[round(x,3) for x in (pfa.tuckers_congruence or [])] if pfa else None}")
    if len(items) >= 2:
        embs = embed_items_sync([it.item_text for it in items])
        sim = compute_cosine_similarity_matrix(embs)
        np.fill_diagonal(sim, np.nan)
        off = sim[~np.eye(len(items), dtype=bool)]
        print(f"redundancy mean_cosine={float(np.nanmean(off)):.3f} max_cosine={float(np.nanmax(off)):.3f}")
    if audit:
        print("warnings=", json.dumps(audit.warnings))
        print(f"iterations={audit.iteration_count} force_accept={audit.force_accepted_below_threshold}")
        print(f"stop_reason={audit.stop_reason}")


asyncio.run(main())
