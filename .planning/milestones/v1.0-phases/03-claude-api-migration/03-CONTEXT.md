# Phase 3: Claude API Migration - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Add Claude as the default LLM provider with smart model allocation (Opus for validation agent, Sonnet for all other agents) while keeping OpenAI as a user-selectable fallback. Users choose their provider before generation via setup form, and the system displays API costs broken down by model after generation completes. Environment configuration (CLAUDE_API_KEY) is handled via Vercel environment variables with helpful error messages for missing keys.

</domain>

<decisions>
## Implementation Decisions

### Model Selection UI
- **Location:** Top of InstrumentSetupForm.tsx (first field before construct name)
- **Component:** Dropdown/select with options "Claude" (default) and "OpenAI"
- **Persistence:** Save to localStorage alongside other form fields—if user picks OpenAI, it stays OpenAI on next visit
- **Default behavior:** Claude selected by default for first-time users
- **Integration:** Add to existing form schema in `frontend/src/lib/schemas.ts`, persist using same pattern as other fields

### Fallback Behavior
- **Missing CLAUDE_API_KEY:** Validate API key presence when form is submitted. Show clear error: "CLAUDE_API_KEY not configured. Add to .env or Vercel environment variables, or switch to OpenAI." Prevent generation from starting.
- **Runtime API failures:** Retry with exponential backoff using existing `max_retries=3` and `timeout=60` in llm_factory.py. If all retries fail, stop generation and preserve checkpoint for resumption.
- **Error communication:** Emit SSE events via existing ProgressIndicator.tsx pattern (e.g., "Claude API rate limit — retrying in 5s..."). Users see real-time error/retry status without UI disruption.
- **Vercel setup guidance:** Add "Deployment > Vercel" section to README.md with step-by-step instructions for adding CLAUDE_API_KEY to Vercel environment variables

### Cost Tracking Display
- **Location:** Integrated into existing results panels (not a dedicated panel)—add cost summary to panel footers or inline where relevant
- **Detail level:** Model totals only—show breakdown: Claude Opus ($X.XX), Claude Sonnet ($Y.YY), Total ($Z.ZZ). No per-agent granularity, no token counts.
- **Timing:** Summary at the end only—calculate and display costs after generation completes in Results UI. No real-time cost accrual during Run step.
- **Export:** UI display only—do NOT include costs in Markdown/CSV/JSON exports. Cost data visible in Results UI but not part of downloaded files.

### Smart Model Allocation
- **Allocation logic:** Automatic—Opus for validation agent, Sonnet for all other agents (Item Writer, reviewers, Meta Editor, Critic, Web Surfer)
- **User control:** No override—allocation is transparent but not configurable. Users choose provider (Claude vs OpenAI), system handles model selection.
- **Visibility:** Not displayed—users don't see which agents use which models. Implementation detail handled by llm_factory.py.

### Claude's Discretion
- Specific panel placement for integrated cost display (footer vs inline vs collapsed section)
- Cost calculation approach (estimate from token counts vs Claude API response metadata)
- Error message copy and formatting for missing keys and API failures
- Whether to add help icon/tooltip next to model selector explaining API key requirements

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **LLM factory:** `app/agents/llm_factory.py` already has `get_claude_chat_model(model)` and `get_validator_model()` functions—Phase 1 implemented Claude support for validation agent
- **Claude dependency:** `langchain-anthropic` already installed and working (used in Phase 1)
- **Settings infrastructure:** `app/settings.py` has `CLAUDE_API_KEY` field and `VALIDATOR_MODEL = "claude-opus-4-6"` constant
- **Form persistence:** `frontend/src/components/InstrumentSetupForm.tsx` uses localStorage pattern with `STORAGE_KEY = "mapig-instrument-setup"`—add model selection field following same pattern
- **SSE streaming:** `frontend/src/components/ProgressIndicator.tsx` displays real-time agent progress via Server-Sent Events—reuse for error/retry notifications
- **Results panels:** `frontend/src/components/QualityChecksPanel.tsx`, `EvidenceAuditPanel.tsx`, `FeedbackHistoryPanel.tsx`—follow same component pattern for cost display

### Established Patterns
- **APP_MODE setting:** `app/settings.py` currently supports `"mock" | "azure" | "openai"`—need to extend to support `"claude"` option or change architecture to model selection
- **Model factory pattern:** `get_chat_model()` in `llm_factory.py` returns appropriate model based on APP_MODE—modify to accept model selection parameter
- **Frontend validation:** `frontend/src/lib/schemas.ts` uses Zod for form validation with defaults—add model_provider field with z.enum()
- **Cost calculation:** No existing cost tracking—need to add token counting or parse API response metadata (Claude API returns usage data in response)

### Integration Points
- **Backend model routing:** Modify `get_chat_model()` to accept optional `model_provider` parameter, route to `get_claude_chat_model()` or `get_openai_chat_model()` accordingly
- **Agent functions:** All agents call `invoke_structured(get_chat_model(), ...)` from `llm_utils.py`—need to pass model selection through state or config
- **State schema:** `app/schemas.py` defines GraphState—may need to add `model_provider` field to track user's choice through workflow
- **API endpoint:** `app/main.py` `/generate_items_stream` receives UserRequest—add model_provider field to request schema
- **Results response:** FinalOutput schema in `app/schemas.py`—add cost breakdown fields (opus_cost, sonnet_cost, total_cost) for UI display

</code_context>

<specifics>
## Specific Ideas

- Model selector dropdown should match existing form input styling (shadcn/ui components, Tailwind classes)
- Error for missing CLAUDE_API_KEY should include clickable link to README deployment section (if technical feasible in error UI)
- Cost display format: "$X.XX" with 2 decimal places, USD assumed (no currency selector needed for v1)
- Smart allocation is intentionally automatic—Opus is expensive but necessary for validation quality, Sonnet is cost-effective for drafting/reviewing

</specifics>

<deferred>
## Deferred Ideas

None—discussion stayed within phase scope.

</deferred>

---

*Phase: 03-claude-api-migration*
*Context gathered: 2026-03-08*
