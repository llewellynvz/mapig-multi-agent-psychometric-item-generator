# Codebase Structure

**Analysis Date:** 2026-03-08

## Directory Layout

```
project-root/
├── app/                           # Backend Python package (FastAPI + LangGraph)
│   ├── main.py                   # FastAPI app, endpoints, SSE streaming
│   ├── graph.py                  # LangGraph workflow, node definitions, state
│   ├── schemas.py                # Pydantic models for all data structures
│   ├── settings.py               # Environment configuration (pydantic-settings)
│   ├── logging_setup.py          # Logging initialization
│   ├── logging_utils.py          # Performance tracking, step context manager
│   ├── agents/                   # Agent implementations
│   │   ├── llm_factory.py        # OpenAI/Azure client factory
│   │   ├── llm_utils.py          # invoke_structured wrapper, LLM call logic
│   │   ├── prompt_loader.py      # Load prompt templates from disk
│   │   ├── item_writer.py        # Draft item generation
│   │   ├── retrieval_agent.py    # Local evidence retrieval (token-based)
│   │   ├── web_surfer.py         # Perplexity academic search integration
│   │   ├── content_reviewer.py   # Content validity review agent
│   │   ├── linguistic_reviewer.py # Clarity and structure review agent
│   │   ├── bias_reviewer.py      # Fairness and bias detection agent
│   │   ├── meta_editor.py        # Revision synthesis and item editing
│   │   ├── critic.py             # Decision logic (accept/revise/stop)
│   │   └── __init__.py           # Package marker
│   ├── prompts/                  # System prompts (markdown)
│   │   ├── _shared.md            # Common instructions used by multiple agents
│   │   ├── item_writer.md        # Item generation guidance
│   │   ├── linguistic_reviewer.md# Linguistic review criteria
│   │   ├── bias_reviewer.md      # Bias detection instructions
│   │   ├── content_reviewer.md   # Content validity instructions
│   │   ├── web_surfer.md         # Perplexity query formation
│   │   ├── meta_editor.md        # Revision strategy guidance
│   │   └── critic.md             # Decision criteria
│   └── __init__.py               # Package marker
│
├── frontend/                      # Frontend Next.js application
│   ├── next.config.js            # Next.js configuration
│   ├── package.json              # Node dependencies
│   ├── public/                   # Static assets
│   │   ├── landing_page.png
│   │   └── ... (images, icons)
│   └── src/                      # React source code
│       ├── app/                  # Next.js App Router
│       │   ├── page.tsx          # Main application page (Setup/Run/Results flow)
│       │   ├── layout.tsx        # Root layout, global styles, providers
│       │   ├── api/              # API routes
│       │   │   └── debug-ping/   # Health check endpoint
│       │   └── stepper-story/    # Storybook-style component demo
│       ├── components/           # React components
│       │   ├── InstrumentSetupForm.tsx      # Construct/constraint input form
│       │   ├── FlowStepper.tsx              # Step navigation (Setup/Run/Results)
│       │   ├── ProgressIndicator.tsx       # Real-time progress with node steps
│       │   ├── GeneratedItemsTable.tsx     # Display draft items
│       │   ├── HumanFeedbackPanel.tsx      # Feedback collection for refinement
│       │   ├── EvidenceAuditPanel.tsx      # Display evidence sources
│       │   ├── QualityChecksPanel.tsx      # Review comments summary
│       │   ├── FeedbackHistoryPanel.tsx    # Multi-round refinement history
│       │   ├── SetupSnapshotCard.tsx       # Display prior setup parameters
│       │   ├── RunTimeline.tsx             # Iteration summary
│       │   ├── DeveloperDrawer.tsx         # Debug panel for developers
│       │   ├── Providers.tsx               # React Query, Toast setup
│       │   ├── ui/                        # UI primitives (shadcn/ui)
│       │   │   ├── card.tsx
│       │   │   ├── button.tsx
│       │   │   ├── action-buttons.tsx
│       │   │   ├── surface-card.tsx
│       │   │   ├── use-toast.ts
│       │   │   └── ... (more primitives)
│       │   └── ... (utility components)
│       ├── lib/                 # Utilities and types
│       │   ├── api.ts           # API constants (base URL, endpoints)
│       │   ├── generate.ts      # generate_items_stream(), generateItems(), fetchRunStatus()
│       │   ├── types.ts         # TypeScript interfaces (UserRequest, FinalOutput)
│       │   ├── schemas.ts       # Zod validation schemas + defaults
│       │   └── ... (utilities)
│       └── hooks/               # Custom React hooks
│           └── ... (useQuery, useToast, etc.)
│
├── desktop/                       # Electron-based desktop app (Windows)
│   ├── package.json              # Electron build config
│   ├── backend_entry.py          # Python subprocess launcher for backend
│   ├── setup/                    # Installer scripts
│   │   ├── setup.js              # NSIS installer generator
│   │   └── ... (installer config)
│   ├── scripts/                  # Build and packaging scripts
│   └── README.md                 # Desktop app usage
│
├── data/                          # Static data and approved sources
│   ├── approved_sources/         # Markdown files for local evidence
│   │   └── *.md                 # (e.g., "psychometric_scales.md")
│   └── ... (other data)
│
├── tests/                         # Test files
│   └── ... (pytest fixtures, integration tests)
│
├── .planning/                     # GSD planning artifacts
│   ├── codebase/                # This structure and related analyses
│   │   ├── ARCHITECTURE.md
│   │   ├── STRUCTURE.md
│   │   └── ... (other docs)
│   └── ... (phases, execution logs)
│
├── .env.example                  # Template for environment variables
├── .env                          # (ignored, contains secrets)
├── README.md                     # Project overview and quickstart
├── pyproject.toml                # Poetry Python project config
├── poetry.lock                   # Python dependency lock
├── .gitignore                    # Git exclusions (.env, __pycache__, node_modules, etc.)
└── run_dev.sh                    # Shell script to start dev environment
```

## Directory Purposes

**app/:**
- Purpose: FastAPI backend with multi-agent orchestration
- Contains: Workflow graph, agent functions, API endpoints, configuration
- Key files: `main.py` (entry), `graph.py` (orchestration), `schemas.py` (contracts)

**app/agents/:**
- Purpose: Modular agent implementations
- Contains: Each agent is a pure function that accepts state, calls LLM or local logic, returns output
- Key files: `llm_utils.py` (unified LLM call), `prompt_loader.py` (prompt management)

**app/prompts/:**
- Purpose: System instructions for each agent
- Contains: Markdown files with role descriptions, task definitions, output format specifications
- Pattern: Loaded dynamically by agent functions via `load_prompt("agent_name.md")`

**frontend/src/app/:**
- Purpose: Next.js App Router routes and layout
- Key file: `page.tsx` (main application page with Stepper logic)

**frontend/src/components/:**
- Purpose: Reusable React components for UI building blocks
- Pattern: Named after domain concepts (InstrumentSetupForm, HumanFeedbackPanel, etc.)
- UI primitives in `components/ui/` (shadcn/ui based)

**frontend/src/lib/:**
- Purpose: Business logic, API client, validation schemas
- Key files:
  - `api.ts`: URL constants, ProgressEvent interface, API response types
  - `generate.ts`: Wrapper functions for HTTP calls (generateItemsStream, fetchRunStatus)
  - `schemas.ts`: Zod validation aligned with backend UserRequest
  - `types.ts`: TypeScript interfaces matching backend Pydantic models

**data/approved_sources/:**
- Purpose: Local evidence base (curated markdown documents)
- Usage: `retrieve_evidence()` tokenizes these files and returns matching chunks
- Committed to repo: Yes

**desktop/:**
- Purpose: Windows desktop application wrapper
- Functionality: Prompts for API keys, starts backend/frontend, manages lifecycle
- Build output: `desktop/release/` contains NSIS installer

## Key File Locations

**Entry Points:**

- Backend HTTP: `app/main.py` (FastAPI app startup via uvicorn)
- Backend Graph: `app/graph.py` (build_graph() called in lifespan context)
- Frontend UI: `frontend/src/app/page.tsx` (root page, Stepper + form + results)
- Desktop: `desktop/backend_entry.py` (launches uvicorn subprocess)

**Configuration:**

- Environment: `app/settings.py` (Settings class with pydantic-settings)
- Frontend config: `frontend/.env.local` (NEXT_PUBLIC_API_URL, if needed)
- Build config: `frontend/next.config.js`, `pyproject.toml`, `package.json`

**Core Logic:**

- Workflow: `app/graph.py` (node functions, GraphState, edges, checkpointing)
- Agents: `app/agents/*.py` (per-agent logic, prompt loading, LLM integration)
- API: `app/main.py` (HTTP endpoints, SSE streaming, run status)
- Frontend state: `frontend/src/app/page.tsx` (React hooks, sessionStorage persistence)

**Testing:**

- Backend tests: `tests/` (pytest)
- Frontend tests: `frontend/__tests__` (not shown but expected)
- Test fixtures: `tests/` (conftest.py if using pytest)

## Naming Conventions

**Files:**

- Python modules: `snake_case.py` (e.g., `llm_utils.py`, `item_writer.py`)
- React components: `PascalCase.tsx` (e.g., `InstrumentSetupForm.tsx`, `ProgressIndicator.tsx`)
- Markdown prompts: `snake_case.md` (e.g., `item_writer.md`, `meta_editor.md`)
- Utility files: `snake_case.ts` (e.g., `api.ts`, `schemas.ts`, `generate.ts`)

**Directories:**

- Python packages: `lowercase` (e.g., `agents`, `prompts`)
- React features: `lowercase` (e.g., `components`, `hooks`, `lib`)
- Routes/pages: `kebab-case` for URL paths (e.g., `debug-ping`, `stepper-story`)

**Functions/Classes:**

- Python: `snake_case` for functions, `PascalCase` for classes
- React: `PascalCase` for components, `camelCase` for hooks (e.g., `useToast`)
- TypeScript: `camelCase` for variables/functions, `PascalCase` for types/interfaces

**Constants:**

- Python: `UPPER_SNAKE_CASE` (e.g., `STANDARD_ITEM_CONSTRAINTS`, `MAX_ITERATIONS`)
- TypeScript: `UPPER_SNAKE_CASE` or `camelCase` depending on role (e.g., `API_BASE_URL`, `SESSION_STORAGE_KEY`)

## Where to Add New Code

**New Agent:**
- Implementation: `app/agents/{agent_name}.py`
  - Function signature: `def agent_name(state_input: Type) -> StateOutput:`
  - Pattern: Load prompt, build payload, call `invoke_structured()`, return response
  - Location example: `app/agents/new_reviewer.py`
- System prompt: `app/prompts/{agent_name}.md`
- Integration: Register node in `app/graph.py` via `builder.add_node(name, function)`, add edges
- Schema: Define I/O types in `app/schemas.py` if not reusing existing types

**New Frontend Component:**
- Primary code: `frontend/src/components/{ComponentName}.tsx`
- Pattern: "use client" directive, export function returning JSX, use shadcn/ui primitives
- Example: `frontend/src/components/NewReviewPanel.tsx`
- Styling: Tailwind CSS (inline className), no CSS modules
- Tests: `frontend/__tests__/{ComponentName}.test.tsx` (if testing framework set up)

**New Utility Function:**
- Shared helpers: `frontend/src/lib/utilities.ts` (or create domain-specific file)
- API functions: Extend `frontend/src/lib/generate.ts` for new endpoints
- Validation: Add Zod schema to `frontend/src/lib/schemas.ts`

**New Backend Endpoint:**
- Location: Add route in `app/main.py` (FastAPI @app.get/post)
- Pattern: Validate input, call graph or utility, return response or StreamingResponse
- Example: `@app.post("/v1/new-operation")`

**New Prompt:**
- Location: `app/prompts/{agent_name}.md`
- Pattern: Start with role/persona, specify input format, define output constraints and format
- Loading: `load_prompt("agent_name.md")` in agent function
- Shared sections: Use references to `_shared.md` for common instructions

## Special Directories

**__pycache__, node_modules:**
- Purpose: Generated cache and installed dependencies
- Generated: Yes
- Committed: No (in .gitignore)

**.next:**
- Purpose: Next.js build output and cache
- Generated: Yes
- Committed: No (in .gitignore)

**.checkpoints.sqlite:**
- Purpose: LangGraph checkpoint database (thread state persistence)
- Generated: Yes
- Committed: No (in .gitignore, can be local-only or backed up separately)

**data/approved_sources/:**
- Purpose: Curated markdown evidence base
- Generated: No (human-maintained)
- Committed: Yes

**.env:**
- Purpose: Environment variables (API keys, config)
- Generated: No (user-created from .env.example)
- Committed: No (in .gitignore)

---

*Structure analysis: 2026-03-08*
