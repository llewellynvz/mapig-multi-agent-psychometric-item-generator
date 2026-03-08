# Testing Patterns

**Analysis Date:** 2026-03-08

## Test Framework

**Runner:**
- pytest (version ==9.0.2)
- Config: No explicit pytest.ini or pytest.cfg found; configured via `pyproject.toml` `[tool.poetry.group.dev.dependencies]`

**Assertion Library:**
- pytest assertions (`assert` statements)
- Pydantic model validation via `.model_validate()` and `.model_validate_json()`

**Run Commands:**
```bash
pytest tests/                          # Run all tests
pytest tests/test_smoke.py             # Run specific test file
pytest tests/ -v                       # Verbose output
pytest tests/ --tb=short               # Short traceback format
```

**Frontend Testing:**
- No test framework configured for TypeScript/React
- `eslint` available but linting-only: `npm --prefix frontend run lint`

## Test File Organization

**Location:**
- Backend: `tests/` directory at project root
- Frontend: No test files present

**Naming:**
- Pattern: `test_*.py` (e.g., `test_smoke.py`)
- Follows pytest convention

**Structure:**
```
lmaig-langgraph/
└── tests/
    └── test_smoke.py           # Integration-style smoke test
```

## Test Structure

**Suite Organization:**
```python
def test_graph_smoke():
    """Test the graph executes end-to-end with mock mode."""
    # Setup
    graph = build_graph(checkpointer=MemorySaver())
    req = UserRequest(...)
    initial_state = {...}

    # Execute
    config = {"configurable": {"thread_id": "test-thread"}, "recursion_limit": 50}
    state = graph.invoke(initial_state, config=config)

    # Assert
    assert "final_output" in state
    assert len(state["final_output"].final_items) == 10
```

**Patterns:**
- **Setup:** Construct required objects (graph, request, state dict)
- **Execute:** Call primary function/method and store result
- **Assert:** Use simple `assert` statements to verify state
- **No teardown:** Objects are isolated and garbage collected; SQLite checkpointer uses in-memory MemorySaver for tests

## Mocking

**Framework:** No explicit mocking library used; mock mode via environment variable

**Patterns:**
```python
# tests/test_smoke.py sets APP_MODE before imports
os.environ["APP_MODE"] = "mock"

from langgraph.checkpoint.memory import MemorySaver
from app.graph import build_graph

def test_graph_smoke():
    # Mock mode is active - agents return deterministic stub data
    graph = build_graph(checkpointer=MemorySaver())
```

**Agent Mock Behavior:**
- When `APP_MODE == "mock"`, agents return hardcoded responses
- Example in `app/agents/item_writer.py`:
  ```python
  if settings.APP_MODE == "mock":
      items: List[DraftItem] = []
      for i in range(item_count):
          items.append(DraftItem(
              item_text=f"I feel a sense of belonging at my workplace. (Item {i + 1})",
              construct_name=request.construct_name,
              rationale="Stubbed item for orchestration testing.",
              evidence_citations=["local:unknown#1"],
          ))
      return ItemWriterResponse(items=items)
  ```

**What to Mock:**
- External LLM calls (automatically handled by APP_MODE=mock)
- Optional services like Perplexity web search (skipped when not in "perplexity" or "hybrid" SEARCH_PROVIDER mode)

**What NOT to Mock:**
- Graph orchestration logic (test actual routing via LangGraph StateGraph)
- Pydantic validation (test real model creation and validation)
- State transformations (ensure actual state dicts flow correctly through nodes)

## Fixtures and Factories

**Test Data:**
- Inline construction of Pydantic models in test functions
- No separate fixtures module

**Example:**
```python
req = UserRequest(
    construct_name="Workplace belonging",
    construct_definition="A sustained sense of acceptance, inclusion, and social connection at work...",
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
```

**Location:**
- `tests/test_smoke.py` - single test file; no factory functions extracted yet

## Coverage

**Requirements:** None enforced (no coverage config in pyproject.toml)

**View Coverage:**
```bash
pytest tests/ --cov=app --cov-report=html
# Requires: pip install pytest-cov
```

## Test Types

**Unit Tests:**
- Minimal explicit unit tests; single agent functions could be tested in isolation
- Not currently implemented; focus is on integration via smoke test
- Would test individual agent functions like `write_items()`, `review_bias()` with mock evidence

**Integration Tests:**
- **Scope:** Full graph execution from initial state to final output
- **Approach:** `test_smoke()` is an integration test
  - Builds complete LangGraph with all agents
  - Passes realistic UserRequest through entire workflow
  - Verifies output structure and count
  - Uses mock checkpointer (MemorySaver) for persistence testing
- **What it covers:** Graph routing, state threading, agent orchestration, final output assembly

**E2E Tests:**
- Not implemented
- Would require running actual backend server with live LLM calls
- Currently developers test via browser with `npm run dev` + `python run_dev.py`

## Common Patterns

**Async Testing:**
- Not used; Python tests are synchronous
- Graph execution via `graph.invoke(state, config)` is blocking

**Error Testing:**
```python
# Pattern not explicitly shown in test_smoke.py, but should follow:
def test_invalid_request():
    try:
        UserRequest(construct_name="X")  # Violates min_length=2
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "construct_name" in str(e)
```

**LangGraph Testing:**
- Use `MemorySaver()` for in-memory checkpointing instead of SQLite
- Pass `config` dict with `{"configurable": {"thread_id": "..."}, "recursion_limit": 50}`
- Assert on final state keys: `assert "final_output" in state`
- Validate Pydantic model fields: `assert len(state["final_output"].final_items) == expected_count`

**Example Structure:**
```python
import os
import datetime as _dt

os.environ["APP_MODE"] = "mock"  # Set mode before imports

from langgraph.checkpoint.memory import MemorySaver
from app.graph import build_graph
from app.schemas import UserRequest

def test_graph_smoke():
    graph = build_graph(checkpointer=MemorySaver())

    req = UserRequest(
        construct_name="Test Construct",
        construct_definition="A clear definition of the construct.",
        target_population="Sample Population",
        response_scale="5-point Likert",
        constraints=[],
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
    assert len(state["final_output"].final_items) == 10
    assert state["final_output"].audit.thread_id == "test-thread"
```

## Frontend Testing Notes

**Current State:** No test framework for React/TypeScript components
- Developers manually test components via `npm --prefix frontend run dev`
- Components use React hooks (`useState`, `useImperativeHandle`, `useEffect`)
- Potential test targets: `InstrumentSetupForm`, `GeneratedItemsTable`, `ProgressIndicator`

**Recommended Approach** (not yet implemented):
- Would use Vitest (faster than Jest for Vite/Next.js) or Jest
- Would require testing library: `@testing-library/react`
- Would test form validation via Zod schemas
- Would mock API calls from `lib/generate.ts` and `lib/api.ts`

---

*Testing analysis: 2026-03-08*
