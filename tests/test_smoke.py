import os
import datetime as _dt

os.environ["APP_MODE"] = "mock"

from langgraph.checkpoint.memory import MemorySaver

from app.graph import build_graph
from app.schemas import UserRequest


def test_graph_smoke():
    graph = build_graph(checkpointer=MemorySaver())

    req = UserRequest(
        construct_name="Workplace belonging",
        construct_definition="A sustained sense of acceptance, inclusion, and social connection at work, reflected in feeling valued and able to participate without exclusion.",
        target_population="Employees",
        response_scale="5-point Likert",
        constraints=["No double-barrelled items", "Avoid idioms"],
    )


    initial_state = {
        "user_request": req,
        "thread_id": "test-thread",
        "run_id": "test-run",
        "timestamp_utc": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
    }

    config = {"configurable": {"thread_id": "test-thread"}, "recursion_limit": 50}
    state = graph.invoke(initial_state, config=config)

    assert "final_output" in state
    out = state["final_output"]
    assert len(out.final_items) == 10
    assert out.audit.thread_id == "test-thread"
