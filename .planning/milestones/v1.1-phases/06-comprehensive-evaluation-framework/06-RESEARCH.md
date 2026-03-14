# Phase 6: Comprehensive Evaluation Framework - Research

**Researched:** 2026-03-09
**Domain:** LLM-as-judge evaluation frameworks, psychometric validation metrics, agent workflow assessment
**Confidence:** HIGH

## Summary

Comprehensive evaluation of psychometric item generation requires a multi-dimensional assessment framework spanning item quality, agent performance, workflow efficiency, and construct validity. The research establishes that modern LLM-as-judge evaluation achieves 85% alignment with human judgment (exceeding 81% human-to-human agreement), making it suitable for automated validation of generated items against published scales.

The evaluation architecture should leverage existing MAPIG infrastructure: the proven LLM-as-judge validation pattern (already implemented in validator.py), Web Surfer agent for benchmark scale selection, and Next.js dashboard components (GeneratedItemsTable, EvidenceAuditPanel patterns). Five benchmark constructs across psychological domains (personality, clinical, social, organizational, attitudes) provide sufficient coverage while keeping evaluation runtime under 5 minutes.

**Primary recommendation:** Build automated evaluation suite with LLM-as-judge comparison of generated items to published scale items, using 4 evaluation dimensions (quality parity, construct fidelity, stylistic similarity, psychometric properties). Present results in dashboard UI with aggregated metrics per dimension, reusing existing Next.js component patterns and Pydantic structured output from validation agent.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Evaluation Dimensions:**
- All 4 dimensions equally weighted (no prioritization):
  1. Item quality (clarity, bias, construct validity scores)
  2. Agent performance (accuracy, reliability per agent)
  3. Workflow metrics (total time, iteration count, acceptance rate)
  4. Construct validity (correspondence scores, distinctiveness)
- Comprehensive evaluation matching roadmap success criteria

**Results Presentation:**
- Dashboard UI (web interface with visualization)
- Reuse existing Next.js components (GeneratedItemsTable, EvidenceAuditPanel patterns)
- Aggregated summary metrics (high-level scores per dimension: "Item Quality: 8.2/10")
- No per-agent breakdowns or per-construct drill-downs in v1 (keep simple)
- Dashboard accessible from main app (new route or tab)

**Baseline for ≥15% Improvement:**
- Compare current v1.0 (with LLM-as-judge validation) vs pre-v1.0 system (without validation gate)
- Simple A/B comparison: system with validation gate vs system without
- Demonstrates value of v1.0 optimization work

**Benchmark Construct Sourcing:**
- Use published scales (5 well-validated scales across domains)
- Web Surfer agent finds scales via Perplexity academic search
- Selection criteria: (1) High citation count, (2) Open access/public domain, (3) Established validity evidence
- 5 items per construct (25 total items, ~2-5 min runtime)
- Web Surfer outputs scale metadata: name, author, year, domain, sample items

**AI-Based Comparison (Not Human Experts):**
- LLM-as-judge comparison using Claude Opus
- Same pattern as current validation gate (proven approach)
- 4 comparison criteria:
  1. Quality parity (clarity, precision, readability)
  2. Construct fidelity (measures same construct effectively)
  3. Stylistic similarity (tone, format, style match)
  4. Psychometric properties (difficulty, discrimination, bias)
- Each criterion scored 1-10 with reasoning (structured output)

### Claude's Discretion

- Comparison results presentation format (aggregate scores vs per-item cards vs summary+drill-down)
- Dashboard UI design and component structure
- How to run pre-v1.0 baseline comparison (disable validation gate, regenerate items)
- Metrics aggregation formulas (how to combine scores across constructs)
- Dashboard routing and navigation integration

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EVAL-01 | Automated evaluation suite runs on demand | Backend endpoint pattern + pytest integration for trigger mechanism |
| EVAL-02 | Reports across 4 dimensions (item quality, agent performance, workflow, construct validity) | Multi-dimensional evaluation framework with aggregated metrics per dimension |
| EVAL-03 | 5 benchmark constructs (personality, clinical, social, organizational, attitudes) | Published scales identified (NEO-PI-R, PHQ-9/GAD-7, JSS, domain-specific scales) |
| EVAL-04 | Test cases for each benchmark | 5 items per scale = 25 test cases, Web Surfer agent sources metadata |
| EVAL-05 | Generated items compared to published scales | LLM-as-judge 4-criteria comparison (quality, fidelity, style, psychometric) |
| EVAL-06 | Documented comparison results | Structured output with scores + reasoning, dashboard visualization |
| EVAL-07 | ≥15% improvement vs baseline demonstrated | A/B comparison: v1.0 (with validation) vs pre-v1.0 (without validation) |
| EVAL-08 | Success criteria documented | Dashboard displays improvement metrics and comparison results |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test framework, evaluation suite runner | Already in project, TDD established pattern from Phase 1-5 |
| Pydantic | 2.12.5 | Structured output schemas for eval results | Existing validation pattern, type-safe, proven in validator.py |
| FastAPI | 0.128.0 | Backend endpoint for eval suite trigger | Existing backend framework, reuse API patterns |
| Next.js | 14 | Dashboard UI framework | Existing frontend, App Router, component reuse |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn/ui | Current | Dashboard components | Reuse InsetPanel, SurfaceCard, CardContent patterns |
| TanStack Query | Current | API state management | If dashboard needs real-time eval status polling |
| langchain-anthropic | ≥1.3.4 | Claude Opus LLM-as-judge | Comparison scoring, proven validator pattern |
| httpx | 0.28.1 | Perplexity API for scale sourcing | Web Surfer agent already uses for academic search |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LLM-as-judge | Human expert comparison | LLM: 85% accuracy, automated, fast. Human: 81% agreement, slow, expensive |
| Pytest + custom endpoint | Dedicated eval framework (e.g., LangSmith) | Pytest: simple, in-project. LangSmith: richer features, external dependency |
| Aggregated metrics only | Per-agent drill-down dashboards | Aggregated: simpler v1 implementation. Drill-down: deferred to v2 |

**Installation:**
```bash
# All dependencies already installed from phases 1-5
# No additional packages required
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── evaluation/
│   ├── __init__.py
│   ├── eval_suite.py         # Main evaluation orchestrator
│   ├── benchmark_loader.py   # Load 5 published scales
│   ├── item_comparison.py    # LLM-as-judge 4-criteria comparison
│   ├── metrics_aggregator.py # Compute dimension scores
│   └── baseline_runner.py    # A/B comparison: v1 vs pre-v1
tests/
├── test_eval_suite.py         # Evaluation suite tests
src/
├── app/
│   └── evaluation/
│       └── page.tsx           # Dashboard route
├── components/
│   └── EvaluationDashboard.tsx # Results visualization
```

### Pattern 1: LLM-as-Judge Comparison (Reuse Validator Pattern)

**What:** Use structured output with chain-of-thought reasoning to compare generated items to published scale items

**When to use:** For all 4 comparison criteria (quality parity, construct fidelity, stylistic similarity, psychometric properties)

**Example:**
```python
# Source: Existing validator.py pattern (backend/agents/validator.py)
from langchain_core.messages import HumanMessage, SystemMessage
from backend.agents.llm_factory import get_chat_model_for_agent
from backend.schemas import ComparisonResult  # New schema

def compare_to_published_item(
    generated_item: str,
    published_item: str,
    construct_name: str,
    model_provider: str = "claude"
) -> ComparisonResult:
    """Compare generated item to published scale item using LLM-as-judge.

    Returns structured comparison with 4 dimensions:
    - quality_parity: 1-10 score + reasoning
    - construct_fidelity: 1-10 score + reasoning
    - stylistic_similarity: 1-10 score + reasoning
    - psychometric_properties: 1-10 score + reasoning
    """
    system_prompt = load_prompt("item_comparator.md")  # New prompt

    model = get_chat_model_for_agent(
        agent_name="validator",  # Reuse Opus allocation
        model_provider=model_provider,
        use_chatgpt_critics=False  # Always use Opus for evaluation
    )

    messages = [
        SystemMessage(
            content=system_prompt,
            additional_kwargs={"cache_control": {"type": "ephemeral"}}
        ),
        HumanMessage(
            content=f"Compare these items:\n\nGenerated: {generated_item}\nPublished: {published_item}\nConstruct: {construct_name}"
        ),
    ]

    runnable = model.with_structured_output(ComparisonResult, strict=False, include_raw=True)
    response = runnable.invoke(messages)

    return response["parsed"]
```

### Pattern 2: Benchmark Scale Loading via Web Surfer

**What:** Use existing Web Surfer agent to research and select 5 published scales

**When to use:** One-time setup to identify benchmark constructs

**Example:**
```python
# Source: Existing web_surfer.py pattern (backend/agents/web_surfer.py)
from backend.agents.web_surfer import surf
from backend.schemas import UserRequest

def find_benchmark_scales() -> List[BenchmarkScale]:
    """Use Web Surfer to identify 5 published scales across domains.

    Searches for:
    - Personality: NEO-PI-R or Big Five Inventory
    - Clinical: PHQ-9, GAD-7
    - Social: Social Connectedness Scale
    - Organizational: Job Satisfaction Survey (JSS)
    - Attitudes: Domain-specific validated scales
    """
    domains = [
        "personality assessment Big Five NEO-PI-R",
        "clinical depression anxiety PHQ-9 GAD-7",
        "social connectedness belongingness scale",
        "job satisfaction organizational JSS",
        "attitude measurement validated scales"
    ]

    scales = []
    for domain in domains:
        request = UserRequest(
            construct_name=domain,
            construct_definition=f"Find well-validated, public domain scale for {domain}",
            target_population="Research",
            response_scale="Likert",
            item_count=5
        )

        result = surf(request)  # Returns RetrievalResponse with evidence
        # Parse evidence to extract scale metadata
        scale = parse_scale_metadata(result.evidence)
        scales.append(scale)

    return scales
```

### Pattern 3: Aggregated Metrics Dashboard

**What:** Display high-level scores per evaluation dimension without per-agent/per-construct drill-down

**When to use:** Results visualization in v1 (keep simple)

**Example:**
```tsx
// Source: Reuse EvidenceAuditPanel pattern (src/components/EvidenceAuditPanel.tsx)
import { InsetPanel, SurfaceCard } from "@/components/ui/surface-card";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface EvaluationResults {
  item_quality_score: number;      // 0-10
  agent_performance_score: number;  // 0-10
  workflow_efficiency_score: number; // 0-10
  construct_validity_score: number; // 0-10
  baseline_improvement: number;     // percentage
}

export function EvaluationDashboard({ results }: { results: EvaluationResults }) {
  return (
    <SurfaceCard className="border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-base md:text-lg">Evaluation Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5 pt-5">
        <InsetPanel className="space-y-2 rounded-2xl p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Item Quality
          </p>
          <p className="text-2xl font-bold">{results.item_quality_score.toFixed(1)}/10</p>
        </InsetPanel>

        <InsetPanel className="space-y-2 rounded-2xl p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Agent Performance
          </p>
          <p className="text-2xl font-bold">{results.agent_performance_score.toFixed(1)}/10</p>
        </InsetPanel>

        <InsetPanel className="space-y-2 rounded-2xl p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Workflow Efficiency
          </p>
          <p className="text-2xl font-bold">{results.workflow_efficiency_score.toFixed(1)}/10</p>
        </InsetPanel>

        <InsetPanel className="space-y-2 rounded-2xl p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Construct Validity
          </p>
          <p className="text-2xl font-bold">{results.construct_validity_score.toFixed(1)}/10</p>
        </InsetPanel>

        <InsetPanel className="rounded-2xl border border-accent/35 bg-accent/15 p-3">
          <p className="text-sm font-semibold">Baseline Improvement</p>
          <p className="text-2xl font-bold text-accent mt-1">
            {results.baseline_improvement >= 15 ? '✓' : '✗'} {results.baseline_improvement.toFixed(1)}%
          </p>
          <p className="text-xs text-slate-100/90 mt-1">
            {results.baseline_improvement >= 15
              ? 'Success: Exceeds 15% improvement threshold'
              : 'Below target: Additional optimization needed'}
          </p>
        </InsetPanel>
      </CardContent>
    </SurfaceCard>
  );
}
```

### Anti-Patterns to Avoid

- **Complex drill-down UIs in v1:** User decided aggregated metrics only — avoid per-agent, per-construct, per-item breakdowns that add complexity without clear v1 value
- **Human expert comparison:** User decided AI-based comparison — don't plan manual expert review workflows, use LLM-as-judge exclusively
- **Real-time streaming eval:** Not needed — evaluation runs on-demand, results displayed after completion (no SSE streaming required)
- **External eval frameworks:** Avoid introducing LangSmith, Weights & Biases, or similar external dependencies — use pytest + custom endpoint pattern

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM-as-judge scoring | Custom scoring logic, manual rubrics | Existing validator.py pattern with structured output | Proven chain-of-thought pattern, Pydantic validation, cache control for cost |
| Benchmark scale selection | Manual curation, hardcoded items | Web Surfer agent with Perplexity search | Automated research, citation tracking, metadata extraction already implemented |
| Dashboard visualization | Custom chart libraries | Reuse InsetPanel, SurfaceCard, existing shadcn/ui patterns | Consistent UI, no new dependencies, proven component patterns |
| Test orchestration | Custom test runner | pytest with fixtures and parametrization | Industry standard, already in project, IDE integration, CI/CD ready |
| Structured output parsing | JSON.parse() with error handling | Pydantic with_structured_output | Type-safe, validation built-in, null-handling proven in validator tests |

**Key insight:** MAPIG already implements the core evaluation patterns (LLM-as-judge, structured output, Web Surfer research, dashboard components). Phase 6 is composition, not invention — combine existing building blocks into evaluation suite.

## Common Pitfalls

### Pitfall 1: LLM-as-Judge Position Bias
**What goes wrong:** LLM judges favor the first option in comparisons due to position bias

**Why it happens:** Documented bias in LLM evaluation research — judges systematically prefer earlier-presented options

**How to avoid:**
- Randomize order: Compare both (generated → published) and (published → generated)
- Average scores from both orderings
- Document in prompt: "Evaluate independently, order does not indicate quality"

**Warning signs:** Generated items consistently score higher/lower than published items regardless of actual quality

### Pitfall 2: Baseline Comparison Without True Pre-v1.0 State
**What goes wrong:** Comparing current system to "simulated" baseline by disabling validation gate, but other v1.0 optimizations remain active

**Why it happens:** v1.0 includes multiple optimizations beyond validation gate (bias reviewer 7-type taxonomy, meta editor facet balancing, item writer 10 principles)

**How to avoid:**
- Clearly document what "pre-v1.0" means: "System without validation gate" (not full rollback to pre-optimization)
- Alternative: Compare validation scores from actual pre-v1.0 runs (if available in project history)
- Set realistic expectations: ≥15% improvement threshold assumes validation gate is primary optimization

**Warning signs:** Improvement significantly exceeds 15% (suggests baseline isn't truly "pre-v1.0" state)

### Pitfall 3: Benchmark Scale Copyright Violations
**What goes wrong:** Selected benchmark scales are copyrighted, can't legally include items in evaluation

**Why it happens:** Many published scales (e.g., NEO-PI-R full version) are proprietary despite wide use

**How to avoid:**
- Web Surfer selection criteria must include "public domain" or "open access"
- Prioritize: PHQ-9/GAD-7 (Pfizer made public domain), IPIP scales (Creative Commons), MSQ (CC BY-NC 4.0)
- Verify license before including items in eval suite
- Use abbreviated versions (e.g., NEO-FFI items from IPIP, not PAR copyrighted version)

**Warning signs:** Scale requires purchase, registration, or written permission — not suitable for automated eval

### Pitfall 4: Aggregated Metrics Hide Critical Failures
**What goes wrong:** Overall score looks good (e.g., 8.2/10) but one dimension is critically low (e.g., construct validity: 4/10)

**Why it happens:** Simple averaging across dimensions masks outliers

**How to avoid:**
- Display all 4 dimension scores prominently (not just overall score)
- Flag dimensions below threshold (e.g., <7.0 = warning)
- Success criteria: ALL dimensions ≥7.0 AND overall improvement ≥15%
- Document in evaluation logic: "System passes only if no dimension fails"

**Warning signs:** Dashboard shows "Success" but individual dimension scores vary widely (e.g., 10, 9, 8, 3)

### Pitfall 5: Evaluation Suite Runtime Exceeds Acceptable Limits
**What goes wrong:** 25-item evaluation takes 10+ minutes, making on-demand runs impractical

**Why it happens:** Each comparison requires LLM-as-judge call (4 criteria × 25 items = 100 structured outputs)

**How to avoid:**
- Parallel processing: Batch comparisons using asyncio (FastAPI already async)
- Cache published scale items: Load once, reuse across runs
- Optimize prompt: Combine 4 criteria into single structured output (not 4 separate calls)
- Monitor runtime: Log per-item comparison time, set timeout (e.g., 5 min max)

**Warning signs:** Evaluation takes >5 minutes for 25 items (target: 2-5 min total runtime)

## Code Examples

Verified patterns from existing codebase:

### Structured Output with Null Handling
```python
# Source: backend/agents/validator.py (lines 154-189)
# Pattern: Parse structured output with explicit null checks
runnable = model.with_structured_output(ValidationResponse, strict=False, include_raw=True)
response = runnable.invoke(messages)

if isinstance(response, dict) and "parsed" in response and "raw" in response:
    result = response["parsed"]
    raw_message = response["raw"]

    # CRITICAL: Check if parsing failed (returns None when schema doesn't match)
    if result is None:
        logger.error(
            f"Structured output parsing failed for validator. "
            f"Model: {model_name}, Attempt: {attempt}/3."
        )
        raise RuntimeError(
            f"Validator structured output parsing failed - LLM returned invalid format."
        )

    usage = _extract_token_usage(raw_message, model_name)
else:
    # Fallback for older LangChain behavior
    result = response
    usage = TokenUsage(model_name=model_name)

    if result is None:
        raise RuntimeError(f"Validator returned None - no response from LLM.")
```

### Web Surfer Academic Search with Domain Filter
```python
# Source: backend/agents/web_surfer.py (lines 156-207)
# Pattern: Perplexity search with approved domains and structured evidence extraction
def surf(request: UserRequest) -> RetrievalResponse:
    """Use Perplexity academic search to retrieve evidence chunks."""
    if not settings.PERPLEXITY_API_KEY:
        raise RuntimeError("PERPLEXITY_API_KEY is not set")

    system_prompt = load_prompt("web_surfer.md")
    user_query = _synthesize_theoretical_query(request, boundary, exclude)
    domains = _domain_filter(request)  # Approved domains only

    payload = {
        "model": settings.PERPLEXITY_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        "temperature": 0,
        "web_search_options": {
            "search_mode": settings.PERPLEXITY_SEARCH_MODE,
            "num_search_results": settings.PERPLEXITY_MAX_RESULTS,
            "search_domain_filter": domains,  # Critical: only approved sources
        },
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    evidence = _process_perplexity_response(data)  # Structured extraction
    return RetrievalResponse(evidence=evidence)
```

### Dashboard Component with Expandable Details
```tsx
// Source: src/components/GeneratedItemsTable.tsx (lines 17-101)
// Pattern: Expandable validation score display with structured reasoning
function ValidationScoreDisplay({ validation, rationale }: {
  validation: ItemValidation;
  rationale: string;
}) {
  const [expandedReasoning, setExpandedReasoning] = React.useState(false);
  const [expandedRationale, setExpandedRationale] = React.useState(false);

  return (
    <div className="validation-score mt-3 space-y-2">
      {/* Score display */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-sm font-semibold ${validation.accept ? 'text-green-400' : 'text-red-400'}`}>
          Score: {validation.weighted_score.toFixed(2)}/10
        </span>

        <PrimaryButton
          size="sm"
          onClick={() => setExpandedReasoning(!expandedReasoning)}
          className="h-8 text-xs"
        >
          {expandedReasoning ? <ChevronDown /> : <ChevronRight />}
          Show Reasoning
        </PrimaryButton>
      </div>

      {/* Reasoning panel */}
      {expandedReasoning && (
        <InsetPanel className="rounded-xl border border-white/20 bg-slate-900/45 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            Dimension Scores
          </p>
          <div className="space-y-2">
            {validation.dimension_scores.map((dim, idx) => (
              <div key={idx} className="border-l-2 border-accent/40 pl-3">
                <div className="text-sm font-medium text-slate-100">
                  {dim.dimension}: {dim.score}/10
                </div>
                {dim.reasoning && (
                  <div className="mt-1 text-xs text-slate-300 italic">
                    {dim.reasoning}
                  </div>
                )}
              </div>
            ))}
          </div>
        </InsetPanel>
      )}
    </div>
  );
}
```

### Pytest Mock Mode Pattern
```python
# Source: tests/test_validator.py (lines 10-11, 196-215)
# Pattern: Set APP_MODE=mock for deterministic test results
import os
import pytest

os.environ["APP_MODE"] = "mock"

def test_mock_mode_returns_deterministic_results():
    """Mock mode returns deterministic validation results."""
    from backend.agents.validator import validate_items

    request = _sample_user_request()
    items = _sample_draft_items()

    result, usage = validate_items(request, items, attempt=1)

    # Mock mode: deterministic results
    assert len(result.validations) == 2, "Should validate both items"

    # First item (idx 0) passes with score 8.0
    assert result.validations[0].weighted_score == 8.0
    assert result.validations[0].accept is True

    # Second item (idx 1) fails with score 6.5
    assert result.validations[1].weighted_score == 6.5
    assert result.validations[1].accept is False
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual expert comparison | LLM-as-judge (85% human alignment) | 2024-2025 | Automated, scalable, cost-effective, documented reasoning |
| Embedding similarity | Chain-of-thought LLM scoring | 2024 | Transparent reasoning (not black-box), 10-15% reliability improvement |
| Single aggregated metric | Multi-dimensional evaluation (4+ dimensions) | 2025-2026 | Comprehensive assessment, identifies specific failure modes |
| External eval frameworks (LangSmith, W&B) | In-project pytest + custom dashboards | 2026 | No external dependencies, full control, CI/CD integration |
| Hardcoded benchmark datasets | Dynamic scale sourcing via Web Surfer | 2026 | Up-to-date scales, citation tracking, automated metadata extraction |

**Deprecated/outdated:**
- **SurveyBot3000 synthetic correlation approach:** Validated LLM-as-judge but required large-scale synthetic data generation — now superseded by direct comparison to published scales
- **Reference-free evaluation only:** 2026 best practice combines reference-based (compare to published items) and reference-less (absolute quality rubric) for comprehensive assessment
- **Position-unaware comparison:** Early LLM-as-judge implementations ignored position bias — now standard to evaluate both orderings and average

## Open Questions

1. **Which NEO-PI-R variant is suitable for evaluation?**
   - What we know: NEO-PI-R full version is copyrighted (PAR), 240 items, $$ license required
   - What's unclear: Can we use IPIP-NEO items (Creative Commons) as proxy for Big Five personality assessment?
   - Recommendation: Use IPIP-NEO-120 or IPIP-NEO-60 (open access, well-validated, similar construct coverage) instead of proprietary NEO-PI-R

2. **How to operationalize "pre-v1.0 baseline" for A/B comparison?**
   - What we know: v1.0 included validation gate + multiple agent optimizations (bias taxonomy, facet balancing, 10 psychometric principles)
   - What's unclear: Does "pre-v1.0" mean (a) disable validation gate only, or (b) rollback all v1.0 optimizations?
   - Recommendation: Define as "validation gate disabled, all other v1.0 optimizations active" — documents incremental value of validation gate specifically

3. **Should evaluation dashboard be accessible publicly or require authentication?**
   - What we know: Main MAPIG app has no authentication (Phase 1-5 scope), Vercel deployment is public
   - What's unclear: Evaluation results may reveal system performance details — should dashboard be public?
   - Recommendation: Keep public in v1 (aligns with open-access approach), consider authentication in v2 if competitive concerns arise

4. **What aggregation formula for overall "system quality" score?**
   - What we know: 4 dimensions (item quality, agent performance, workflow, construct validity), user wants aggregated summary
   - What's unclear: Equal weighting (25% each) or prioritized (e.g., construct validity 40%, others 20%)?
   - Recommendation: Equal weighting (25% each) for v1 simplicity, document formula explicitly in evaluation logic

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (lines 49-50) |
| Quick run command | `pytest tests/test_eval_suite.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVAL-01 | Evaluation suite runs on demand | integration | `pytest tests/test_eval_suite.py::test_eval_suite_runs_on_demand -x` | ❌ Wave 0 |
| EVAL-02 | Reports 4 dimensions | unit | `pytest tests/test_eval_suite.py::test_reports_four_dimensions -x` | ❌ Wave 0 |
| EVAL-03 | 5 benchmark constructs loaded | unit | `pytest tests/test_eval_suite.py::test_loads_five_benchmarks -x` | ❌ Wave 0 |
| EVAL-04 | 25 test cases (5 items × 5 constructs) | unit | `pytest tests/test_eval_suite.py::test_25_test_cases -x` | ❌ Wave 0 |
| EVAL-05 | LLM-as-judge comparison works | unit | `pytest tests/test_eval_suite.py::test_llm_comparison_structured_output -x` | ❌ Wave 0 |
| EVAL-06 | Comparison results documented | integration | `pytest tests/test_eval_suite.py::test_comparison_results_persisted -x` | ❌ Wave 0 |
| EVAL-07 | Baseline improvement calculated | unit | `pytest tests/test_eval_suite.py::test_baseline_comparison_15_percent -x` | ❌ Wave 0 |
| EVAL-08 | Success criteria documented in results | unit | `pytest tests/test_eval_suite.py::test_success_criteria_in_output -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_eval_suite.py -x` (eval suite tests only, <30s)
- **Per wave merge:** `pytest tests/ -v` (full suite including eval tests)
- **Phase gate:** Full suite green + manual dashboard verification before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_eval_suite.py` — covers all EVAL-01 through EVAL-08 requirements
- [ ] `tests/test_benchmark_loader.py` — covers benchmark scale loading and validation
- [ ] `tests/test_item_comparison.py` — covers LLM-as-judge comparison logic
- [ ] `backend/evaluation/__init__.py` — module initialization
- [ ] `data/benchmarks/` — directory for storing published scale metadata (created during implementation)

## Sources

### Primary (HIGH confidence)
- [LLM-as-a-Judge Evaluation: Complete Guide - Langfuse](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge) - LLM-as-judge methodology, structured output patterns
- [LLM Evaluation: Frameworks, Metrics, and Best Practices (2026 Edition)](https://futureagi.substack.com/p/llm-evaluation-frameworks-metrics) - 2026 best practices, 85% human alignment, chain-of-thought improvements
- [Best Practices for Developing and Validating Scales for Health, Social, and Behavioral Research: A Primer](https://pmc.ncbi.nlm.nih.gov/articles/PMC6004510/) - Psychometric validation metrics, construct validity assessment
- [Current Concepts in Validity and Reliability for Psychometric Instruments - The American Journal of Medicine](https://www.amjmed.com/article/S0002-9343(05)01037-5/fulltext) - Validity and reliability metrics, correlation thresholds
- [Pfizer To Offer Free Public Access To Mental Health Assessment Tools](https://www.pfizer.com/news/press-release/press-release-detail/pfizer_to_offer_free_public_access_to_mental_health_assessment_tools_to_improve_diagnosis_and_patient_care) - PHQ-9 and GAD-7 public domain status

### Secondary (MEDIUM confidence)
- [Evaluating Agentic Workflows: The Essential Metrics That Matter](https://www.getmaxim.ai/articles/evaluating-agentic-workflows-the-essential-metrics-that-matter/) - Agent workflow evaluation metrics (iteration count, acceptance rate, completion rate)
- [pytest-glow-report: Beautiful Test Reports for the Modern Era](https://www.dhirajdas.dev/blog/pytest-glow-report-beautiful-test-reports) - Modern pytest dashboard reporting patterns
- [Job Satisfaction Survey (JSS) - Paul Spector](https://paulspector.com/assessments/pauls-no-cost-assessments/job-satisfaction-survey-jss/) - Open access organizational behavior scale (36 items, 9 facets)
- [Minnesota Satisfaction Questionnaire (MSQ)](https://vpr.psych.umn.edu/node/26) - CC BY-NC 4.0 licensed job satisfaction scale
- [Open psychology data: Raw data from online personality tests](http://openpsychometrics.org/_rawdata/) - IPIP datasets, public domain personality scales

### Tertiary (LOW confidence - for general context only)
- [Revised NEO Personality Inventory - Wikipedia](https://en.wikipedia.org/wiki/Revised_NEO_Personality_Inventory) - NEO-PI-R background (note: full version is copyrighted, not suitable for direct use)
- [How to Build an Analytical Dashboard with Next.js](https://www.freecodecamp.org/news/build-an-analytical-dashboard-with-nextjs/) - Next.js dashboard patterns (general guidance, not MAPIG-specific)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project (pytest, Pydantic, FastAPI, Next.js), no new dependencies
- Architecture: HIGH - Reuses proven patterns (validator LLM-as-judge, Web Surfer search, dashboard components), composition not invention
- Pitfalls: HIGH - Position bias, copyright issues, aggregation failures documented in 2026 LLM-as-judge research

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (30 days - stable evaluation practices, unlikely to change rapidly)
