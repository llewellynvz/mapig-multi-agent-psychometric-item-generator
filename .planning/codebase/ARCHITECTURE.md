# Architecture

**Analysis Date:** 2026-03-08

## Pattern Overview

**Overall:** Multi-agent orchestration with LangGraph state machine, following a sequential draft-review-revision loop with streaming progress updates.

**Key Characteristics:**
- **Agent-based collaboration**: Specialized agents (item writer, reviewers, editor, critic) operate on a shared typed state
- **Iterative improvement**: Draft items → parallel reviews → critic decision → revision or finalization
- **Stateful checkpointing**: LangGraph SQLite checkpoint system allows thread resumption and run recovery
- **Evidence-bounded generation**: All item drafting constrained to approved sources (local files or Perplexity academic search)
- **Streaming for UX**: Server-Sent Events (SSE) progress updates enable real-time frontend feedback without polling

## Layers

**API Layer (FastAPI):**
- Purpose: HTTP interface, SSE streaming, run status queries, request validation
- Location: `app/main.py`
- Contains: Two main endpoints (`/v1/generate-items`, `/v1/generate-items-stream`), health checks, status registry
- Depends on: LangGraph graph, checkpoint database
- Used by: Frontend (Next.js)

**Graph Orchestration Layer (LangGraph):**
- Purpose: Define workflow DAG, route state through nodes, handle decision logic (critic routing), enable checkpointing
- Location: `app/graph.py`
- Contains: `GraphState` TypedDict (shared state contract), node functions, edge definitions, graph compilation
- Depends on: Agent functions, schemas
- Used by: FastAPI app via `graph.invoke()` and `graph.astream()`

**Agent Layer:**
- Purpose: Encapsulate domain logic for retrieval, writing, reviewing, and editing
- Location: `app/agents/*.py`
- Contains: Specialized functions that call LLMs via `invoke_structured()` or execute deterministic logic
- Depends on: Prompt loader, LLM factory, schemas, settings
- Agents:
  - `retrieve_evidence()` / `web_surf()`: Evidence gathering (local + web)
  - `write_items()`: Initial item generation
  - `review_linguistic()`, `review_bias()`, `review_content()`: Parallel review passes
  - `revise_items()`: Reconciliation and editing
  - `decide()`: Accept/revise/stop decision

**LLM Integration Layer:**
- Purpose: Unified interface to OpenAI or Azure OpenAI with structured output validation
- Location: `app/agents/llm_utils.py`, `app/agents/llm_factory.py`
- Contains: `invoke_structured()` (LLM call wrapper), `get_chat_model()` (factory), mock mode stubs
- Depends on: LangChain, pydantic for schema validation
- Used by: All agent functions

**Schema / Contract Layer:**
- Purpose: Define all data structures between agents and at API boundaries
- Location: `app/schemas.py`
- Contains: `UserRequest`, `DraftItem`, `ReviewComment`, `FinalOutput`, agent I/O wrappers
- Pydantic validation ensures type safety and contract enforcement across all layers

**Frontend Layer (Next.js):**
- Purpose: User-facing UI for setup, generation, results, and feedback
- Location: `frontend/src/`
- Contains: Components (form, stepper, results table), API client, state management (React hooks + sessionStorage)
- Depends on: API client library (`lib/api.ts`), Zod for form validation
- Interaction: POST to `/v1/generate-items-stream`, poll `/v1/runs/{thread_id}/status`, receive SSE events

## Data Flow

**Standard Generation Run (Setup → Results):**

1. **User submits setup form** → `InstrumentSetupForm` (frontend)
   - Validates via Zod schema (`instrumentSetupSchema`)
   - Converts to `UserRequest` via `formToRequest()`

2. **Frontend calls `/v1/generate-items-stream`** with `UserRequest` header `X-Thread-ID`
   - Backend creates `thread_id` (uuid) if not provided
   - Initializes `RUN_STATUS_REGISTRY[thread_id]` with status="running"

3. **Graph execution begins** (invoked via `graph.astream()`)

   **init_run node:**
   - Initializes iteration counter, empty review comment arrays, timestamps
   - Sets up state for first iteration

   **retrieve_node:**
   - Calls `retrieve_evidence()` (local markdown files via token matching)
   - Optionally calls `web_surf()` if `SEARCH_PROVIDER` includes "perplexity" or "hybrid"
   - Deduplicates by URL/docref
   - Returns `evidence: List[EvidenceChunk]`

   **item_writer_node:**
   - Receives evidence chunks
   - Calls `write_items(request, evidence)` via LLM
   - Returns `draft_items: List[DraftItem]` (typically ~10 items)

   **reviewers_fanout_node (parallel execution):**
   - Spawns 3 concurrent threads: `review_content()`, `review_linguistic()`, `review_bias()`
   - Each returns `List[ReviewComment]` with issue/severity/suggestion
   - Comments are item-indexed (0-based) or global (item_index=None)
   - Results merged into state

4. **critic_node (decision point):**
   - Examines all review comments
   - Calls `decide()` to determine: "accept" | "revise" | "stop_max_iterations" | "needs_human"
   - Routes via `Command` with either "meta_editor_node" or "finalize_node"

5. **Conditional path A: Revise (iteration < MAX_ITERATIONS):**
   - **meta_editor_node:**
     - Calls `revise_items()` with conflicting comments
     - Returns revised items + revision plan
     - Clears old comments (fresh state for next iteration)
     - Loops back to `reviewers_fanout_node`

6. **Conditional path B: Finalize (accept or max iterations):**
   - **finalize_node:**
     - Collects approved sources (evidence URLs/docrefs)
     - Creates `AuditMetadata` with run tracking info
     - Wraps items + audit into `FinalOutput`

7. **Frontend streaming:**
   - Each node execution triggers SSE event: `{type: 'node_start', node, display_name, iteration}`
   - Final event: `{type: 'complete', data: final_output}` or `{type: 'error', message}`
   - Frontend parses SSE, updates `ProgressIndicator`, stores result in sessionStorage

**Human Feedback Rerun (Results → Refinement):**

1. User adds feedback in `HumanFeedbackPanel`, clicks "Refine"
2. Frontend submits new request with:
   - `human_feedback: str` (reviewer notes)
   - `previous_items: List[str]` (item texts from prior run)
   - Same `X-Thread-ID` (uses existing thread for checkpointing)
3. Graph restarts: retrieve → item_writer → review → critic → (revise | finalize)
4. Item writer can reference prior items for context
5. Result stored under same run context

**State Management:**

- **GraphState** (persistent across iterations):
  - `user_request`: Input contract, never modified
  - `draft_items`: Updated by item_writer, meta_editor
  - `evidence`: Set once by retrieve_node
  - `iteration`: Incremented by critic_node on revise decision
  - All comments cleared before next review cycle

- **RUN_STATUS_REGISTRY** (in-memory, per-thread):
  - Tracks current_node, display_name, iteration, final_output for SSE subscribers
  - Keyed by thread_id
  - Used by `/v1/runs/{thread_id}/status` polling endpoint

- **Checkpoint DB** (`.checkpoints.sqlite`):
  - LangGraph persists state after each node for resumption
  - Enables browser refresh recovery via X-Thread-ID

## Key Abstractions

**GraphState (TypedDict):**
- Purpose: Single source of truth for all workflow state
- Location: `app/graph.py` lines 37–58
- Pattern: Typed dictionary with required and optional fields; `total=False` allows partial updates
- Example: `retrieve_node()` returns `{"evidence": [...]}` — only updates that key

**UserRequest:**
- Purpose: Immutable user intent and constraints
- Location: `app/schemas.py` lines 8–71
- Pattern: Pydantic BaseModel with validation, forbidden extra fields, required + optional fields
- Used by: All agents; never modified in workflow

**ReviewComment:**
- Purpose: Standardized feedback unit from reviewers
- Location: `app/schemas.py` lines 107–121
- Fields: `type` (literal "linguistic"|"bias"|"content"), `item_index` (0-based or None), `issue`, `severity` (1–5), `suggested_edit`
- Pattern: Enables critic to aggregate and rank issues by severity

**DraftItem:**
- Purpose: Candidate item with provenance
- Location: `app/schemas.py` lines 86–101
- Fields: `item_text`, `construct_name`, `rationale`, `evidence_citations` (source_id list)
- Pattern: Maintains audit trail of evidence used per item

**Agent I/O Wrappers:**
- `ItemWriterResponse`, `LinguisticReviewResponse`, etc.
- Pattern: Simplify type checking in graph nodes; enforce contract via Pydantic validation
- Example: `invoke_structured(ItemWriterResponse, messages) → ItemWriterResponse`

## Entry Points

**Backend Entry (FastAPI app start):**
- Location: `app/main.py` lines 116–120
- Triggers: `lifespan()` context manager
- Responsibilities:
  1. Configure logging
  2. Initialize AsyncSqliteSaver checkpoint database
  3. Build LangGraph workflow
  4. Attach graph to `app.state`

**HTTP Entry (user generates items):**
- Endpoint: `POST /v1/generate-items-stream`
- Location: `app/main.py` lines 253–448
- Responsibilities:
  1. Parse request + X-Thread-ID header
  2. Normalize constraints (merge baseline + user)
  3. Initialize RUN_STATUS_REGISTRY
  4. Call `graph.astream()` to yield node events
  5. Return SSE StreamingResponse

**Frontend Entry:**
- Location: `frontend/src/app/page.tsx` lines 1–60+
- Triggers: Page load or Stepper navigation
- Responsibilities:
  1. Manage UI flow: "setup" | "run" | "results"
  2. Handle form submission → `generateItemsStream()`
  3. Parse SSE events and update ProgressIndicator
  4. Persist session state to sessionStorage
  5. Display results or error state

## Error Handling

**Strategy:** Multi-layered with fallback to rule-based decisions.

**Agent Errors:**
- LLM call fails → `invoke_structured()` attempts fallback JSON parsing
- If both fail → exception propagates to graph node
- Node exception → caught in `/generate-items-stream` event_generator, yields `{type: 'error', message, trace}`
- Frontend displays error banner with optional trace

**Graph Errors:**
- Node raises exception → recorded in `RUN_STATUS_REGISTRY[thread_id].error`
- FastAPI returns 500 HTTPException if graph.invoke() fails
- Streaming endpoint yields error event and closes SSE

**Critic Fallback:**
- If LLM critic fails → `_rule_based_fallback()` applies deterministic rules
- Severity thresholds: accept if max_sev <= 2 (or <= 3 after iteration 2)
- Blocking severity >= 5 always triggers revise
- Location: `app/agents/critic.py` lines 31–59

**Mock Mode:**
- APP_MODE="mock" → all agents return deterministic stub data
- Allows testing without API keys
- Example: `write_items()` generates fixed stems, `revise_items()` diversifies stems
- Location: Pattern in each agent file (e.g., `app/agents/item_writer.py` lines 16–42)

## Cross-Cutting Concerns

**Logging:**
- Framework: Python stdlib `logging` with root logger "lmaig"
- Pattern: `step()` context manager wraps each node, logs start/end with duration
- Setup: `configure_logging()` in FastAPI lifespan
- Location: `app/logging_setup.py`, `app/logging_utils.py`
- Performance tracking: `_performance_log` dict accumulates durations, exposed via `/v1/performance-summary`

**Validation:**
- Pydantic at all boundaries: `UserRequest`, agent I/O schemas, `FinalOutput`
- Zod on frontend: `instrumentSetupSchema` ensures form data before submission
- LLM structured output: `invoke_structured()` validates returned JSON against schema
- Extra fields forbidden (ConfigDict(extra="forbid")) prevents silent data loss

**Authentication:**
- Not implemented; API assumes trusted frontend (localhost/127.0.0.1 only)
- CORS restricted to localhost and regex `^https?://(localhost|127\.0\.0\.1)(:\d+)?$`
- Desktop app can include API keys in environment or launch config

**Threading:**
- Reviewers fanout: ThreadPoolExecutor with 3 workers in `reviewers_fanout_node()`
- Async main loop: FastAPI uses asyncio; `event_generator()` is async generator
- Checkpointer: AsyncSqliteSaver manages concurrent access to checkpoint DB
- No explicit locks; relies on SQLite ACID semantics and Python GIL

**Observability:**
- Debug logs: JSON-formatted to `.mapig/logs/debug.log` via `_debug_log()` middleware
- Run status polling: `/v1/runs/{thread_id}/status` allows frontend to query state without SSE
- Audit trail: Every run produces `AuditMetadata` with thread_id, run_id, iteration_count, stop_reason, approved_sources

---

*Architecture analysis: 2026-03-08*
