# Phase 7: Foundation & Infrastructure - Research

**Researched:** 2026-03-14
**Domain:** LangGraph state schema extension, Pydantic v2 patterns, langchain-openai GPT-5.2 reasoning models, Python/TypeScript type safety
**Confidence:** MEDIUM-HIGH

## Summary

Phase 7 lays the foundation for v2.0 psychometric analytics by extending GraphState/FinalOutput schemas, integrating GPT-5.2 reasoning models, and creating analytics node placeholders. Research reveals established patterns for backward-compatible schema extension (Phase 3.1 precedent), emerging GPT-5.2 support in langchain-openai with known compatibility issues, and clear patterns for no-op placeholder nodes.

**Key findings:**
- **Schema extension pattern proven**: Phase 3.1 successfully used Optional fields with None defaults for backward-compatible FinalOutput extension — same pattern applies to v2.0 analytics fields
- **GPT-5.2 support available but evolving**: langchain-openai supports reasoning_effort parameter via dictionary format `{"effort": "high", "summary": "auto"}`, but GitHub issues (#32714, #29947, #32949) document max_completion_tokens and reasoning parameter compatibility problems requiring testing
- **Token tracking infrastructure exists**: _accumulate_tokens() pattern in graph.py ready to extend for gpt52_tokens_used counter with separate reasoning_tokens/output_tokens tracking
- **Test framework mature**: pytest with 19 existing test files, no pytest.ini (uses defaults), comprehensive schema validation tests provide strong foundation

**Primary recommendation:** Follow Phase 3.1 schema extension pattern exactly (Optional fields + Field(default=None) + default_factory=list), test langchain-openai upgrade to 2.x in isolation before integrating, create analytics nodes as simple pass-through functions with step() context manager for SSE events.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Correlation data model**: Rich cells (CorrelationCell with value, ci_low, ci_high, item_i_index, item_j_index), flat list structure (N*(N-1)/2 entries), aggregate metrics embedded (cronbachs_alpha, mean_inter_item_correlation, internal_consistency_flag), disclaimer field embedded defaulting to "LLM-estimated, not empirically validated"
- **GPT-5.2 reasoning integration**: reasoning_effort hardcoded to "high" for analytics tasks (not user-configurable), GPT-5.2 for analytics agents only (item writer/reviewers stay Claude), new gpt52_tokens_used counter in GraphState, track reasoning_tokens vs output_tokens separately
- **Analytics graph topology**: Placeholders sit after finalize_node before END, three separate nodes (correlation_node, comparison_node, cross_construct_node), sequential execution for Phase 7, emit SSE node_start/complete events
- **Export backward compatibility**: New FinalOutput fields use Optional with None defaults (Phase 3.1 pattern), correlation CSV as separate file (correlation_matrix.csv), JSON export includes full CorrelationMatrix object, TypeScript types updated in Phase 7

### Claude's Discretion
- Exact field names and Pydantic model structure for ComparisonInstrument and CrossConstructComparison types
- LLM factory caching strategy for GPT-5.2 (lru_cache adjustment for reasoning_effort parameter)
- No-op implementation details for analytics node placeholders
- SSE event naming conventions for analytics nodes
- Token tracking data structure for reasoning_tokens separation

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | GraphState schema extended with CorrelationMatrix, ComparisonInstrument, and CrossConstructComparison types | TypedDict extension pattern (total=False), Pydantic models with extra="forbid" |
| INFRA-02 | FinalOutput schema extended with correlation_matrix, comparison_instruments, and cross_construct_analysis fields | Phase 3.1 precedent: Optional fields with None defaults, backward compatibility proven |
| INFRA-05 | llm_factory.py supports reasoning_effort parameter for GPT-5.2 model allocation | langchain-openai reasoning parameter via dict format, caching strategy needs adjustment |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.12.5 | Schema validation and serialization | Already in use, ConfigDict(extra="forbid") pattern established, proven backward-compatible extension pattern from Phase 3.1 |
| typing_extensions | Bundled with Python 3.11+ | TypedDict for GraphState | LangGraph requires TypedDict for state schemas, total=False pattern for optional fields |
| langchain-openai | 1.1.7 → 2.x (upgrade needed) | OpenAI model integration with GPT-5.2 reasoning support | Official LangChain integration, supports reasoning parameter, but requires version upgrade and compatibility testing |
| langchain-anthropic | >=1.3.4 (current) | Claude integration | No changes needed, item writer and reviewers stay on Claude |
| pytest | 9.0.2 (current) | Test framework | 19 existing test files, comprehensive schema validation tests, no changes needed |

**Installation:**
```bash
# langchain-openai upgrade (test in isolation first)
poetry add langchain-openai@^2.0  # or specific 2.x version after testing

# No new dependencies needed (Pydantic, typing_extensions already present)
```

**Version upgrade risk:**
langchain-openai 1.1.7 → 2.x requires isolated testing due to documented GitHub issues with max_completion_tokens and reasoning parameter compatibility.

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── schemas.py              # Pydantic models (add CorrelationMatrix, ComparisonInstrument, CrossConstructComparison)
├── graph.py               # GraphState TypedDict extension + analytics nodes
├── agents/
│   └── llm_factory.py     # Add get_gpt52_analytics_model() function
└── tests/
    ├── test_schemas.py    # Add analytics schema tests (validation, serialization)
    ├── test_graph.py      # Add analytics node placeholder tests
    └── test_llm_factory.py # Add GPT-5.2 model allocation tests

src/lib/
└── types.ts               # Mirror new backend types for frontend type safety
```

### Pattern 1: Backward-Compatible Schema Extension (Proven in Phase 3.1)

**What:** Extend Pydantic BaseModel or TypedDict with new optional fields without breaking existing consumers

**When to use:** Adding analytics fields to FinalOutput and GraphState schemas

**Example (from Phase 3.1 test_schemas.py):**
```python
# Source: D:\GITHUB REPOS\lmaig-langgraph\tests\test_schemas.py, lines 199-234
class FinalOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    final_items: List[DraftItem]
    audit: AuditMetadata

    # Phase 03.1: Optional metadata for complete context export
    user_request: Optional[UserRequest] = Field(
        default=None,
        description="Original user request..."
    )

    linguistic_feedback: List[ReviewComment] = Field(
        default_factory=list,
        description="All linguistic reviewer comments..."
    )

# Backward compatibility test proves pattern works:
output = FinalOutput(final_items=[item], audit=audit)  # No new fields
assert output.user_request is None  # Defaults to None
assert output.linguistic_feedback == []  # Defaults to empty list
```

**Apply to Phase 7:**
```python
class FinalOutput(BaseModel):
    # ... existing fields ...

    # Phase 7: Analytics fields (v2.0)
    correlation_matrix: Optional["CorrelationMatrix"] = Field(
        default=None,
        description="Synthetic correlation matrix with Cronbach's alpha and confidence intervals"
    )

    comparison_instruments: List["ComparisonInstrument"] = Field(
        default_factory=list,
        description="Validated instruments measuring same/related constructs"
    )

    cross_construct_analysis: Optional["CrossConstructComparison"] = Field(
        default=None,
        description="Discriminant validity analysis against related-but-distinct constructs"
    )
```

**Key insight:** Optional fields with None defaults + List fields with default_factory=list preserve backward compatibility. Existing code that doesn't populate analytics fields continues to work unchanged.

### Pattern 2: TypedDict Extension with total=False

**What:** Extend LangGraph GraphState (TypedDict) with new optional keys

**When to use:** Adding analytics fields to GraphState for node communication

**Example (from backend/graph.py lines 113-143):**
```python
# Source: D:\GITHUB REPOS\lmaig-langgraph\backend\graph.py
class GraphState(TypedDict, total=False):
    # Existing fields
    user_request: UserRequest
    thread_id: str
    draft_items: List[DraftItem]

    # Cost tracking (Phase 3.1 addition)
    opus_tokens_used: int
    sonnet_tokens_used: int
    openai_tokens_used: int
    chatgpt_tokens_used: int

    # Output
    final_output: FinalOutput
```

**Apply to Phase 7:**
```python
class GraphState(TypedDict, total=False):
    # ... existing fields ...

    # Phase 7: Analytics state (v2.0)
    correlation_matrix: Optional[CorrelationMatrix]
    comparison_instruments: List[ComparisonInstrument]
    cross_construct_analysis: Optional[CrossConstructComparison]

    # Phase 7: GPT-5.2 token tracking
    gpt52_tokens_used: int
    gpt52_reasoning_tokens: int  # Separate counter for reasoning tokens
    gpt52_output_tokens: int     # Separate counter for output tokens
```

**Why total=False:** All keys are optional in TypedDict, nodes only populate fields they need. No initialization required.

### Pattern 3: Token Accumulation Extension

**What:** Extend _accumulate_tokens() function to track new model token usage

**When to use:** Adding GPT-5.2 token tracking to existing cost calculation infrastructure

**Example (from backend/graph.py lines 40-76):**
```python
# Source: D:\GITHUB REPOS\lmaig-langgraph\backend\graph.py
def _accumulate_tokens(state: GraphState, usage: TokenUsage) -> dict:
    """Accumulate token usage into appropriate GraphState counters."""
    model_name = usage.model_name.lower()
    opus_tokens = state.get("opus_tokens_used", 0)
    sonnet_tokens = state.get("sonnet_tokens_used", 0)
    openai_tokens = state.get("openai_tokens_used", 0)
    chatgpt_tokens = state.get("chatgpt_tokens_used", 0)

    if "opus" in model_name:
        opus_tokens += usage.total_tokens
    elif "sonnet" in model_name or "claude" in model_name:
        sonnet_tokens += usage.total_tokens
    # ... OpenAI routing ...

    return {
        "opus_tokens_used": opus_tokens,
        "sonnet_tokens_used": sonnet_tokens,
        # ...
    }
```

**Apply to Phase 7:**
```python
def _accumulate_tokens(state: GraphState, usage: TokenUsage) -> dict:
    # ... existing counters ...
    gpt52_tokens = state.get("gpt52_tokens_used", 0)
    gpt52_reasoning = state.get("gpt52_reasoning_tokens", 0)
    gpt52_output = state.get("gpt52_output_tokens", 0)

    # New routing for GPT-5.2 models
    if "gpt-5.2" in model_name or "gpt-5-nano" in model_name:
        gpt52_tokens += usage.total_tokens
        # Extract reasoning vs output tokens from usage metadata
        gpt52_reasoning += usage.reasoning_tokens  # Requires TokenUsage enhancement
        gpt52_output += usage.output_tokens

    return {
        # ... existing tokens ...
        "gpt52_tokens_used": gpt52_tokens,
        "gpt52_reasoning_tokens": gpt52_reasoning,
        "gpt52_output_tokens": gpt52_output,
    }
```

**Key insight:** Separate reasoning_tokens counter enables GPT-05 requirement (post-run audit breakdown) without future refactoring.

### Pattern 4: No-Op Placeholder Nodes

**What:** Create graph nodes that pass through state unchanged, emit SSE events for UX consistency

**When to use:** Phase 7 analytics placeholders (real implementation in Phases 8-9)

**Example (from backend/graph.py logging pattern lines 172-209):**
```python
# Source: D:\GITHUB REPOS\lmaig-langgraph\backend\graph.py
from backend.logging_utils import step

def init_run(state: GraphState) -> GraphState:
    """Initialize control fields."""
    with step("init_run", state):  # SSE event emission
        return {
            "iteration": 0,
            # ... field initialization ...
        }

def retrieve_node(state: GraphState) -> GraphState:
    with step("retrieve_node", state):
        resp = retrieve_evidence(state["user_request"])
        return {"evidence": list(resp.evidence)}
```

**Apply to Phase 7 (analytics placeholders):**
```python
def correlation_node(state: GraphState) -> GraphState:
    """Placeholder for correlation analysis (Phase 8 implementation).

    Phase 7: No-op pass-through, emits SSE events for frontend progress tracking.
    Phase 8: Implements CORR-01 through CORR-06 requirements.
    """
    with step("correlation_node", state):
        logger.info("Correlation analysis placeholder (Phase 8 implementation pending)")
        # No-op: return empty dict, state unchanged
        return {}

def comparison_node(state: GraphState) -> GraphState:
    """Placeholder for instrument comparison (Phase 9 implementation)."""
    with step("comparison_node", state):
        logger.info("Instrument comparison placeholder (Phase 9 implementation pending)")
        return {}

def cross_construct_node(state: GraphState) -> GraphState:
    """Placeholder for cross-construct analysis (Phase 9 implementation)."""
    with step("cross_construct_node", state):
        logger.info("Cross-construct analysis placeholder (Phase 9 implementation pending)")
        return {}
```

**Graph topology (Phase 7):**
```python
# In build_graph() function
builder.add_node("correlation_node", correlation_node)
builder.add_node("comparison_node", comparison_node)
builder.add_node("cross_construct_node", cross_construct_node)

# Sequential chain: finalize → correlation → comparison → cross_construct → END
builder.add_edge("finalize_node", "correlation_node")
builder.add_edge("correlation_node", "comparison_node")
builder.add_edge("comparison_node", "cross_construct_node")
builder.add_edge("cross_construct_node", END)
```

**Key insight:** step() context manager automatically emits node_start/node_complete SSE events. Placeholder nodes integrate seamlessly with existing progress tracking UX.

### Pattern 5: GPT-5.2 Reasoning Model Integration

**What:** Configure ChatOpenAI with reasoning parameter for GPT-5.2 models

**When to use:** Analytics agents requiring structured reasoning (correlation, comparison, cross-construct)

**Example (from web search - ChatOpenAI integration docs):**
```python
# Source: https://docs.langchain.com/oss/python/integrations/chat/openai
from langchain_openai import ChatOpenAI

# GPT-5.2 with reasoning parameter (dictionary format)
reasoning_config = {
    "effort": "high",      # 'low' | 'medium' | 'high' | 'xhigh' (GPT-5.2+)
    "summary": "auto",     # 'detailed' | 'auto' | None
}

llm = ChatOpenAI(
    model="gpt-5.2",
    reasoning=reasoning_config,
    max_completion_tokens=25000,  # Required for GPT-5+ (not max_tokens)
    output_version="responses/v1"  # Formats reasoning summaries in content field
)

# Extract reasoning from response
response = llm.invoke("Analyze correlation between items...")
for block in response.content:
    if block["type"] == "reasoning":
        for summary in block["summary"]:
            print(summary["text"])  # Reasoning summary
```

**Apply to Phase 7 (llm_factory.py):**
```python
def get_gpt52_analytics_model() -> ChatOpenAI:
    """Get GPT-5.2 reasoning model for analytics tasks.

    Returns:
        ChatOpenAI configured with high reasoning effort (hardcoded per user decision).

    Raises:
        ValueError: If OPENAI_API_KEY not configured
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY required for GPT-5.2 analytics")

    reasoning_config = {
        "effort": "high",    # Hardcoded per CONTEXT.md user decision
        "summary": "auto",   # Auto-select summary detail level
    }

    return ChatOpenAI(
        model="gpt-5.2",
        api_key=settings.OPENAI_API_KEY,
        reasoning=reasoning_config,
        max_completion_tokens=25000,
        temperature=0.2,
        max_retries=3,
        timeout=60,
        output_version="responses/v1"  # Enable reasoning summary extraction
    )

# Note: lru_cache NOT applied to get_gpt52_analytics_model because reasoning_config
# is constant (hardcoded "high"). Cache at module level if needed.
```

**Key insight:** reasoning parameter uses dictionary format (not string). max_completion_tokens required (max_tokens deprecated for GPT-5+). output_version="responses/v1" enables reasoning summary extraction.

### Anti-Patterns to Avoid

- **Breaking schema changes:** Adding required fields to FinalOutput breaks existing consumers. Always use Optional or default_factory.
- **Shared mutable defaults:** `Field(default=[])` creates shared reference across instances. Use `Field(default_factory=list)` (proven in Phase 3.1 test line 276).
- **Tight coupling of analytics nodes:** Don't make correlation_node depend on comparison_node state. Keep nodes independent for Phase 10 parallel execution upgrade.
- **max_tokens with GPT-5 models:** OpenAI deprecated max_tokens in favor of max_completion_tokens. Using max_tokens causes API errors.
- **String reasoning_effort:** reasoning parameter requires dictionary format `{"effort": "high"}`, not string "high".

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OpenAI reasoning model configuration | Custom reasoning_effort parameter handling | langchain-openai ChatOpenAI with reasoning dict parameter | Official integration handles API versioning, error handling, response parsing. Custom implementation risks breaking changes. |
| Token usage tracking | Custom token counter aggregation | Extend existing _accumulate_tokens() pattern | Infrastructure already handles multi-model tracking, cost calculation, per-1M-token pricing. Building separate system duplicates complexity. |
| Schema migration/versioning | Manual backward compatibility checks | Pydantic Optional fields + default_factory pattern | Pydantic validates at runtime, serializes cleanly, handles None/missing gracefully. Manual checks error-prone. |
| SSE event emission | Manual logging + event formatting | step() context manager from logging_utils | Automatic node_start/complete events, consistent format, error handling built-in. Reimplementing risks inconsistent UX. |
| Type validation for correlation cells | Custom range checks for correlation values | Pydantic Field validators with ge/le constraints | Pydantic provides declarative validation, clear error messages, JSON schema generation. Custom validators scatter validation logic. |

**Key insight:** Phase 7 is integration, not invention. Use proven patterns from Phase 3.1 (schema extension), existing infrastructure (_accumulate_tokens, step() context manager), and official library features (langchain-openai reasoning parameter).

## Common Pitfalls

### Pitfall 1: langchain-openai 2.x Compatibility Issues

**What goes wrong:** Upgrading langchain-openai from 1.1.7 to 2.x breaks existing agents due to max_completion_tokens parameter handling changes

**Why it happens:** GitHub issues (#29947, #32714, #32949) document that AzureChatOpenAI and ChatOpenAI have incompatible parameter handling between versions. max_tokens deprecated but max_completion_tokens not universally accepted.

**How to avoid:**
1. Test langchain-openai upgrade in isolated environment first
2. Run full test suite (pytest tests/) before integrating
3. Verify existing agents (item_writer, validator, reviewers) still work with 2.x
4. Keep fallback plan: pin langchain-openai==1.1.7 if upgrade breaks existing functionality

**Warning signs:**
- Validation errors mentioning "max_completion_tokens" or "max_tokens"
- API errors from OpenAI: "unsupported_parameter"
- Existing tests failing after langchain-openai upgrade

**Sources:**
- [GitHub Issue #32714](https://github.com/langchain-ai/langchain/issues/32714): AzureChatOpenAI doesn't accept reasoning parameter
- [GitHub Issue #29947](https://github.com/langchain-ai/langchain/issues/29947): AzureChatOpenAI reasoning models compatibility
- [GitHub Issue #32949](https://github.com/langchain-ai/langchain/issues/32949): Adding GPT-5 max_completion_tokens in AzureChatOpenAI

### Pitfall 2: Shared Mutable Defaults in Pydantic

**What goes wrong:** Using `Field(default=[])` causes all FinalOutput instances to share the same list reference, leading to data corruption

**Why it happens:** Python evaluates default arguments once at function definition time. Mutable defaults (list, dict) are shared across all calls.

**How to avoid:** Always use `Field(default_factory=list)` for List fields, `Field(default_factory=dict)` for Dict fields

**Warning signs:**
- Test failure: "Other instance unaffected (not shared reference)" (test_schemas.py line 276)
- Unexpected data appearing in FinalOutput instances
- Data from one generation appearing in another

**Proven solution (from Phase 3.1):**
```python
# WRONG (shared reference):
comparison_instruments: List[ComparisonInstrument] = Field(default=[])

# CORRECT (factory creates new list each time):
comparison_instruments: List[ComparisonInstrument] = Field(default_factory=list)
```

### Pitfall 3: TypedDict Forward References Without Quotes

**What goes wrong:** Using `correlation_matrix: CorrelationMatrix` in GraphState before CorrelationMatrix is defined causes NameError

**Why it happens:** Python evaluates type annotations at class definition time. TypedDict doesn't support forward references without quotes.

**How to avoid:** Use string quotes for forward references: `correlation_matrix: "CorrelationMatrix"`

**Warning signs:**
- NameError: name 'CorrelationMatrix' is not defined
- mypy/pyright type checking errors about undefined types

**Solution:**
```python
# Define Pydantic models first
class CorrelationMatrix(BaseModel):
    # ... fields ...

# Then reference in TypedDict with quotes
class GraphState(TypedDict, total=False):
    correlation_matrix: Optional["CorrelationMatrix"]  # String quote for forward ref
```

### Pitfall 4: GPT-5.2 Reasoning Tokens Not Tracked Separately

**What goes wrong:** Treating reasoning_tokens and output_tokens as single total_tokens counter prevents GPT-05 requirement (post-run audit breakdown)

**Why it happens:** Existing TokenUsage pattern only tracks total_tokens. GPT-5.2 reasoning models generate significant reasoning tokens (potentially 10-100x output tokens) that need separate tracking for cost transparency.

**How to avoid:**
1. Extend TokenUsage dataclass with reasoning_tokens and output_tokens fields
2. Extract reasoning token count from OpenAI response metadata
3. Store separately in GraphState (gpt52_reasoning_tokens, gpt52_output_tokens)
4. Display breakdown in audit metadata

**Warning signs:**
- User complaints about unexpectedly high GPT-5.2 costs
- Inability to explain cost breakdown (reasoning effort invisible)
- GPT-05 requirement (post-run audit) unmet

**Solution:**
```python
# Extend TokenUsage in agents/llm_utils.py
@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_name: str
    reasoning_tokens: int = 0  # New field for GPT-5.2

# Extract from OpenAI response
usage = response.usage_metadata
token_usage = TokenUsage(
    input_tokens=usage.get("input_tokens", 0),
    output_tokens=usage.get("output_tokens", 0),
    total_tokens=usage.get("total_tokens", 0),
    model_name=response.model,
    reasoning_tokens=usage.get("reasoning_tokens", 0)  # GPT-5.2 specific
)
```

### Pitfall 5: Breaking Existing v1.1 Workflow

**What goes wrong:** Analytics node placeholders accidentally modify state, breaking existing generation workflow

**Why it happens:** Returning non-empty dict from placeholder nodes can overwrite GraphState fields, causing downstream nodes to fail

**How to avoid:**
1. No-op nodes MUST return empty dict `return {}`
2. Add regression test: run existing test suite with analytics nodes enabled
3. Verify final_output unchanged when analytics disabled
4. Test SSE event stream doesn't cause frontend errors

**Warning signs:**
- Existing tests fail after adding analytics nodes
- final_output missing fields or has None values unexpectedly
- Frontend shows "generation failed" after analytics integration

**Solution:**
```python
def correlation_node(state: GraphState) -> GraphState:
    with step("correlation_node", state):
        logger.info("Correlation placeholder (no-op)")
        return {}  # Empty dict = no state modifications
```

**Regression test:**
```python
def test_analytics_placeholders_preserve_v1_workflow():
    """Phase 7: Analytics placeholders don't break existing generation."""
    from backend.graph import build_graph
    from backend.schemas import UserRequest

    graph = build_graph()
    result = graph.invoke({
        "user_request": UserRequest(...),
        # ... minimal state for generation ...
    })

    # Assert: final_output still populated correctly
    assert result["final_output"] is not None
    assert len(result["final_output"].final_items) > 0
    # Assert: analytics fields are None/empty (not populated by placeholders)
    assert result.get("correlation_matrix") is None
```

## Code Examples

Verified patterns from existing codebase and official documentation:

### TypedDict Extension with Optional Analytics Fields
```python
# Source: D:\GITHUB REPOS\lmaig-langgraph\backend\graph.py (extended)
from typing_extensions import TypedDict
from typing import Optional, List

class GraphState(TypedDict, total=False):
    # Existing v1.1 fields (unchanged)
    user_request: UserRequest
    thread_id: str
    draft_items: List[DraftItem]
    final_output: FinalOutput

    # Phase 7: Analytics state (v2.0)
    correlation_matrix: Optional["CorrelationMatrix"]
    comparison_instruments: List["ComparisonInstrument"]
    cross_construct_analysis: Optional["CrossConstructComparison"]

    # Phase 7: GPT-5.2 token tracking
    gpt52_tokens_used: int
    gpt52_reasoning_tokens: int
    gpt52_output_tokens: int
```

### Pydantic Schema with Nested Correlation Cells
```python
# Source: CONTEXT.md user decisions + Pydantic v2 patterns
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class CorrelationCell(BaseModel):
    """Single correlation with confidence interval."""
    model_config = ConfigDict(extra="forbid")

    item_i_index: int = Field(..., ge=0, description="First item index (0-based)")
    item_j_index: int = Field(..., ge=0, description="Second item index (0-based)")
    correlation: float = Field(..., ge=-1.0, le=1.0, description="Pearson correlation coefficient")
    ci_low: float = Field(..., ge=-1.0, le=1.0, description="95% CI lower bound")
    ci_high: float = Field(..., ge=-1.0, le=1.0, description="95% CI upper bound")

class CorrelationMatrix(BaseModel):
    """LLM-estimated correlation matrix with aggregate metrics."""
    model_config = ConfigDict(extra="forbid")

    cells: List[CorrelationCell] = Field(
        ...,
        description="Flat list of N*(N-1)/2 correlation cells (upper-triangular)"
    )

    # Aggregate metrics embedded directly (per user decision)
    cronbachs_alpha: float = Field(..., ge=0.0, le=1.0, description="Internal consistency estimate")
    mean_inter_item_correlation: float = Field(..., description="Average correlation across all item pairs")
    internal_consistency_flag: str = Field(
        ...,
        description="Assessment: 'excellent' (α≥0.90), 'good' (α≥0.80), 'acceptable' (α≥0.70), 'poor' (α<0.70)"
    )

    # Disclaimer embedded at data layer (enforces CORR-05)
    disclaimer: str = Field(
        default="LLM-estimated, not empirically validated",
        description="Warning that correlations are synthetic predictions, not observed data"
    )
```

### FinalOutput Extension (Phase 3.1 Pattern)
```python
# Source: D:\GITHUB REPOS\lmaig-langgraph\backend\schemas.py (extended)
class FinalOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    final_items: List[DraftItem]
    audit: AuditMetadata

    # Phase 03.1 fields (existing)
    user_request: Optional[UserRequest] = Field(default=None)
    linguistic_feedback: List[ReviewComment] = Field(default_factory=list)
    bias_feedback: List[ReviewComment] = Field(default_factory=list)
    content_feedback: List[ReviewComment] = Field(default_factory=list)

    # Phase 7: v2.0 analytics fields
    correlation_matrix: Optional[CorrelationMatrix] = Field(
        default=None,
        description="Synthetic correlation matrix with Cronbach's alpha and confidence intervals (CORR-01 through CORR-06)"
    )

    comparison_instruments: List[ComparisonInstrument] = Field(
        default_factory=list,
        description="Validated instruments measuring same construct for convergent validity (INST-01 through INST-06)"
    )

    cross_construct_analysis: Optional[CrossConstructComparison] = Field(
        default=None,
        description="Discriminant validity analysis against related-but-distinct constructs (XCON-01 through XCON-04)"
    )
```

### GPT-5.2 LLM Factory with Reasoning
```python
# Source: https://docs.langchain.com/oss/python/integrations/chat/openai + llm_factory.py pattern
from langchain_openai import ChatOpenAI
from backend.settings import settings

def get_gpt52_analytics_model() -> ChatOpenAI:
    """Get GPT-5.2 reasoning model for analytics tasks.

    Configured with hardcoded high reasoning effort per user decision (CONTEXT.md).
    Used by correlation_node, comparison_node, cross_construct_node in Phase 8-10.

    Returns:
        ChatOpenAI configured with GPT-5.2 and high reasoning effort

    Raises:
        ValueError: If OPENAI_API_KEY not configured

    Note: No lru_cache because reasoning_config is constant (hardcoded "high").
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY required for GPT-5.2 analytics")

    reasoning_config = {
        "effort": "high",    # Hardcoded per user decision (not configurable)
        "summary": "auto",   # Auto-select summary detail level
    }

    return ChatOpenAI(
        model="gpt-5.2",
        api_key=settings.OPENAI_API_KEY,
        reasoning=reasoning_config,
        max_completion_tokens=25000,
        temperature=0.2,
        max_retries=3,
        timeout=60,
        output_version="responses/v1"  # Enable reasoning summary extraction
    )

# Usage in analytics agents (Phase 8+):
# llm = get_gpt52_analytics_model()
# response = llm.invoke("Analyze correlation between items...")
```

### No-Op Analytics Node Placeholder
```python
# Source: D:\GITHUB REPOS\lmaig-langgraph\backend\graph.py pattern (extended)
from backend.logging_utils import step
import logging

logger = logging.getLogger("lmaig")

def correlation_node(state: GraphState) -> GraphState:
    """Placeholder for correlation analysis (Phase 8 implementation).

    Phase 7: No-op pass-through, emits SSE events for frontend progress tracking.
    Phase 8: Implements CORR-01 through CORR-06 requirements.

    Args:
        state: Current graph state with final_items

    Returns:
        Empty dict (no state modifications in Phase 7)
    """
    with step("correlation_node", state):
        logger.info("Correlation analysis placeholder (Phase 8 implementation pending)")
        # Phase 7: No-op, return empty dict
        # Phase 8: Will return {"correlation_matrix": CorrelationMatrix(...)}
        return {}

# Graph builder integration:
def build_graph(checkpointer=None):
    builder = StateGraph(GraphState)

    # ... existing nodes ...
    builder.add_node("finalize_node", finalize_node)

    # Phase 7: Analytics placeholders
    builder.add_node("correlation_node", correlation_node)
    builder.add_node("comparison_node", comparison_node)
    builder.add_node("cross_construct_node", cross_construct_node)

    # Sequential chain: finalize → correlation → comparison → cross_construct → END
    builder.add_edge("finalize_node", "correlation_node")
    builder.add_edge("correlation_node", "comparison_node")
    builder.add_edge("comparison_node", "cross_construct_node")
    builder.add_edge("cross_construct_node", END)

    return builder.compile(checkpointer=checkpointer)
```

### Token Tracking Extension
```python
# Source: D:\GITHUB REPOS\lmaig-langgraph\backend\graph.py lines 40-76 (extended)
def _accumulate_tokens(state: GraphState, usage: TokenUsage) -> dict:
    """Accumulate token usage into appropriate GraphState counters.

    Phase 7 extension: Adds GPT-5.2 tracking with separate reasoning/output tokens.

    Args:
        state: Current graph state
        usage: Token usage from LLM call (enhanced with reasoning_tokens field)

    Returns:
        Dict with updated token counters
    """
    model_name = usage.model_name.lower()

    # Existing counters
    opus_tokens = state.get("opus_tokens_used", 0)
    sonnet_tokens = state.get("sonnet_tokens_used", 0)
    openai_tokens = state.get("openai_tokens_used", 0)
    chatgpt_tokens = state.get("chatgpt_tokens_used", 0)

    # Phase 7: GPT-5.2 counters
    gpt52_tokens = state.get("gpt52_tokens_used", 0)
    gpt52_reasoning = state.get("gpt52_reasoning_tokens", 0)
    gpt52_output = state.get("gpt52_output_tokens", 0)

    # Existing routing (unchanged)
    if "opus" in model_name:
        opus_tokens += usage.total_tokens
    elif "sonnet" in model_name or "claude" in model_name:
        sonnet_tokens += usage.total_tokens
    elif "gpt-4o" in model_name and "mini" not in model_name:
        chatgpt_tokens += usage.total_tokens
    elif "gpt" in model_name or "openai" in model_name:
        openai_tokens += usage.total_tokens

    # Phase 7: GPT-5.2 routing
    if "gpt-5.2" in model_name or "gpt-5-nano" in model_name:
        gpt52_tokens += usage.total_tokens
        gpt52_reasoning += getattr(usage, "reasoning_tokens", 0)  # Separate tracking
        gpt52_output += getattr(usage, "output_tokens", 0)
    else:
        # Unknown model - add to sonnet as fallback
        sonnet_tokens += usage.total_tokens

    return {
        "opus_tokens_used": opus_tokens,
        "sonnet_tokens_used": sonnet_tokens,
        "openai_tokens_used": openai_tokens,
        "chatgpt_tokens_used": chatgpt_tokens,
        # Phase 7: GPT-5.2 counters
        "gpt52_tokens_used": gpt52_tokens,
        "gpt52_reasoning_tokens": gpt52_reasoning,
        "gpt52_output_tokens": gpt52_output,
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| langchain-openai 1.1.7 with basic ChatOpenAI | langchain-openai 2.x with reasoning parameter support for GPT-5+ models | Late 2025 (GPT-5 release) | Enables reasoning models (GPT-5.2, GPT-5.3) with configurable reasoning effort. Breaking change: max_tokens → max_completion_tokens. |
| Single token counter (total_tokens) | Separate reasoning_tokens and output_tokens tracking | GPT-5 release (2025) | Transparency for reasoning token costs (10-100x multiplier). Required for GPT-05 audit requirement. |
| Manual schema versioning | Pydantic Optional fields with defaults for backward compatibility | Pydantic v2 (2023+) | Declarative backward compatibility. No manual migration logic needed. |
| Nested 2D correlation matrix arrays | Flat list of correlation cells with explicit indices | Modern data science practice | JSON serialization, easier database storage, avoids nested array complexity. |

**Deprecated/outdated:**
- **max_tokens parameter**: OpenAI deprecated in favor of max_completion_tokens for GPT-5+ models (causes "unsupported_parameter" errors)
- **String reasoning_effort**: Early GPT-5 implementations used string parameter; current API requires dictionary format `{"effort": "high", "summary": "auto"}`
- **Shared correlation matrix across states**: Old pattern stored single matrix globally; v2.0 embeds in FinalOutput for per-run isolation

## Open Questions

1. **langchain-openai 2.x stable version identification**
   - What we know: Version 2.x required for GPT-5.2 support, but GitHub issues show compatibility problems
   - What's unclear: Which specific 2.x version is stable and compatible with existing langchain-anthropic 1.3.4+
   - Recommendation: Test with latest 2.x release in isolated environment, fall back to 1.1.7 if tests fail. Document tested version in pyproject.toml with explicit pin.

2. **Reasoning token extraction from OpenAI response**
   - What we know: GPT-5.2 generates reasoning tokens separately from output tokens, accessible via response metadata
   - What's unclear: Exact field name in ChatOpenAI response object (usage_metadata["reasoning_tokens"]? response.usage.reasoning_tokens?)
   - Recommendation: Log full response object structure during GPT-5.2 testing, identify reasoning token field, update TokenUsage extraction accordingly.

3. **ComparisonInstrument and CrossConstructComparison schema design**
   - What we know: User decisions specify high-level requirements (INST-01 through INST-06, XCON-01 through XCON-04)
   - What's unclear: Exact field names, nested structure for instrument metadata, citation format
   - Recommendation: Design schemas in Phase 7 Wave 0, validate with stakeholders before implementation. Claude's discretion per CONTEXT.md.

4. **Frontend TypeScript type generation strategy**
   - What we know: src/lib/types.ts must mirror backend schema changes for type safety
   - What's unclear: Manual sync vs automated generation (e.g., pydantic-to-typescript tool)
   - Recommendation: Phase 7 uses manual sync (proven in Phase 3.1). Defer automation to future work if maintenance burden increases.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none — uses pytest defaults (autodiscovery from tests/ directory) |
| Quick run command | `pytest tests/test_schemas.py tests/test_graph.py tests/test_llm_factory.py -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | GraphState accepts CorrelationMatrix, ComparisonInstrument, CrossConstructComparison types | unit | `pytest tests/test_graph.py::test_graphstate_analytics_fields -x` | ❌ Wave 0 |
| INFRA-01 | Pydantic models validate field constraints (correlation -1 to 1, ci bounds, etc.) | unit | `pytest tests/test_schemas.py::test_correlation_matrix_validation -x` | ❌ Wave 0 |
| INFRA-02 | FinalOutput serializes with analytics fields as None/empty (backward compatibility) | unit | `pytest tests/test_schemas.py::test_finaloutput_analytics_backward_compat -x` | ❌ Wave 0 |
| INFRA-02 | FinalOutput serializes with populated analytics fields (forward compatibility) | unit | `pytest tests/test_schemas.py::test_finaloutput_analytics_populated -x` | ❌ Wave 0 |
| INFRA-05 | get_gpt52_analytics_model() returns ChatOpenAI with reasoning config | unit | `pytest tests/test_llm_factory.py::test_gpt52_analytics_model_config -x` | ❌ Wave 0 |
| INFRA-05 | Token accumulation tracks gpt52_tokens_used, gpt52_reasoning_tokens, gpt52_output_tokens | unit | `pytest tests/test_graph.py::test_accumulate_tokens_gpt52 -x` | ❌ Wave 0 |
| ALL | Analytics placeholders preserve v1.1 workflow (regression test) | integration | `pytest tests/test_graph.py::test_analytics_placeholders_no_op -x` | ❌ Wave 0 |
| ALL | Existing v1.1 test suite passes with Phase 7 changes | regression | `pytest tests/ -x` | ✅ (19 existing files) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_schemas.py tests/test_graph.py tests/test_llm_factory.py -x` (fast subset, ~5-10s)
- **Per wave merge:** `pytest tests/` (full suite, ~30-60s)
- **Phase gate:** Full suite green + manual smoke test (generate 5 items via UI) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_schemas.py::test_correlation_matrix_validation` — covers INFRA-01 (Pydantic validation)
- [ ] `tests/test_schemas.py::test_finaloutput_analytics_backward_compat` — covers INFRA-02 (backward compatibility)
- [ ] `tests/test_schemas.py::test_finaloutput_analytics_populated` — covers INFRA-02 (forward compatibility)
- [ ] `tests/test_graph.py::test_graphstate_analytics_fields` — covers INFRA-01 (TypedDict extension)
- [ ] `tests/test_graph.py::test_accumulate_tokens_gpt52` — covers INFRA-05 (token tracking)
- [ ] `tests/test_graph.py::test_analytics_placeholders_no_op` — covers ALL (regression test)
- [ ] `tests/test_llm_factory.py::test_gpt52_analytics_model_config` — covers INFRA-05 (GPT-5.2 model factory)
- [ ] Framework install: Already installed (pytest 9.0.2 in pyproject.toml)

## Sources

### Primary (HIGH confidence)
- D:\GITHUB REPOS\lmaig-langgraph\backend\graph.py — Existing GraphState pattern, _accumulate_tokens() implementation, step() context manager usage
- D:\GITHUB REPOS\lmaig-langgraph\backend\schemas.py — FinalOutput schema, Phase 3.1 extension pattern, ConfigDict(extra="forbid") usage
- D:\GITHUB REPOS\lmaig-langgraph\tests\test_schemas.py — Backward compatibility tests (lines 199-234), mutable defaults test (line 276)
- D:\GITHUB REPOS\lmaig-langgraph\backend\agents\llm_factory.py — LLM factory pattern, lru_cache usage, agent-based model routing
- D:\GITHUB REPOS\lmaig-langgraph\.planning\phases\07-foundation-infrastructure\07-CONTEXT.md — User decisions, locked constraints, Claude's discretion areas

### Secondary (MEDIUM confidence)
- [ChatOpenAI integration - LangChain Docs](https://docs.langchain.com/oss/python/integrations/chat/openai) — reasoning parameter dictionary format, output_version configuration
- [Pydantic Models - Pydantic Validation](https://docs.pydantic.dev/latest/concepts/models/) — ConfigDict usage, extra="forbid" validation
- [Pydantic Fields - Pydantic Validation](https://docs.pydantic.dev/latest/concepts/fields/) — Field validators, default_factory pattern
- [LangChain Changelog](https://changelog.langchain.com/) — GPT-5.2 support announcements, version history

### Tertiary (LOW confidence — requires verification)
- [GitHub Issue #32714](https://github.com/langchain-ai/langchain/issues/32714) — AzureChatOpenAI reasoning parameter issues (marked for Phase 7 testing)
- [GitHub Issue #29947](https://github.com/langchain-ai/langchain/issues/29947) — AzureChatOpenAI reasoning models compatibility (marked for Phase 7 testing)
- [GitHub Issue #32949](https://github.com/langchain-ai/langchain/issues/32949) — GPT-5 max_completion_tokens issues (marked for Phase 7 testing)
- [Reasoning_effort parameter not working - LangChain Forum](https://forum.langchain.com/t/reasoning-effort-parameter-not-working-with-gpt-5-2-in-playground/3069) — Community reports of reasoning parameter issues (requires verification)

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM-HIGH — Pydantic/pytest proven in codebase, langchain-openai 2.x upgrade needs testing
- Architecture: HIGH — Phase 3.1 precedent provides proven pattern, TypedDict extension well-documented
- Pitfalls: MEDIUM — GitHub issues document problems but specific versions/fixes unclear, needs testing
- GPT-5.2 integration: MEDIUM — Official docs confirm reasoning parameter support, but compatibility issues require isolated testing

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days — langchain-openai 2.x evolving rapidly, revalidate if delayed)
