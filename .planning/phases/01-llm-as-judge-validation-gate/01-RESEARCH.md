# Phase 1: LLM-as-Judge Validation Gate - Research

**Researched:** 2026-03-08
**Domain:** LLM-as-judge validation, LangGraph conditional routing, psychometric construct validity
**Confidence:** HIGH

## Summary

Phase 1 implements an automated validation gate using Claude Opus as an LLM judge to score generated psychometric items across four weighted dimensions (correspondence 50%, distinctiveness 25%, clarity 15%, specificity 10%) immediately after the Item Writer agent completes. Items scoring below 7.0 are automatically rejected and regenerated up to 3 times before accepting the best-scoring version.

The validation agent uses chain-of-thought prompting with explicit reasoning before numeric scores, structured Pydantic output validation, and conditional routing in LangGraph to implement retry logic. This approach aligns with current best practices for LLM-as-judge systems and psychometric validation principles while maintaining the existing FastAPI + LangGraph + Next.js architecture.

**Primary recommendation:** Use Claude Opus for the validation agent with chain-of-thought prompting, weighted multi-dimensional scoring (1-10 scale), conditional edge routing for retry logic, and explicit rubric anchors per score level per dimension.

## Phase Requirements

<phase_requirements>
| ID | Description | Research Support |
|----|-------------|-----------------|
| VAL-01 | Validation agent executes immediately after Item Writer, before reviewers | LangGraph conditional edges enable post-writer routing; insert validation_node between item_writer_node and reviewers_fanout_node |
| VAL-02 | Multi-dimensional scoring (correspondence 50%, distinctiveness 25%, clarity 15%, specificity 10%) | Weighted rubric design is standard in psychometric assessment; implicit aggregation (LLM weighs internally) achieves higher accuracy than explicit weighted sums |
| VAL-03 | Chain-of-thought prompting with explicit reasoning before scores | CoT improves LLM judge correlation with human judgments from 0.51 to 0.66 (G-Eval study); provides debuggable reasoning trails |
| VAL-04 | 1-10 categorical scale with clear criterion definitions per level | Numeric scales with anchored definitions (rubrics) improve consistency; avoid continuous scales that lack concrete decision points |
| VAL-05 | Automatic rejection threshold ≥7.0 for item acceptance | Threshold-based routing via conditional edges; conservative cutoff ensures only high-quality items proceed |
| VAL-06 | Immediate retry logic (regenerate rejected items only, max 3 attempts) | LangGraph supports conditional loops with state tracking; regenerate individual items rather than entire set for efficiency |
| VAL-07 | Claude Opus model for validation agent (highest accuracy) | Opus 4.6 excels at deep reasoning and multi-step deduction tasks; Sonnet 4.6 sufficient for other agents (cost optimization) |
| VAL-08 | Validation scores and reasoning visible in results UI | Store validation results in GraphState; include in FinalOutput schema; render in Next.js results view |
| VAL-09 | Export validation metadata (all dimension scores, reasoning, attempt count) | Extend FinalOutput and AuditMetadata schemas to include validation_results array with per-item scores, reasoning, and retry metadata |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain-anthropic | 0.4.x+ | Anthropic Claude integration for LangChain | Official LangChain partner package for Claude API; supports Claude Opus 4.6 and Sonnet 4.6 models |
| anthropic | 0.84.0+ | Anthropic Python SDK | Official SDK released Feb 2026; supports 1M token context, beta features, streaming |
| langgraph | 1.0.6 | State machine orchestration | Already in use; conditional edges and retry policies for validation routing |
| pydantic | 2.12.5+ | Structured output validation | Already in use; ValidationError handling for retry logic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain-core | 1.2.8+ | LangChain base abstractions | Already in use; required for ChatAnthropic integration |
| langgraph-checkpoint-sqlite | 3.0.3 | State persistence | Already in use; maintain checkpointing across validation retries |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Claude Opus for validation | Sonnet 4.6 | 70% prefer Sonnet 4.6 over Opus 4.5 for general tasks, but validation requires deep reasoning where Opus excels; cost savings not worth accuracy loss on critical path |
| Anthropic SDK | OpenAI fallback | User-selectable fallback planned for Phase 3; Claude superior for complex reasoning tasks per project decisions |
| LangGraph conditional edges | Manual retry loops | Conditional edges provide built-in state management, checkpointing, and clean routing; manual loops harder to debug |

**Installation:**
```bash
poetry add langchain-anthropic@latest anthropic@latest
# OR
pip install langchain-anthropic>=0.4.0 anthropic>=0.84.0
```

## Architecture Patterns

### Recommended Project Structure
```
app/
├── agents/
│   ├── validator.py           # New validation agent
│   ├── llm_factory.py          # Update to support Claude models
│   └── prompts/
│       └── validator.md        # Validation rubric prompt
├── graph.py                    # Add validation_node, update routing
├── schemas.py                  # Extend with ValidationResult, ValidationScore
└── settings.py                 # Add CLAUDE_API_KEY, VALIDATOR_MODEL settings
```

### Pattern 1: Validation Node with Chain-of-Thought Scoring
**What:** LLM judge evaluates each item across 4 dimensions using explicit reasoning before numeric scores
**When to use:** Immediately after item_writer_node, before reviewers_fanout_node
**Example:**
```python
# Source: Research synthesis from LLM-as-judge best practices
from pydantic import BaseModel, Field
from typing import List

class DimensionScore(BaseModel):
    dimension: str  # correspondence, distinctiveness, clarity, specificity
    reasoning: str  # Chain-of-thought explanation BEFORE score
    score: int = Field(ge=1, le=10)  # 1-10 categorical scale

class ValidationResult(BaseModel):
    item_index: int
    item_text: str
    dimension_scores: List[DimensionScore]  # 4 dimensions
    weighted_score: float  # Computed: correspondence*0.5 + distinctiveness*0.25 + clarity*0.15 + specificity*0.1
    accept: bool  # True if weighted_score >= 7.0
    attempt: int  # 1-3

def validation_node(state: GraphState) -> GraphState:
    """Validate draft items with LLM-as-judge scoring."""
    with step("validation_node", state):
        draft_items = state.get("draft_items", [])
        results = []

        for idx, item in enumerate(draft_items):
            result = validate_item(
                item=item,
                user_request=state["user_request"],
                attempt=1
            )
            results.append(result)

        return {"validation_results": results}
```

### Pattern 2: Conditional Routing for Retry Logic
**What:** Use LangGraph conditional edges to route based on validation scores
**When to use:** After validation_node; route to regenerate_node if items failed, else proceed to reviewers
**Example:**
```python
# Source: LangGraph conditional edges documentation
from langgraph.types import Command
from typing import Literal

def route_after_validation(state: GraphState) -> Command[Literal["regenerate_node", "reviewers_fanout_node"]]:
    """Route based on validation results."""
    validation_results = state.get("validation_results", [])

    # Check if any items need regeneration
    failed_items = [r for r in validation_results if not r.accept]
    max_attempts = 3

    # Check if we've exhausted retries
    if failed_items:
        max_attempt = max(r.attempt for r in validation_results)
        if max_attempt < max_attempts:
            return Command(
                update={"retry_count": max_attempt + 1},
                goto="regenerate_node"
            )

    # All items passed or max retries exhausted
    return Command(goto="reviewers_fanout_node")

# In build_graph:
builder.add_conditional_edges(
    "validation_node",
    route_after_validation
)
```

### Pattern 3: Selective Item Regeneration
**What:** Regenerate only failed items, not entire set; merge with accepted items
**When to use:** In regenerate_node after validation failures
**Example:**
```python
# Source: LangGraph best practices for selective state updates
def regenerate_node(state: GraphState) -> GraphState:
    """Regenerate only items that failed validation."""
    with step("regenerate_node", state):
        validation_results = state.get("validation_results", [])
        draft_items = state.get("draft_items", [])

        # Identify failed items
        failed_indices = [r.item_index for r in validation_results if not r.accept]

        # Regenerate only failed items with validation feedback
        regenerated = regenerate_failed_items(
            user_request=state["user_request"],
            evidence=state.get("evidence", []),
            failed_indices=failed_indices,
            validation_feedback=[r for r in validation_results if not r.accept]
        )

        # Merge: keep accepted items, replace failed items
        merged_items = draft_items.copy()
        for idx, new_item in zip(failed_indices, regenerated):
            merged_items[idx] = new_item

        return {"draft_items": merged_items}
```

### Pattern 4: Claude Model Selection in LLM Factory
**What:** Add get_claude_chat_model() to support Opus and Sonnet models
**When to use:** For validation agent (Opus) and other agents (Sonnet)
**Example:**
```python
# Source: langchain-anthropic documentation
from langchain_anthropic import ChatAnthropic
from functools import lru_cache

@lru_cache(maxsize=2)
def get_claude_chat_model(model: str = "claude-opus-4-6") -> ChatAnthropic:
    """Create Claude chat model (Opus or Sonnet)."""
    if not settings.CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY required for Claude models")

    return ChatAnthropic(
        model=model,
        api_key=settings.CLAUDE_API_KEY,
        temperature=0.2,
        max_retries=3,
        timeout=60,
    )

def get_validator_model() -> ChatAnthropic:
    """Get validation model (always Opus for highest accuracy)."""
    return get_claude_chat_model(model="claude-opus-4-6")
```

### Pattern 5: Weighted Multi-Dimensional Rubric
**What:** Define 1-10 scale anchors for each dimension; use implicit weighting (LLM applies weights internally)
**When to use:** In validator.md prompt
**Example:**
```markdown
# Source: Psychometric validation principles + LLM-as-judge rubric design

## Scoring Instructions

Evaluate each item on FOUR dimensions. For each dimension:
1. First, write your reasoning (chain-of-thought)
2. Then, assign a score 1-10 using the rubric below

### Dimension 1: Correspondence (Weight: 50%)
**Definition:** Does the item content directly and accurately reflect the construct definition?

**Scale:**
- 10: Item perfectly captures core construct meaning; no ambiguity
- 9: Item strongly reflects construct with minor peripheral elements
- 7-8: Item reflects construct but includes some non-core content
- 5-6: Item partially reflects construct; significant non-core content
- 3-4: Item loosely related to construct; mostly measures something else
- 1-2: Item clearly measures different construct

### Dimension 2: Distinctiveness (Weight: 25%)
**Definition:** Is the item clearly about THIS construct rather than nearby constructs?

**Scale:**
- 10: Uniquely measures target construct; no plausible alternative interpretation
- 9: Strong specificity with minimal overlap with related constructs
- 7-8: Primarily target construct with minor overlap possible
- 5-6: Could measure target OR closely related construct
- 3-4: Likely measures related construct more than target
- 1-2: Clearly measures different construct (e.g., job satisfaction vs belonging)

### Dimension 3: Clarity (Weight: 15%)
**Definition:** Is the item unambiguous, concise, and comprehensible to the target population?

**Scale:**
- 10: Perfectly clear; single interpretation; appropriate reading level
- 9: Very clear with negligible ambiguity
- 7-8: Clear to most respondents; minor ambiguity possible
- 5-6: Some ambiguity or complexity; may confuse some respondents
- 3-4: Ambiguous wording or complex language; likely to confuse
- 1-2: Incomprehensible or multiple interpretations

### Dimension 4: Specificity (Weight: 10%)
**Definition:** Does the item avoid vague quantifiers and provide concrete referents?

**Scale:**
- 10: Completely concrete; no vague terms; clear behavioral referent
- 9: Mostly concrete with minimal abstraction
- 7-8: Concrete with minor vague elements (acceptable quantifiers)
- 5-6: Some vague quantifiers or abstract language
- 3-4: Multiple vague quantifiers; abstract without concrete anchor
- 1-2: Entirely abstract or filled with undefined terms

## Weighted Score Calculation
Weighted_Score = (Correspondence * 0.5) + (Distinctiveness * 0.25) + (Clarity * 0.15) + (Specificity * 0.10)

**Acceptance Threshold:** Weighted_Score >= 7.0
```

### Anti-Patterns to Avoid
- **Explicit weighted sums in prompt:** Research shows implicit aggregation (LLM applies weights internally after seeing scores) achieves better accuracy than asking LLM to compute weighted sums
- **Continuous scales (e.g., 1-10.5):** Use categorical integers 1-10 with clear rubric anchors per level
- **Regenerating entire item set:** Only regenerate failed items; preserve accepted items to avoid introducing new failures
- **Skipping chain-of-thought:** Reasoning before scoring improves reliability by 10-15% and provides audit trails
- **Position bias in scoring:** Randomize item order or use explicit debiasing instructions to avoid position effects

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry logic with state management | Custom retry loops in Python | LangGraph conditional edges with Command routing | LangGraph provides built-in checkpointing, state tracking, and debuggable routing; custom loops risk lost state and complex error handling |
| Structured LLM output validation | Manual JSON parsing + validation | Pydantic models + invoke_structured | Pydantic provides automatic validation, retry on ValidationError, and clear error messages; manual parsing fragile |
| Weighted scoring aggregation | Prompt LLM to compute weighted sums | Compute weights in Python after receiving dimension scores | Research shows implicit weighting (LLM sees scores, applies weights mentally) more accurate than explicit computation; Python computation is deterministic and debuggable |
| Exponential backoff for API errors | Custom sleep timers | Anthropic SDK built-in max_retries + retry-after header | SDK handles 429 rate limits, 500 server errors, and 529 overloaded errors with proper backoff; custom timers risk violating rate limits |

**Key insight:** LangGraph's conditional routing, Pydantic's structured validation, and Anthropic SDK's retry handling are battle-tested for exactly these patterns. Custom solutions introduce bugs, lose checkpointing, and miss edge cases (rate limits, validation errors, state persistence).

## Common Pitfalls

### Pitfall 1: Validation Creates Infinite Loop
**What goes wrong:** Validation rejects items, regeneration produces similar items, validation rejects again, cycle repeats
**Why it happens:** Regeneration prompt doesn't include validation feedback; LLM repeats same mistakes
**How to avoid:** Include validation reasoning in regeneration prompt; set max_attempts=3 hard limit; accept best-scoring items after max retries
**Warning signs:** State.iteration keeps incrementing; same items fail validation repeatedly; no convergence after 2-3 attempts

### Pitfall 2: Position Bias in Scoring
**What goes wrong:** LLM rates items differently based on position in list (first item scored higher, last item scored lower)
**Why it happens:** LLMs exhibit position bias; early items set mental anchor, later items compared to anchor
**How to avoid:** Randomize item order during validation (restore original order after); include explicit "evaluate each item independently" instruction
**Warning signs:** First items consistently score higher; validation scores correlate with position

### Pitfall 3: Validation Slower Than Item Generation
**What goes wrong:** Validation becomes bottleneck; total runtime doubles; users see "Validating..." step taking 30+ seconds
**Why it happens:** Validation prompt too long; evaluating all 4 dimensions for 10 items = 40 LLM calls if sequential; Opus has higher latency than Sonnet
**How to avoid:** Validate all items in single prompt (batch scoring); use structured output to get all 40 dimension scores in one response; consider parallel validation for large item sets (10+ items)
**Warning signs:** Validation node takes >20 seconds for 10 items; logs show sequential API calls

### Pitfall 4: Rubric Anchor Ambiguity
**What goes wrong:** LLM assigns inconsistent scores; same item gets score 7 on first attempt, score 5 on retry
**Why it happens:** Rubric levels lack concrete examples; "clearly reflects construct" is subjective without anchors
**How to avoid:** Include 2-3 example items per rubric level (few-shot learning); use comparative anchors ("better than level 6 because..."); test rubric consistency on pilot items
**Warning signs:** Validation scores vary widely across retries for same item; difficult to predict scores

### Pitfall 5: ValidationError Breaks Retry Policy
**What goes wrong:** Pydantic ValidationError raised; LangGraph retry policy doesn't trigger; node fails without retrying
**Why it happens:** Known LangGraph issue (#6027): retry policies not respected for ValidationError; only respected for generic exceptions
**How to avoid:** Catch ValidationError explicitly; log error details; return error state to trigger conditional edge routing instead of relying on retry_policy
**Warning signs:** ValidationError in logs; retry_policy configured but retries don't happen; node fails on first attempt

### Pitfall 6: Missing Weighted Score in UI
**What goes wrong:** Users see validation passed/failed but don't understand why; no transparency into dimension scores
**Why it happens:** Validation results stored in state but not passed to FinalOutput; UI only shows pass/fail boolean
**How to avoid:** Extend DraftItem schema to include optional validation_result field; include in FinalOutput; render dimension scores and reasoning in results table
**Warning signs:** User confusion about rejections; support requests asking "why was this rejected?"; no audit trail

## Code Examples

Verified patterns from official sources:

### Complete Validation Agent Implementation
```python
# Source: Synthesized from langchain-anthropic docs + LLM-as-judge best practices
from typing import List
from pydantic import BaseModel, Field
from app.agents.llm_utils import invoke_structured
from app.agents.llm_factory import get_validator_model
from app.agents.prompt_loader import load_prompt
from app.schemas import DraftItem, UserRequest

class DimensionScore(BaseModel):
    dimension: str
    reasoning: str  # Chain-of-thought BEFORE score
    score: int = Field(ge=1, le=10)

class ItemValidation(BaseModel):
    item_index: int
    item_text: str
    dimension_scores: List[DimensionScore]  # 4 dimensions
    weighted_score: float
    accept: bool  # True if weighted_score >= 7.0

class ValidationResponse(BaseModel):
    validations: List[ItemValidation]

def validate_items(
    request: UserRequest,
    items: List[DraftItem],
    attempt: int = 1
) -> ValidationResponse:
    """Validate all items using LLM-as-judge with chain-of-thought scoring."""

    system_prompt = load_prompt("validator.md")

    user_payload = {
        "construct_name": request.construct_name,
        "construct_definition": request.construct_definition,
        "items": [{"index": i, "text": item.item_text} for i, item in enumerate(items)],
        "attempt": attempt
    }

    messages = [
        ("system", system_prompt),
        ("human", f"Validate these items. Return ValidationResponse.\n\nINPUT:\n{user_payload}")
    ]

    # Use Claude Opus for highest accuracy
    model = get_validator_model()

    return invoke_structured(
        ValidationResponse,
        messages,
        model=model
    )
```

### Conditional Routing After Validation
```python
# Source: LangGraph conditional edges documentation
from langgraph.types import Command
from typing import Literal

def route_after_validation(
    state: GraphState
) -> Command[Literal["regenerate_items_node", "reviewers_fanout_node"]]:
    """Route to regeneration if items failed, else proceed to reviewers."""

    validation_results = state.get("validation_results", [])

    # Separate passed and failed items
    failed = [v for v in validation_results if not v.accept]

    if not failed:
        # All items passed
        return Command(goto="reviewers_fanout_node")

    # Check retry limit
    max_attempts = 3
    current_attempt = validation_results[0].attempt if validation_results else 1

    if current_attempt >= max_attempts:
        # Max retries exhausted; accept best available
        logger.warning(f"Validation max retries ({max_attempts}) exhausted. Accepting best-scoring items.")
        return Command(goto="reviewers_fanout_node")

    # Route to regeneration
    return Command(
        update={
            "validation_attempt": current_attempt + 1,
            "failed_item_indices": [v.item_index for v in failed]
        },
        goto="regenerate_items_node"
    )

# In build_graph():
builder.add_node("validation_node", validation_node)
builder.add_node("regenerate_items_node", regenerate_items_node)
builder.add_conditional_edges(
    "validation_node",
    route_after_validation
)
```

### Retry with Exponential Backoff (Anthropic SDK)
```python
# Source: Anthropic SDK documentation + best practices
from anthropic import Anthropic, APIError, RateLimitError
import time

def call_with_retry(client: Anthropic, messages: list, max_retries: int = 3):
    """Call Anthropic API with exponential backoff on errors."""

    for attempt in range(max_retries):
        try:
            return client.messages.create(
                model="claude-opus-4-6",
                messages=messages,
                max_tokens=4096
            )
        except RateLimitError as e:
            # 429: Respect retry-after header
            retry_after = getattr(e, 'retry_after', None) or 2 ** attempt
            logger.warning(f"Rate limit hit. Retrying after {retry_after}s")
            time.sleep(retry_after)
        except APIError as e:
            # 500/529: Exponential backoff
            if attempt == max_retries - 1:
                raise
            backoff = 2 ** attempt
            logger.warning(f"API error {e}. Retrying after {backoff}s")
            time.sleep(backoff)

    raise RuntimeError(f"Max retries ({max_retries}) exhausted")
```

### Updated Graph Structure
```python
# Source: LangGraph graph API documentation
def build_graph(checkpointer=None):
    """Build graph with validation gate between item_writer and reviewers."""

    builder = StateGraph(GraphState)

    # Existing nodes
    builder.add_node("init_run", init_run)
    builder.add_node("retrieve_node", retrieve_node)
    builder.add_node("item_writer_node", item_writer_node)

    # NEW: Validation gate
    builder.add_node("validation_node", validation_node)
    builder.add_node("regenerate_items_node", regenerate_items_node)

    # Existing review/revision nodes
    builder.add_node("reviewers_fanout_node", reviewers_fanout_node)
    builder.add_node("critic_node", critic_node)
    builder.add_node("meta_editor_node", meta_editor_node)
    builder.add_node("finalize_node", finalize_node)

    # Linear flow up to item writer
    builder.add_edge(START, "init_run")
    builder.add_edge("init_run", "retrieve_node")
    builder.add_edge("retrieve_node", "item_writer_node")

    # NEW: Validation gate BEFORE reviewers
    builder.add_edge("item_writer_node", "validation_node")
    builder.add_conditional_edges(
        "validation_node",
        route_after_validation  # Routes to regenerate_items_node OR reviewers_fanout_node
    )

    # Regeneration loops back to validation
    builder.add_edge("regenerate_items_node", "validation_node")

    # Existing review/revision flow
    builder.add_edge("reviewers_fanout_node", "critic_node")
    builder.add_edge("meta_editor_node", "reviewers_fanout_node")
    builder.add_edge("finalize_node", END)

    return builder.compile(checkpointer=checkpointer)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Embedding similarity for validation | LLM-as-judge with chain-of-thought | 2024-2025 | CoT improves human correlation from 0.51 to 0.66 (G-Eval); provides transparent reasoning |
| Single-dimension scoring | Multi-dimensional weighted rubrics | 2025+ | Rubric decomposition improves accuracy; catches items that pass overall but fail critical dimensions |
| Explicit weighted sums in prompt | Implicit aggregation (LLM mental weighting) | 2025+ | Implicit weighting achieves higher accuracy; LLMs struggle with arithmetic but excel at holistic judgment |
| Fixed retry delays | Retry-after header + exponential backoff | 2026 Anthropic SDK | Respects server-provided timing; reduces rate limit violations; faster recovery from transient errors |
| Claude 3.5 Sonnet for validation | Claude Opus 4.6 for validation | Feb 2026 | Opus 4.6 maintains coherence across long reasoning chains; critical for multi-step validation logic |

**Deprecated/outdated:**
- **SurveyBot3000 embedding approach:** Used cosine similarity for construct correspondence (r=0.59 correlation); replaced by LLM-as-judge (80%+ agreement with experts)
- **Single aggregate score:** Early LLM judge systems used single 1-5 score; replaced by multi-dimensional rubrics that surface specific failure modes
- **Regenerate entire item set on failure:** Inefficient; now regenerate only failed items to preserve accepted work

## Open Questions

1. **Optimal retry limit: 3 attempts vs 5 attempts?**
   - What we know: Research shows diminishing returns after 2-3 retries; LLMs struggle to fix fundamental construct misalignment through iteration alone
   - What's unclear: Whether 3 attempts is optimal for psychometric items specifically; no published data on item generation retry curves
   - Recommendation: Start with max_attempts=3; collect metrics (success rate by attempt number); adjust if data shows attempt 4-5 frequently succeed

2. **Should validation run in parallel or sequential?**
   - What we know: Single prompt with all items faster but risks truncation for large sets (10+ items); parallel validation adds overhead but scales better
   - What's unclear: Anthropic API rate limits for Opus; whether batch validation affects scoring consistency
   - Recommendation: Single-prompt batch validation for ≤10 items (Phase 1 scope); investigate parallel validation if future phases increase item_count

3. **Should validation feedback include dimension scores in regeneration prompt?**
   - What we know: Providing specific failure reasons improves iteration quality; too much information can confuse LLM
   - What's unclear: Whether showing numeric scores (e.g., "correspondence=5.2") helps or whether qualitative reasoning ("item too broad, includes social support") is better
   - Recommendation: Include reasoning text only (not numeric scores) in regeneration prompt; test with/without scores in Wave 0

4. **How to handle items that pass validation but fail human review?**
   - What we know: LLM-as-judge has 80% agreement with experts (not 100%); some items will pass validation but need human revision
   - What's unclear: Whether to tighten validation threshold (≥7.5 instead of ≥7.0) or accept that human reviewers catch remaining issues
   - Recommendation: Keep threshold at 7.0 for Phase 1; collect validation vs human review disagreement metrics in Phase 6 evaluation framework

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None — pytest auto-discovery |
| Quick run command | `pytest tests/test_validation.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-01 | Validation executes after Item Writer | integration | `pytest tests/test_graph.py::test_validation_placement -x` | ❌ Wave 0 |
| VAL-02 | Multi-dimensional scoring (4 dimensions) | unit | `pytest tests/test_validator.py::test_four_dimensions -x` | ❌ Wave 0 |
| VAL-03 | Chain-of-thought reasoning before scores | unit | `pytest tests/test_validator.py::test_cot_reasoning -x` | ❌ Wave 0 |
| VAL-04 | 1-10 scale with rubric anchors | unit | `pytest tests/test_validator.py::test_score_range -x` | ❌ Wave 0 |
| VAL-05 | Rejection threshold ≥7.0 | unit | `pytest tests/test_validator.py::test_rejection_threshold -x` | ❌ Wave 0 |
| VAL-06 | Retry logic max 3 attempts | integration | `pytest tests/test_graph.py::test_retry_limit -x` | ❌ Wave 0 |
| VAL-07 | Claude Opus model for validation | unit | `pytest tests/test_llm_factory.py::test_validator_uses_opus -x` | ❌ Wave 0 |
| VAL-08 | Validation scores visible in UI | e2e | `pytest tests/test_api.py::test_validation_in_response -x` | ❌ Wave 0 |
| VAL-09 | Export validation metadata | unit | `pytest tests/test_schemas.py::test_validation_export -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_validator.py -x` (unit tests for validator agent)
- **Per wave merge:** `pytest tests/ -v` (full suite including integration tests)
- **Phase gate:** Full suite green + manual smoke test in mock mode before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_validator.py` — covers VAL-02, VAL-03, VAL-04, VAL-05
- [ ] `tests/test_graph.py` — covers VAL-01, VAL-06 (integration tests for graph routing)
- [ ] `tests/test_llm_factory.py` — covers VAL-07 (Claude model selection)
- [ ] `tests/test_schemas.py` — covers VAL-09 (ValidationResult schema validation)
- [ ] `tests/test_api.py` — covers VAL-08 (API response includes validation_results)
- [ ] Framework install: Already installed (pytest 9.0.2 in pyproject.toml)

## Sources

### Primary (HIGH confidence)
- [LangGraph Conditional Edges Documentation](https://docs.langchain.com/oss/python/langgraph/graph-api) - Conditional routing patterns
- [langchain-anthropic Integration](https://docs.langchain.com/oss/python/integrations/chat/anthropic) - ChatAnthropic usage
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) - Official SDK, version 0.84.0
- [LLM-as-a-Judge: A Practical Guide](https://towardsdatascience.com/llm-as-a-judge-a-practical-guide/) - Rubric design principles
- [Current Concepts in Validity and Reliability for Psychometric Instruments](https://www.researchgate.net/publication/7331143_Current_Concepts_in_Validity_and_Reliability_for_Psychometric_Instruments_Theory_and_Application) - Construct validity framework

### Secondary (MEDIUM confidence)
- [LLM-As-Judge: 7 Best Practices & Evaluation Templates](https://www.montecarlodata.com/blog-llm-as-judge/) - Chain-of-thought improves reliability 10-15%
- [Evidence-Based Prompting Strategies for LLM-as-a-Judge](https://arize.com/blog/evidence-based-prompting-strategies-for-llm-as-a-judge-explanations-and-chain-of-thought/) - CoT improves correlation 0.51 to 0.66
- [Claude Sonnet vs Opus: Which Model Should You Actually Use in 2026?](https://www.sparkagents.com/blog/claude-sonnet-vs-opus) - Model selection guidance
- [How to Fix Claude API 429 Rate Limit Error](https://www.aifreeapi.com/en/posts/claude-api-429-error-fix) - Retry-after header usage
- [A Beginner's Guide to Handling Errors in LangGraph with Retry Policies](https://dev.to/aiengineering/a-beginners-guide-to-handling-errors-in-langgraph-with-retry-policies-h22) - Retry policy patterns
- [Rubric Evaluation: A Comprehensive Framework for Generative AI Assessment](https://encord.com/rubric-evaluation-generative-ai-assessment/) - Weighted scoring in rubrics
- [Psychometric Test Development for Certification Programs in 2026](https://oasis-lms.com/post/psychometric-test-development-a-complete-guide-for-certification-credentialing-programs-in-2026) - Item validation standards

### Tertiary (LOW confidence)
- [Node Retry Policies not respected for ValidationError](https://github.com/langchain-ai/langgraph/issues/6027) - Known LangGraph issue (unresolved as of search date)
- [Wikipedia: Psychometrics](https://en.wikipedia.org/wiki/Psychometrics) - General background only

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation for langchain-anthropic, Anthropic SDK, LangGraph verified
- Architecture: HIGH - Patterns validated against official LangGraph docs and LLM-as-judge best practices
- Pitfalls: MEDIUM - Based on documented issues (ValidationError retry bug) and common LLM-as-judge failure modes; specific psychometric validation pitfalls extrapolated from general principles

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (30 days - stable libraries and established patterns)
