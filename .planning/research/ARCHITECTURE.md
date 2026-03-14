# Architecture Research: v2.0 Psychometric Rigor Extensions

**Domain:** Multi-agent psychometric item generation with construct validation
**Researched:** 2026-03-14
**Confidence:** HIGH

## Executive Summary

This research addresses how to integrate three psychometric rigor features (synthetic inter-item correlations, instrument comparison, cross-construct analysis) into MAPIG's existing LangGraph state machine architecture. The analysis reveals that these features represent **post-finalize analytics** rather than item generation improvements, suggesting a new parallel branch architecture with minimal disruption to the existing validated workflow.

**Key finding:** All three features operate on finalized items, not draft items, making them ideal candidates for a **post-finalize analytics node** that runs after validation completes but before final output.

## Current Architecture Analysis

### Existing LangGraph Workflow

```
START → init_run → retrieve_node → item_writer_node
                                         ↓
                                    validation_node ←────────┐
                                         ↓                    │
                              ┌──────────┴─────────┐         │
                              ↓                    ↓         │
                      (accept: ≥7.0)    (reject: <7.0)      │
                              ↓                    ↓         │
                    reviewers_fanout_node  regenerate_items_node
                    (parallel: content,            │
                     linguistic, bias)             │
                              ↓                    │
                        critic_node                │
                              ↓                    │
                    ┌─────────┴──────────┐         │
                    ↓                    ↓         │
            (revise)                  (accept)     │
                    ↓                    ↓         │
            meta_editor_node ───────> finalize_node
                    │
                    └──> (loops back to reviewers_fanout_node)

                              finalize_node
                                   ↓
                                  END
```

### GraphState Schema

```python
class GraphState(TypedDict, total=False):
    # Inputs
    user_request: UserRequest
    thread_id: str
    run_id: str

    # Working artifacts
    evidence: List[EvidenceChunk]
    draft_items: List[DraftItem]
    linguistic_comments: List[ReviewComment]
    bias_comments: List[ReviewComment]
    content_comments: List[ReviewComment]
    revision_plan: Optional[RevisionPlan]
    validation_results: List[ItemValidation]

    # Control
    iteration: int
    stop_reason: str

    # Output
    final_output: FinalOutput
```

**Critical observation:** GraphState has no fields for comparison instruments, correlation matrices, or cross-construct analysis. These must be added.

## Recommended Integration Architecture

### Pattern: Post-Finalize Analytics Branch

**What:** Add new node after `finalize_node` but before `END` to compute psychometric analytics on finalized items.

**Why this pattern:**
1. **Separation of concerns**: Item generation workflow remains unchanged (validated in v1.1)
2. **Dependencies are met**: All three features require finalized items, not drafts
3. **Failure isolation**: Analytics failure doesn't break item generation
4. **Gradual rollout**: Can ship features incrementally (correlations → comparison → cross-construct)
5. **Performance**: Analytics can run in parallel using LangGraph's Send API

### Proposed Graph Structure

```
                    finalize_node
                         ↓
              psychometric_analytics_node
                         ↓
           ┌─────────────┼─────────────┐
           ↓             ↓             ↓
   correlation_node  comparison_node  cross_construct_node
   (synthetic        (find similar    (discriminant
    correlations)     instruments)     validity)
           ↓             ↓             ↓
           └─────────────┼─────────────┘
                         ↓
              analytics_aggregator_node
              (merge results into
               final_output)
                         ↓
                        END
```

**LangGraph implementation pattern:**

```python
def psychometric_analytics_node(state: GraphState) -> Command[Literal["analytics_aggregator_node"]]:
    """Fan out to parallel analytics branches using Send API."""
    from langgraph.types import Send

    # Send work to three parallel branches
    return Command(
        update={},
        goto=[
            Send("correlation_node", state),
            Send("comparison_node", state),
            Send("cross_construct_node", state),
        ]
    )

def analytics_aggregator_node(state: GraphState) -> GraphState:
    """Merge analytics results back into final_output."""
    final_output = state["final_output"]

    # Enrich FinalOutput with analytics
    enriched_output = final_output.model_copy(deep=True)
    enriched_output.correlation_matrix = state.get("correlation_matrix")
    enriched_output.comparison_instruments = state.get("comparison_instruments")
    enriched_output.cross_construct_analysis = state.get("cross_construct_analysis")

    return {"final_output": enriched_output}
```

**Reference:** [LangGraph parallel workflows](https://medium.com/@ameejais0999/parallel-workflows-in-langgraph-a-practical-approach-6e4340ceb8d4), [Map-reduce with Send API](https://medium.com/@astropomeai/implementing-map-reduce-with-langgraph-creating-flexible-branches-for-parallel-execution-b6dc44327c0e)

## Feature-Specific Integration Patterns

### Feature 1: Synthetic Inter-Item Correlation Matrix

**What:** Generate synthetic response data for finalized items and compute correlation matrix to assess internal consistency.

**Architecture decision:** NEW node (`correlation_node`)

**Why not enhance existing agent:** Correlations are computed on finalized items, not during generation. This is post-hoc analysis, not generative work.

**Implementation approach:**

```python
async def correlation_node(state: GraphState) -> GraphState:
    """Compute synthetic inter-item correlations."""
    final_items = state["final_output"].final_items
    user_request = state["user_request"]

    # Use LLM to generate synthetic responses
    # Research: LLMs can simulate respondents conditioned on demographics
    # Ref: "Silicon sampling" (LLMs simulate survey respondents)

    synthetic_responses = await generate_synthetic_responses(
        items=final_items,
        target_population=user_request.target_population,
        n_respondents=200,  # Common sample size for pilot testing
    )

    # Compute Pearson correlations
    correlation_matrix = compute_correlation_matrix(synthetic_responses)

    # Validate: adequate inter-item correlations (0.3-0.9 range)
    # Ref: Best practices show 0.3-0.9 is acceptable range

    return {
        "correlation_matrix": correlation_matrix,
        "synthetic_responses": synthetic_responses,  # Optional: for further analysis
    }
```

**Data flow:** `final_output.final_items` → LLM generates synthetic responses → compute Pearson correlations → store in GraphState

**Psychometric validation:**
- Inter-item correlations should be 0.3-0.9 (too low = items don't cohere, too high = redundancy)
- Research reference: [Best Practices for Developing and Validating Scales](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/)

**Model choice:** GPT-4o-mini for synthetic response generation (cheap, sufficient for numerical rating simulation)

**Confidence:** HIGH (established psychometric practice, LLM simulation validated in research)

### Feature 2: Instrument Comparison (Validated Scales)

**What:** Find published instruments measuring similar constructs and compare psychometric properties.

**Architecture decision:** ENHANCE Web Surfer agent OR NEW agent

**Two options:**

#### Option A: Enhance Web Surfer (Recommended)

**Pros:**
- Web Surfer already searches literature with domain filtering
- Perplexity integration already working
- Reuses existing prompt loading, evidence chunking patterns
- Minimal code duplication

**Cons:**
- Web Surfer currently runs pre-generation (retrieve_node)
- Would need to run twice: once for construct evidence, once for instrument comparison

**Implementation:**

```python
def comparison_node(state: GraphState) -> GraphState:
    """Find similar validated instruments for comparison."""
    from backend.agents.web_surfer import surf_for_instruments

    user_request = state["user_request"]

    # Specialized search query for instruments (not theoretical papers)
    instrument_query = UserRequest(
        construct_name=user_request.construct_name,
        construct_definition=user_request.construct_definition,
        # Custom query focus: instruments, not theory
        human_feedback="Find validated measurement instruments ONLY. List instrument name, authors, psychometric properties (reliability, validity). Do NOT quote items."
    )

    instruments = surf_for_instruments(instrument_query)

    return {
        "comparison_instruments": instruments,
    }
```

**Enhancement to Web Surfer:**
- Add `surf_for_instruments()` variant that modifies Perplexity query to prioritize:
  - Instrument names (e.g., "Beck Depression Inventory")
  - Psychometric properties (Cronbach's alpha, test-retest, CFA fit indices)
  - Validation studies
- Suppress item text retrieval (copyright concerns, not needed for comparison)

#### Option B: New Comparison Agent

**Pros:**
- Clean separation: Web Surfer = construct evidence, Comparison Agent = instrument discovery
- Can use different prompt strategy optimized for instrument metadata extraction
- Easier to track which agent found which evidence

**Cons:**
- Code duplication with Web Surfer (Perplexity API, evidence processing)
- Two agents doing similar search tasks

**Recommendation:** **Option A (enhance Web Surfer)** with conditional logic:
- If called from `retrieve_node` → search for construct evidence
- If called from `comparison_node` → search for validated instruments

**Psychometric comparison metrics:**

When comparing found instruments to generated items:
1. **Convergent validity:** Do items measure same construct? (correlation should be high if measuring same thing)
2. **Discriminant validity:** Do items differentiate from related constructs? (correlation should be low with different constructs)
3. **Criterion validity:** Comparison with established gold standards
4. **Fit indices:** CFA metrics (RMSEA ≤0.06, CFI ≥0.95, TLI ≥0.95)

**Reference:** [Psychometric comparison best practices](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/), [Discriminant validity assessment](https://journals.sagepub.com/doi/10.1177/1094428120968614)

**Confidence:** MEDIUM (established psychometric practice, but dynamic literature search adds complexity)

### Feature 3: Cross-Construct Comparison Analysis

**What:** Compare generated items to validated instruments measuring DIFFERENT but related constructs to assess discriminant validity.

**Architecture decision:** NEW node (`cross_construct_node`)

**Why not enhance comparison_node:** Different intent (discriminant vs convergent validity), different search strategy, different analysis.

**Implementation approach:**

```python
def cross_construct_node(state: GraphState) -> GraphState:
    """Assess discriminant validity via cross-construct comparison."""
    user_request = state["user_request"]
    final_items = state["final_output"].final_items

    # Use construct_exclusions field to guide search
    exclusions = user_request.construct_exclusions or ""

    # Search for instruments measuring RELATED but DISTINCT constructs
    related_constructs = identify_related_constructs(
        construct_name=user_request.construct_name,
        construct_definition=user_request.construct_definition,
        exclusions=exclusions,
    )

    # For each related construct, assess discriminant validity
    cross_construct_results = []
    for related in related_constructs:
        # Expected: LOW correlation (< 0.5 after correction for attenuation)
        # Ref: "Two measures intended to measure distinct constructs have
        #       discriminant validity if correlation after correcting for
        #       measurement error is low enough to be regarded as distinct"

        comparison = assess_discriminant_validity(
            our_items=final_items,
            related_construct=related,
        )
        cross_construct_results.append(comparison)

    return {
        "cross_construct_analysis": cross_construct_results,
    }
```

**Discriminant validity criteria:**
- Correlation < 0.85 (Fornell-Larcker criterion)
- Heterotrait-monotrait ratio (HTMT) < 0.85 (conservative) or < 0.90 (liberal)
- CFA comparison: Two-factor model fits better than one-factor model

**Reference:** [Updated guideline for assessing discriminant validity](https://journals.sagepub.com/doi/10.1177/1094428120968614)

**Confidence:** MEDIUM (established psychometric practice, but requires identifying appropriate comparison constructs)

## GPT-5.2 Reasoning Model Integration

### API Structure Differences

GPT-5.2 uses standard Chat Completions API but adds `reasoning.effort` parameter:

```python
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "user", "content": "Analyze construct validity"}
    ],
    reasoning_effort="high"  # NEW: none, low, medium, high, xhigh
)
```

**Reasoning effort levels:**
- `none` (default): Fast, low cost, minimal reasoning
- `low`: Light reasoning, ~1.5x cost
- `medium`: Moderate reasoning, ~2x cost
- `high`: Deep reasoning, ~3x cost
- `xhigh`: Maximum reasoning (Pro/Thinking only), ~5x cost

**Reference:** [GPT-5.2 API documentation](https://developers.openai.com/api/docs/models/gpt-5.2), [Reasoning effort parameter guide](https://www.nxcode.io/resources/news/gpt-5-4-api-developer-guide-reasoning-computer-use-2026)

### Where to Use GPT-5.2 in MAPIG

**Current model allocation:**
- Validator: Claude Opus 4.6 (highest accuracy)
- Other agents: Claude Sonnet 4.5 (cost-effective)
- Bias/Critic overrides: GPT-4o-mini (20x cheaper)

**Proposed GPT-5.2 integration:**

| Agent/Node | Current Model | GPT-5.2 Candidate? | Reasoning Effort | Rationale |
|------------|---------------|-------------------|------------------|-----------|
| Validator | Claude Opus 4.6 | ❌ No | N/A | Opus already excellent, well-tuned |
| Item Writer | Claude Sonnet 4.5 | ❌ No | N/A | Sonnet produces high-quality items |
| Correlation Node | GPT-4o-mini | ✅ Yes | `medium` | Numerical analysis benefits from reasoning |
| Comparison Node | Claude Sonnet | ✅ Maybe | `high` | Complex literature synthesis |
| Cross-Construct Node | Claude Sonnet | ✅ Yes | `high` | Discriminant validity requires deep reasoning |

**Implementation in llm_factory.py:**

```python
def get_chat_model_for_agent(
    agent_name: str,
    model_provider: str = "claude",
    use_chatgpt_critics: bool = False,
    reasoning_effort: Optional[str] = None,  # NEW parameter
) -> Union[ChatOpenAI, ChatAnthropic]:
    """Get LLM for specific agent with smart model allocation."""

    # GPT-5.2 reasoning model configuration
    GPT_5_2_AGENTS = {
        "correlation_node": "medium",      # Numerical analysis
        "cross_construct_node": "high",    # Deep reasoning for validity
        "comparison_node": "high",         # Complex synthesis
    }

    # Check if agent should use GPT-5.2 reasoning
    if agent_name in GPT_5_2_AGENTS:
        default_effort = GPT_5_2_AGENTS[agent_name]
        effort = reasoning_effort or default_effort
        return get_openai_chat_model(
            model="gpt-5.2",
            reasoning_effort=effort,
        )

    # Existing allocation logic...
```

**Configuration via UserRequest:**

Add field to enable GPT-5.2 for analytics:

```python
class UserRequest(BaseModel):
    # ... existing fields ...

    use_gpt5_analytics: bool = Field(
        default=False,
        description="Use GPT-5.2 reasoning model for psychometric analytics (higher cost, deeper analysis)"
    )

    reasoning_effort: Optional[Literal["none", "low", "medium", "high", "xhigh"]] = Field(
        default=None,
        description="GPT-5.2 reasoning effort level. If None, uses agent-specific defaults."
    )
```

**Cost implications:**

Assuming 200-item correlation analysis:
- GPT-4o-mini: ~$0.10 per run
- GPT-5.2 (medium effort): ~$0.30 per run (3x cost)
- GPT-5.2 (high effort): ~$0.50 per run (5x cost)

**Recommendation:** Default to GPT-4o-mini for correlation, offer GPT-5.2 as opt-in via UI toggle with cost warning.

**Confidence:** HIGH (API structure documented, integration pattern straightforward)

## GraphState Schema Extensions

### New Fields Required

```python
class GraphState(TypedDict, total=False):
    # ... existing fields ...

    # v2.0: Psychometric analytics
    correlation_matrix: Optional[CorrelationMatrix]
    synthetic_responses: Optional[List[SyntheticResponse]]
    comparison_instruments: Optional[List[ComparisonInstrument]]
    cross_construct_analysis: Optional[List[CrossConstructComparison]]
```

### New Pydantic Schemas

```python
class CorrelationMatrix(BaseModel):
    """Inter-item correlation matrix for internal consistency assessment."""

    model_config = ConfigDict(extra="forbid")

    item_count: int = Field(..., ge=2, description="Number of items in matrix")
    correlations: List[List[float]] = Field(
        ...,
        description="NxN matrix of Pearson correlations (symmetric)"
    )
    mean_correlation: float = Field(..., description="Average inter-item correlation")
    range_min: float = Field(..., description="Minimum correlation in matrix")
    range_max: float = Field(..., description="Maximum correlation in matrix")
    flags: List[str] = Field(
        default_factory=list,
        description="Quality flags (e.g., 'correlation_too_low', 'correlation_too_high')"
    )

class ComparisonInstrument(BaseModel):
    """Validated instrument measuring similar construct."""

    model_config = ConfigDict(extra="forbid")

    instrument_name: str = Field(..., description="Name of validated instrument")
    authors: str = Field(..., description="Instrument authors and year")
    construct_measured: str = Field(..., description="What construct it measures")
    reliability: Optional[float] = Field(
        default=None,
        description="Cronbach's alpha or similar reliability coefficient"
    )
    validity_evidence: str = Field(
        ...,
        description="Summary of validity evidence from literature"
    )
    source_url: str = Field(..., description="URL of source paper/documentation")
    comparison_type: Literal["convergent", "criterion"] = Field(
        ...,
        description="Type of validity comparison"
    )

class CrossConstructComparison(BaseModel):
    """Discriminant validity assessment vs related construct."""

    model_config = ConfigDict(extra="forbid")

    related_construct: str = Field(..., description="Name of related but distinct construct")
    relationship: str = Field(
        ...,
        description="How constructs are related (e.g., 'neighboring construct', 'facet of broader construct')"
    )
    expected_correlation: Literal["low", "moderate", "high"] = Field(
        ...,
        description="Expected correlation strength based on theory"
    )
    discriminant_validity: bool = Field(
        ...,
        description="True if constructs are empirically distinguishable"
    )
    evidence: str = Field(
        ...,
        description="Summary of discriminant validity evidence"
    )
```

### FinalOutput Schema Enhancement

```python
class FinalOutput(BaseModel):
    # ... existing fields ...

    # v2.0: Psychometric analytics
    correlation_matrix: Optional[CorrelationMatrix] = Field(
        default=None,
        description="Inter-item correlation matrix for internal consistency"
    )
    comparison_instruments: List[ComparisonInstrument] = Field(
        default_factory=list,
        description="Validated instruments measuring similar constructs"
    )
    cross_construct_analysis: List[CrossConstructComparison] = Field(
        default_factory=list,
        description="Discriminant validity assessment vs related constructs"
    )
```

## Build Order and Dependency Analysis

### Recommended Implementation Sequence

**Phase 1: Foundation (Week 1)**
1. Add GraphState schema extensions (CorrelationMatrix, ComparisonInstrument, CrossConstructComparison)
2. Add FinalOutput schema fields
3. Update graph builder with placeholder analytics nodes
4. Add GPT-5.2 support to llm_factory.py with reasoning.effort parameter
5. **Dependency:** None (foundational changes)

**Phase 2: Synthetic Correlations (Week 2)**
1. Implement `correlation_node` (synthetic response generation + Pearson correlation)
2. Integrate into graph: `finalize_node → correlation_node → END`
3. Add correlation display card to Results UI
4. **Dependency:** Phase 1 schemas
5. **Validation:** Correlations in 0.3-0.9 range for known-good scales

**Phase 3: Instrument Comparison (Week 3)**
1. Enhance Web Surfer with `surf_for_instruments()` variant
2. Implement `comparison_node` (literature search for validated instruments)
3. Add comparison instruments display to Results UI
4. **Dependency:** Phase 1 schemas, existing Web Surfer agent
5. **Validation:** Returns 3-5 relevant instruments for test constructs

**Phase 4: Cross-Construct Analysis (Week 4)**
1. Implement `cross_construct_node` (discriminant validity assessment)
2. Add cross-construct comparison display to Results UI
3. **Dependency:** Phase 3 (comparison_node provides related construct discovery)
4. **Validation:** Correctly identifies discriminant validity for test cases

**Phase 5: Parallel Analytics (Week 5)**
1. Refactor to parallel execution using Send API
2. Add `psychometric_analytics_node` fanout
3. Add `analytics_aggregator_node` to merge results
4. Update graph: `finalize_node → psychometric_analytics_node → [parallel branches] → analytics_aggregator_node → END`
5. **Dependency:** Phases 2, 3, 4 (all analytics nodes implemented)
6. **Validation:** Performance improvement (parallel vs sequential)

**Phase 6: GPT-5.2 Integration (Week 6)**
1. Add UI toggle for GPT-5.2 analytics (with cost warning)
2. Wire `use_gpt5_analytics` field through UserRequest
3. Add reasoning effort selector (none/low/medium/high/xhigh)
4. Update llm_factory to route analytics nodes to GPT-5.2 when enabled
5. **Dependency:** Phases 2-4 (analytics nodes exist)
6. **Validation:** A/B comparison (GPT-4o-mini vs GPT-5.2 high effort)

### Critical Path Dependencies

```
Phase 1 (schemas) → Phase 2, 3, 4 (can run in parallel)
Phases 2, 3, 4 → Phase 5 (parallel execution)
Phase 5 → Phase 6 (GPT-5.2 integration)
```

**Estimated timeline:** 6 weeks for full v2.0 psychometric rigor milestone

## Anti-Patterns to Avoid

### Anti-Pattern 1: Mixing Analytics into Existing Nodes

**What people do:** Add correlation computation to `finalize_node` or comparison logic to `retrieve_node`

**Why it's wrong:**
- Violates single responsibility principle
- Makes existing validated nodes more complex
- Harder to test, debug, and disable features
- Risk of breaking v1.1 production behavior

**Do this instead:** Create separate analytics nodes that run post-finalize

### Anti-Pattern 2: Running Analytics on Draft Items

**What people do:** Compute correlations or comparisons before validation completes

**Why it's wrong:**
- Draft items may fail validation and get regenerated
- Wastes API cost on analysis of items that might be discarded
- Correlation of low-quality items is meaningless

**Do this instead:** Only run analytics after `finalize_node` confirms items are ready

### Anti-Pattern 3: Blocking on Analytics Failures

**What people do:** Make analytics nodes required for successful generation

**Why it's wrong:**
- Analytics are enhancements, not requirements
- If Perplexity API fails, user shouldn't lose generated items
- Creates fragile dependency chain

**Do this instead:** Catch analytics errors gracefully, populate `None` values, allow generation to complete

### Anti-Pattern 4: Hardcoding Comparison Instruments

**What people do:** Maintain static list of instruments for each construct

**Why it's wrong:**
- Doesn't scale to new constructs
- Literature changes (new instruments published)
- Misses domain-specific instruments

**Do this instead:** Dynamic literature search via Web Surfer enhancement

### Anti-Pattern 5: Using Same Model for All Tasks

**What people do:** Use Opus for everything or GPT-5.2 xhigh for all analytics

**Why it's wrong:**
- Synthetic response generation doesn't need Opus-level reasoning
- GPT-5.2 xhigh costs 5x more with minimal quality gain for simple tasks
- Wastes budget that could fund more features

**Do this instead:** Task-specific model allocation (correlation=4o-mini, cross-construct=Sonnet/GPT-5.2 high)

## Integration Points with Existing System

### LangGraph Graph Builder

**File:** `backend/graph.py`

**Changes required:**

```python
def build_graph(checkpointer=None):
    """Build and compile the LangGraph workflow."""
    builder = StateGraph(GraphState)

    # ... existing nodes ...

    # v2.0: Psychometric analytics nodes
    builder.add_node("psychometric_analytics_node", psychometric_analytics_node)
    builder.add_node("correlation_node", correlation_node)
    builder.add_node("comparison_node", comparison_node)
    builder.add_node("cross_construct_node", cross_construct_node)
    builder.add_node("analytics_aggregator_node", analytics_aggregator_node)

    # ... existing edges ...

    # v2.0: Analytics branch (runs AFTER finalize, BEFORE END)
    # OLD: builder.add_edge("finalize_node", END)
    # NEW:
    builder.add_edge("finalize_node", "psychometric_analytics_node")
    # psychometric_analytics_node uses Command with Send for parallel fanout
    builder.add_edge("correlation_node", "analytics_aggregator_node")
    builder.add_edge("comparison_node", "analytics_aggregator_node")
    builder.add_edge("cross_construct_node", "analytics_aggregator_node")
    builder.add_edge("analytics_aggregator_node", END)

    return builder.compile(checkpointer=checkpointer)
```

### FastAPI Endpoints

**File:** `backend/main.py`

**No changes required** — streaming endpoint already emits events based on LangGraph state updates. New nodes will automatically emit SSE events.

**Optional enhancement:** Add analytics-specific event types:

```python
# In SSE streaming logic
if current_node == "correlation_node":
    yield f"data: {json.dumps({'type': 'analytics', 'analytics_type': 'correlation', 'status': 'running'})}\n\n"
```

### Frontend Results UI

**File:** `src/components/Results.tsx`

**New component needed:** `AnalyticsPanel.tsx`

```tsx
interface AnalyticsPanelProps {
  correlationMatrix?: CorrelationMatrix;
  comparisonInstruments?: ComparisonInstrument[];
  crossConstructAnalysis?: CrossConstructComparison[];
}

export function AnalyticsPanel({
  correlationMatrix,
  comparisonInstruments,
  crossConstructAnalysis
}: AnalyticsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Psychometric Analytics</CardTitle>
      </CardHeader>
      <CardContent>
        {correlationMatrix && <CorrelationHeatmap matrix={correlationMatrix} />}
        {comparisonInstruments && <InstrumentComparison instruments={comparisonInstruments} />}
        {crossConstructAnalysis && <DiscriminantValidityTable analysis={crossConstructAnalysis} />}
      </CardContent>
    </Card>
  );
}
```

**Integration point:** `Results.tsx` already displays `FinalOutput`. Add `<AnalyticsPanel>` below items table.

### Model Factory

**File:** `backend/agents/llm_factory.py`

**Enhancement required:**

```python
def get_openai_chat_model(
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None  # NEW
) -> ChatOpenAI:
    """Create OpenAI ChatOpenAI client with optional reasoning effort."""
    model_name = model or settings.OPENAI_MODEL

    kwargs = {
        "model": model_name,
        "api_key": settings.OPENAI_API_KEY,
        "temperature": 0.2,
        "max_retries": 3,
        "timeout": 60,
    }

    # GPT-5.2 reasoning effort configuration
    if model_name == "gpt-5.2" and reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort

    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL

    return ChatOpenAI(**kwargs)
```

## Sources

**LangGraph Architecture:**
- [Parallel workflows in LangGraph](https://medium.com/@ameejais0999/parallel-workflows-in-langgraph-a-practical-approach-6e4340ceb8d4)
- [LangGraph state machine branching logic](https://markaicode.com/langgraph-state-machine-branching-logic/)
- [Map-reduce with LangGraph Send API](https://medium.com/@astropomeai/implementing-map-reduce-with-langgraph-creating-flexible-branches-for-parallel-execution-b6dc44327c0e)
- [Scaling LangGraph: Parallelization and subgraphs](https://aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization)

**Psychometric Methods:**
- [Best practices for scale development and validation](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/)
- [Inter-item correlation in psychometric assessment](https://lhbikos.github.io/ReC_Psychometrics/ItemAnalSurvey.html)
- [Scale validation protocol (6-step R-based)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8133536/)
- [Updated guideline for assessing discriminant validity](https://journals.sagepub.com/doi/10.1177/1094428120968614)
- [Construct validity: New developments](https://pmc.ncbi.nlm.nih.gov/articles/PMC6754793/)

**GPT-5.2 Integration:**
- [GPT-5.2 API documentation](https://developers.openai.com/api/docs/models/gpt-5.2)
- [Using GPT-5.2 reasoning effort](https://platform.openai.com/docs/guides/latest-model)
- [GPT-5.4 API developer guide](https://www.nxcode.io/resources/news/gpt-5-4-api-developer-guide-reasoning-computer-use-2026)
- [Azure OpenAI reasoning models](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/reasoning?view=foundry-classic)

**Synthetic Data and LLM Simulation:**
- [LLMs for synthetic data: Silicon sampling](https://cjbarrie.github.io/GenAI_Soc/week07_silicon_sampling.html)
- [Utility analysis of synthetic data generation](https://pmc.ncbi.nlm.nih.gov/articles/PMC11969122/)

---

*Architecture research for: MAPIG v2.0 Psychometric Rigor*
*Researched: 2026-03-14*
