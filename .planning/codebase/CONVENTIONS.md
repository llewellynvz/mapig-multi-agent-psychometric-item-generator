# Coding Conventions

**Analysis Date:** 2026-03-08

## Naming Patterns

**Files:**
- Python files: `snake_case.py` (e.g., `item_writer.py`, `llm_factory.py`, `bias_reviewer.py`)
- TypeScript/React files: `PascalCase.tsx` for components (e.g., `InstrumentSetupForm.tsx`, `Stepper.tsx`), `camelCase.ts` for utilities (e.g., `api.ts`, `schemas.ts`)
- Test files: `test_*.py` for Python (e.g., `test_smoke.py`)

**Functions:**
- Python: `snake_case` (e.g., `write_items()`, `retrieve_evidence()`, `invoke_structured()`)
- TypeScript/React: `camelCase` for regular functions (e.g., `generateItemsStream()`), `PascalCase` for React components (e.g., `InstrumentSetupForm()`)
- Private/internal functions prefixed with underscore: `_rule_based_fallback()`, `_normalize_request()`, `_set_run_status()`

**Variables:**
- Python: `snake_case` (e.g., `thread_id`, `draft_items`, `evidence_citations`)
- TypeScript/React: `camelCase` (e.g., `threadId`, `draftItems`, `evidenceCitations`)
- Constants: UPPERCASE with underscores in Python (e.g., `STANDARD_ITEM_CONSTRAINTS`, `SESSION_STORAGE_KEY` in TS)
- React hooks state: `[value, setValue]` pattern (e.g., `[step, setStep]`, `[activeRun, setActiveRun]`)

**Types:**
- Python: `PascalCase` for Pydantic models (e.g., `UserRequest`, `DraftItem`, `ReviewComment`)
- TypeScript: `PascalCase` for interfaces/types (e.g., `ProgressEvent`, `InstrumentSetupFormValues`, `FinalOutput`)
- Type parameters: Single uppercase letter (e.g., `SchemaT`, `T`)

## Code Style

**Formatting:**
- **Python:** Implicit via linting (pyproject.toml specifies Python 3.11+)
- **TypeScript/React:** ESLint configured via Next.js defaults (`eslint-config-next`), strict mode enabled in `tsconfig.json`
- **Line length:** No explicit limit enforced; code observed ranges from 80-120 characters
- **Imports:** Grouped and sorted - standard library, third-party, local imports

**Linting:**
- **Python:** No explicit linting config found; rely on type hints via Pydantic
- **TypeScript:** ESLint (version ^8.57.1) configured through Next.js plugin. Run via `npm --prefix frontend run lint`

## Import Organization

**Order:**
1. `from __future__ import annotations` (Python future imports)
2. Standard library imports (os, sys, datetime, functools, etc.)
3. Third-party imports (pydantic, fastapi, langchain, etc.)
4. Local app imports (app.*, relative imports)

**Example (Python):**
```python
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from pydantic import BaseModel
from langchain_openai import ChatOpenAI

from app.agents.llm_utils import invoke_structured
from app.schemas import DraftItem, UserRequest
```

**Example (TypeScript):**
```typescript
import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";

import { AppDescription } from "@/components/AppDescription";
import { generateItemsStream } from "@/lib/generate";
```

**Path Aliases:**
- TypeScript: `@/*` maps to `frontend/src/*` (configured in `tsconfig.json`)
- Python: Absolute imports from `app.*` root namespace

## Error Handling

**Patterns:**
- **Python:** Explicit exception raising with descriptive messages
  - `raise ValueError("message")` for validation errors
  - `raise RuntimeError("message")` for operational errors
  - Try/except blocks with empty pass statements in non-critical code (e.g., `except Exception: pass` in logging setup)
  - FastAPI `HTTPException(status_code, detail)` for API errors
- **TypeScript/React:** Try/catch with optional chaining and type guards
  - `isFinalOutput()` type guard function to validate shape before use
  - Silent failures acceptable for non-critical operations (e.g., localStorage access)

**Example (Python):**
```python
def invoke_structured(schema: Type[SchemaT], messages: List[Message]) -> SchemaT:
    if settings.APP_MODE not in ("openai", "azure"):
        raise RuntimeError("invoke_structured called in mock mode.")

    try:
        runnable = llm.with_structured_output(schema, strict=True)
    except TypeError:
        runnable = llm.with_structured_output(schema)
    return runnable.invoke(messages)
```

**Example (TypeScript):**
```typescript
function isFinalOutput(value: unknown): value is FinalOutput {
  if (!value || typeof value !== "object") return false;
  const obj = value as Record<string, unknown>;
  return Array.isArray(obj.final_items) && typeof obj.audit === "object";
}
```

## Logging

**Framework:** Python `logging` module; TypeScript `console` (for browser) and custom debug logging to `.mapig/logs/debug.log`

**Patterns:**
- Python: Context manager `@contextmanager` for performance tracking with step names
  - `step(step_name, state)` yields and logs STEP_START/STEP_END with duration
  - Logger: `logger = logging.getLogger("lmaig")`
  - Slow step warning if duration > 10 seconds
- TypeScript: Conditional file-based logging when `MAPIG_DEBUG_LOG_PATH` env var set
  - Structured JSON log entries with `{id, timestamp, location, message, data, hypothesisId}`

**Example (Python):**
```python
@contextmanager
def step(step_name: str, state: Optional[Dict[str, Any]] = None) -> Iterator[None]:
    start = time.perf_counter()
    logger.info("STEP_START %s thread_id=%s run_id=%s iteration=%s",
                step_name, state.get("thread_id"), state.get("run_id"), state.get("iteration"))
    try:
        yield
    finally:
        dur = time.perf_counter() - start
        logger.info("STEP_END %s duration=%.3fs", step_name, dur)
        if dur > 10.0:
            logger.warning("SLOW_STEP %s took %.3fs", step_name, dur)
```

## Comments

**When to Comment:**
- Document non-obvious control flow (e.g., LangGraph routing logic)
- Explain "why" not "what" - code should be self-explanatory for "what"
- Docstrings on public functions and classes
- #region and #endregion blocks for visually grouping related functionality (used in `main.py` for debug logging sections)

**JSDoc/TSDoc:**
- Not systematically used; prefer inline type annotations via TypeScript
- React component exports documented via TypeScript interface comments

**Example:**
```python
def _normalize_request(request: UserRequest) -> UserRequest:
    # Baseline constraints are always active; user constraints are additive.
    merged_constraints: list[str] = []
    for item in [*STANDARD_ITEM_CONSTRAINTS, *(request.constraints or [])]:
        value = (item or "").strip()
        if value and value not in merged_constraints:
            merged_constraints.append(value)
    return request.model_copy(update={"constraints": merged_constraints})
```

## Function Design

**Size:** Functions typically 20-60 lines; larger functions (100+ lines) exist for streaming handlers but remain focused on single responsibility

**Parameters:**
- Explicit type hints always present
- Use Pydantic models for multi-field parameters (e.g., `UserRequest` instead of scattered kwargs)
- Optional parameters use `Optional[T] = None` pattern

**Return Values:**
- Pydantic models for structured data (e.g., `ItemWriterResponse`, `FinalOutput`)
- Tuples for multiple returns: `Tuple[Decision, str]`
- None for void operations
- Union types when multiple return types possible: `Union[ChatOpenAI, AzureChatOpenAI]`

**Example:**
```python
def get_chat_model() -> Union[ChatOpenAI, AzureChatOpenAI]:
    """Return the configured chat model for the current APP_MODE."""
    if settings.APP_MODE == "openai":
        return get_openai_chat_model()
    if settings.APP_MODE == "azure":
        return get_azure_chat_model()
    raise RuntimeError("get_chat_model called in mock mode.")
```

## Module Design

**Exports:**
- Python agents export single public function (e.g., `write_items()`, `review_bias()`) with internal helper functions prefixed with underscore
- TypeScript components exported as named/default export with interfaces for props/refs
- Settings and schemas exported as singleton instances (`settings = Settings()`) or type definitions

**Barrel Files:**
- Not extensively used; prefer direct imports from source files
- `app/agents/__init__.py` exists but is empty

**Example (Python agent structure):**
```python
# app/agents/item_writer.py - single public function
def write_items(request: UserRequest, evidence: List[EvidenceChunk]) -> ItemWriterResponse:
    """Generate initial draft items."""
    # Implementation
```

**Example (TypeScript component):**
```typescript
// frontend/src/components/InstrumentSetupForm.tsx
export const InstrumentSetupForm = React.forwardRef<InstrumentSetupFormRef, InstrumentSetupFormProps>(
  function InstrumentSetupForm({ onSubmit, isPending }, ref) {
    // Implementation
  }
);
```

## Type Safety

**Python:**
- Pydantic models with strict validation (`ConfigDict(extra="forbid")` disallows unknown fields)
- Type hints on all functions and class attributes
- Generic types for reusable abstractions: `TypeVar("SchemaT", bound=BaseModel)`
- `from __future__ import annotations` for forward references

**TypeScript:**
- Strict mode enabled in `tsconfig.json` (`"strict": true`)
- Zod schemas for runtime validation of API payloads
- Type inference via `z.infer<typeof schema>` for client-side schemas
- `unknown` type for dynamic data with narrowing via type guards

**Example (Zod schema):**
```typescript
export const instrumentSetupSchema = z.object({
  construct_name: z.string().min(2),
  item_count: z.number().min(2).max(50),
});
export type InstrumentSetupFormValues = z.infer<typeof instrumentSetupSchema>;
```

---

*Convention analysis: 2026-03-08*
