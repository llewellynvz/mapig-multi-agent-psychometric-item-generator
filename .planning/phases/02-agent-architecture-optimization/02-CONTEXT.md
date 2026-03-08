# Phase 2: Agent Architecture Optimization - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Refine all 7 agent prompts (Item Writer, Content Reviewer, Linguistic Reviewer, Bias Reviewer, Meta Editor, Critic, Web Surfer) with research-backed psychometric principles. Improve item quality standards, enforce semantic diversity, strengthen bias detection, and optimize decision logic. No changes to agent architecture or graph structure—prompts only.

</domain>

<decisions>
## Implementation Decisions

### Research Strategy
- **Primary sources:** Established test development standards (AERA/APA/NCME Standards for Educational and Psychological Testing, ITC Guidelines, canonical psychometric textbooks)
- **Extraction approach:** Extract actionable, concrete principles as checklists (e.g., "avoid double-barreled items", "use simple sentence structure")
- **Research focus:** Prioritize Item Writer + Bias Reviewer for deep research (10 principles + 7 bias types). Lighter treatment for other 5 agents.
- **Documentation format:** Create separate RESEARCH.md per agent (e.g., `02-item-writer-RESEARCH.md`, `02-bias-reviewer-RESEARCH.md`) with extracted principles, rationale, and prompt guidance

### Prompt Design Approach
- **Principle embedding:** Supplement existing Item Writer prompt structure (sections A-D) with any missing psychometric principles from research. Keep what's working, fill gaps.
- **Examples:** Include 1-2 examples only for complex concepts (semantic diversity, intersectional bias detection). Rely on instructions for straightforward principles. Balance clarity with token efficiency.
- **Reading level enforcement:** Specify target reading levels in prompts as guidelines (6th-8th grade general, 5th-6th grade clinical, 10th-12th grade specialized). No automated Flesch-Kincaid measurement—rely on agent judgment.
- **Chain-of-thought reasoning:** Required for Item Writer (explain facet targeting, wording choices) and Bias Reviewer (explain bias detection reasoning). Optional for other agents.

### Claude's Discretion
- Specific 10 psychometric principles to include in Item Writer (research will identify)
- Specific 7 bias types taxonomy structure for Bias Reviewer
- Whether to implement multi-pass bias review (separate evaluation per type) or single comprehensive pass
- How to structure Meta Editor's facet balancing guidance
- How to refine Critic's adaptive iteration thresholds
- Whether to A/B test 7→6 agent consolidation (AGT-11 optional requirement)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Prompt loader:** `app/agents/prompt_loader.py` with `load_prompt(agent_name.md)` function—dynamically loads markdown prompts from `app/prompts/`
- **Current agent prompts:** 7 markdown files in `app/prompts/` directory:
  - `item_writer.md` - already has sections A-D with psychometric guidance
  - `content_reviewer.md`, `linguistic_reviewer.md`, `bias_reviewer.md` - reviewer prompts
  - `meta_editor.md`, `critic.md` - revision and decision prompts
  - `web_surfer.md` - evidence retrieval prompt
  - `_shared.md` - common instructions referenced by multiple agents
- **Agent pattern:** Single public function per agent (e.g., `write_items()`, `review_bias()`) that loads prompt, calls `invoke_structured()` wrapper, returns typed Pydantic response

### Established Patterns
- **Prompt format:** Markdown with clear sections (Role, Inputs, Output format, Requirements)
- **LLM calls:** All agents use `invoke_structured(schema, messages)` from `llm_utils.py` for structured output validation
- **Parallel execution:** 3 reviewers run concurrently via ThreadPoolExecutor in `reviewers_fanout_node()` in `app/graph.py`
- **Pydantic schemas:** All agent I/O defined in `app/schemas.py` (e.g., `ItemWriterResponse`, `BiasReviewResponse`)

### Integration Points
- Prompts live in `app/prompts/` and are loaded at runtime—changes don't require code modifications
- Item Writer prompt already references `request.constraints` for layering user constraints on baseline rules
- Bias Reviewer already outputs `ReviewComment` objects with `severity` field (1-5 scale) used by Critic for routing decisions
- Critic already has rule-based fallback logic in `app/agents/critic.py` if LLM call fails

</code_context>

<specifics>
## Specific Ideas

- Keep Item Writer's existing section structure (A: Construct fidelity, B: Wording, C: Keying, D: Bias pre-check) and add new principles within those sections
- Examples needed for: semantic diversity (show how to vary wording while maintaining construct meaning), intersectional bias (show how multiple identities interact)
- Research should extract crisp, actionable rules like "avoid vague quantifiers (often, sometimes, many) unless you anchor a clear time window" (already present) rather than abstract guidance like "ensure high quality"

</specifics>

<deferred>
## Deferred Ideas

None—discussion stayed within phase scope.

</deferred>

---

*Phase: 02-agent-architecture-optimization*
*Context gathered: 2026-03-08*
