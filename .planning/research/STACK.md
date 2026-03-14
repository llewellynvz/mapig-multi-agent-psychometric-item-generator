# Technology Stack Additions for v2.0 Psychometric Rigor

**Project:** MAPIG v2.0 - Synthetic Correlations, Instrument Comparison, Reasoning Models
**Researched:** 2026-03-14
**Confidence:** MEDIUM-HIGH

## Executive Summary

This research identifies stack additions needed for v2.0 psychometric rigor features while maintaining compatibility with the existing FastAPI + LangGraph + Next.js serverless architecture. **Critical finding**: pandas/NumPy will likely exceed Vercel's 250 MB serverless function limit, requiring pure NumPy implementation or correlation computation offload to client-side.

**Recommended approach**: Lightweight NumPy-only backend for correlation computation (if size permits), visx React library for frontend heatmap visualization, langchain-openai upgrade for GPT-5.2/o3 reasoning support, and Perplexity API enhancement for dynamic literature search.

## New Capabilities Analysis

### 1. Synthetic Inter-Item Correlation Analysis

**Requirement:** Generate correlation matrices from LLM-predicted item relationships without requiring response data.

**Stack additions:**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| NumPy | >=2.1.0, <3.0 | Correlation matrix computation | `np.corrcoef()` provides Pearson correlations with minimal dependencies; significantly lighter than pandas (critical for Vercel 250 MB limit) |

**Alternative (if NumPy size is problematic):**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Client-side correlation | N/A (pure JS) | Compute correlations in browser | Avoids serverless size limits entirely; correlation is simple math (Σ(x-x̄)(y-ȳ) / √Σ(x-x̄)²Σ(y-ȳ)²) implementable in 20-30 lines of TypeScript |

**What NOT to use:**
- ❌ **pandas** - Full pandas adds ~100-150 MB uncompressed, will likely exceed Vercel's 250 MB limit alongside existing dependencies (FastAPI, LangGraph, LangChain)
- ❌ **SciPy** - Adds significant size for features beyond basic correlation (overkill for this use case)
- ❌ **PyNetCor** - High-performance library for massive datasets (70k+ features); unnecessary complexity for typical 10-50 item scales

**Rationale:**
- NumPy is likely already transitively included via existing dependencies (langchain may pull it in)
- `np.corrcoef()` is standard, well-documented, and sufficient for Pearson correlations
- If size becomes issue, pure Python/TypeScript correlation is trivial to implement

**Vercel size constraint mitigation:**
1. Check if NumPy already exists in deployment (likely via transitive deps)
2. Use `excludeFiles` in `vercel.json` to exclude test files, docs, examples
3. If size exceeded: implement correlation client-side in TypeScript (benefits: no backend compute, no size limit)

### 2. Dynamic Literature Search for Validated Instruments

**Requirement:** Search academic literature for existing validated instruments to compare against generated items.

**Stack additions:**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Perplexity API (existing) | sonar-pro | Academic search with scholarly source prioritization | Already integrated; supports "Academic" Focus mode to restrict search to peer-reviewed journals and scholarly databases |
| httpx (existing) | 0.28.1 | API requests for literature search | Already in pyproject.toml; used for Perplexity calls |

**No new dependencies required** - existing Perplexity API integration sufficient.

**Enhancement approach:**
- Use Perplexity's `academic` domain focus mode (already available in API)
- Structured prompts to extract: instrument name, construct measured, sample items, facets/subscales, validation study citations
- Store structured extraction results in existing Pydantic schemas (new schema: `ValidatedInstrument`)

**Alternative (lower priority):**

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| Semantic Scholar API | Free tier: 100 req/5min | Academic paper search with citation data | If Perplexity Academic mode proves insufficient for retrieving full instrument details; provides direct access to ~200M papers |

**What NOT to use:**
- ❌ **Google Scholar scraping** - Violates ToS, unreliable, no official API
- ❌ **PubMed API** - Limited to biomedical literature; misses psychology/org psych instruments
- ❌ **CrossRef API** - Metadata only; doesn't retrieve full-text or instrument items

**Rationale:**
- Perplexity Academic already provides scholarly source prioritization
- Perplexity returns structured snippets with source URLs (no need for separate full-text retrieval)
- Semantic Scholar as backup if Perplexity can't retrieve specific instrument items

### 3. Cross-Construct Comparison Analysis

**Requirement:** Compare generated items against validated instruments from literature to assess construct correspondence.

**Stack additions:**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| None required | - | Use existing LLM-as-judge infrastructure | Leverage existing Claude Opus 4.6 validation agent pattern for cross-construct comparison; add new comparison dimensions to existing 4-dimensional scoring |

**Enhancement approach:**
- Extend existing `ValidationAgent` with new comparison mode: `ComparisonAgent`
- New Pydantic schema: `CrossConstructComparison` with fields:
  - `generated_item`: str
  - `reference_instrument`: str
  - `reference_items`: list[str]
  - `correspondence_score`: float (0-10)
  - `distinctiveness_score`: float (0-10)
  - `overlap_reasoning`: str
  - `divergence_reasoning`: str
- Reuse existing Claude Opus 4.6 allocation for comparison accuracy

**What NOT to use:**
- ❌ **Sentence transformers / embeddings** - Abandoned in v1.0 in favor of LLM-as-judge (more transparent reasoning, better psychometric alignment)
- ❌ **Traditional NLP similarity metrics (cosine, Jaccard)** - Surface-level; miss psychometric nuance (e.g., "I feel sad" vs "I am depressed" - high lexical similarity but different clinical implications)

**Rationale:**
- Existing validation infrastructure already proven (v1.1 evaluation showed ≥7.0/10 on all dimensions)
- LLM-as-judge provides explicit reasoning (critical for psychometric validation)
- No new dependencies = no deployment complexity

### 4. GPT-5.2 / o3 Reasoning Model Integration

**Requirement:** Support GPT-5.2, o3, o1 reasoning models with thinking mode configuration (high effort by default).

**Stack additions:**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| langchain-openai | >=2.0.0 (upgrade from 1.1.7) | GPT-5.2, o3, o1 reasoning model support with `reasoning_effort` parameter | Version 2.x adds native support for `max_completion_tokens` (required by o3/o1) and `reasoning` parameter configuration |
| openai (transitive) | >=1.50.0 | OpenAI Python SDK with Responses API support | GPT-5.2 and o3 models use Responses API (unified interface); older Chat Completions API deprecated for reasoning models |

**Configuration parameters:**

| Parameter | Values | Default | Purpose |
|-----------|--------|---------|---------|
| `reasoning.effort` | none, low, medium, high, xhigh | **high** (recommended for psychometric validation) | Controls reasoning token generation before response; higher = more thorough but slower/costier |
| `reasoning.summary` | none, concise, detailed | **detailed** (recommended) | Controls reasoning summary verbosity in GPT-5.2+ |
| `max_completion_tokens` | int | Model-specific | Replaces deprecated `max_tokens` for o3/o1 models |

**Implementation approach:**

```python
# backend/settings.py additions
REASONING_EFFORT: str = "high"  # Environment-configurable
REASONING_SUMMARY: str = "detailed"

# backend/agents/validation_agent.py update
model = ChatOpenAI(
    model="gpt-5.2",  # or "o3", "o3-mini", "o1"
    reasoning={
        "effort": settings.REASONING_EFFORT,
        "summary": settings.REASONING_SUMMARY
    },
    max_completion_tokens=4000,  # Not max_tokens
)
```

**Known compatibility issues (as of 2026-03):**
- LangChain GitHub issues (#29632, #29947, #32714) report parameter compatibility problems with o3 models
- `max_tokens` → `max_completion_tokens` transition not fully stable across all LangChain wrappers (AzureChatOpenAI especially)
- **Mitigation:** Test thoroughly; fallback to gpt-4o if o3/5.2 integration unstable

**What NOT to use:**
- ❌ **o3/o1 with existing langchain-openai 1.1.7** - Missing `max_completion_tokens` support causes 400 errors
- ❌ **Chat Completions API** - Reasoning models require Responses API (newer unified interface)
- ❌ **reasoning.effort = "none"** - Defeats purpose of reasoning models; use gpt-4o instead for latency-critical paths

**Rationale:**
- Reasoning models provide deeper psychometric analysis (critical for construct validation)
- High effort mode aligns with v2.0 goal: "scale-level psychometric rigor" not just item-level quality
- Detailed summaries provide transparency for validation reasoning

**Cost implications:**
- Reasoning tokens billed separately (check OpenAI pricing)
- High effort = 2-5x more reasoning tokens than low
- Use for validation only (not all agents) - same pattern as existing Opus allocation

### 5. Correlation and Comparison Visualization

**Requirement:** Display correlation matrices and cross-construct comparisons in React frontend.

**Stack additions:**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| @visx/heatmap | ^3.12.0 | Correlation matrix heatmap visualization | Low-level React + D3 components; tree-shakeable (only ship what you use); Airbnb-maintained with 19.9k GitHub stars; no built-in heatmap in shadcn/Recharts |
| @visx/scale | ^3.12.0 | Color scales for heatmap (correlation strength) | Required peer dependency for @visx/heatmap; provides linear/sequential color scales |
| @visx/tooltip | ^3.12.0 | Hover tooltips for correlation values | Accessible tooltip primitives; integrates with existing Radix UI patterns |

**Alternative (if visx too complex):**

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| Custom React component | N/A | Pure React/SVG heatmap | If visx learning curve too steep; correlation heatmap is ~100 lines of React + SVG math |
| Tremor (@tremor/react) | ^3.x | Pre-built chart components (built on Recharts) | If need rapid prototyping; BUT lacks native heatmap support (only line/bar/area) |

**Why NOT existing libraries:**

| Library | Why Not Use |
|---------|-------------|
| Recharts (existing) | No native heatmap component; would require custom Scatter chart workaround (200+ lines vs 50 with visx) |
| MUI X Charts | Different design system (Material); conflicts with existing shadcn/Radix primitives |
| Syncfusion / KendoReact | Commercial licenses required; overkill for single heatmap use case |
| D3 directly | Lower-level than necessary; visx provides React-friendly wrappers around D3 primitives |

**Recommended approach:**

1. **Correlation matrix heatmap:**
   - Use `@visx/heatmap` with `@visx/scale` for color gradients (red = negative, white = 0, blue = positive)
   - Custom Radix Tooltip (existing pattern) for hover values
   - Display: triangular matrix (upper or lower only) to avoid redundant diagonal

2. **Comparison visualization:**
   - Simple bar chart showing correspondence scores (use existing Recharts from evaluation dashboard)
   - Alternatively: radar chart for multi-dimensional comparison (Recharts `RadarChart` already available)

**Bundle size considerations:**
- `@visx/heatmap`: ~15 KB minified + gzipped (tree-shakeable)
- `@visx/scale`: ~8 KB minified + gzipped
- `@visx/tooltip`: ~5 KB minified + gzipped
- **Total addition:** ~28 KB (negligible compared to existing Next.js bundle)

**Integration with existing stack:**
- visx uses React + D3 math (no DOM manipulation) = works with Next.js SSR
- SVG-based = accessible, printable, screenshot-friendly
- Styling via Tailwind classes (matches existing shadcn patterns)

## Installation

### Backend (Python)

```bash
# Upgrade for reasoning models
poetry add langchain-openai@^2.0.0

# NumPy (check if already present via transitive deps first)
poetry add numpy@^2.1.0

# Alternative: If NumPy causes size issues, remove and implement client-side
poetry remove numpy
```

### Frontend (TypeScript/React)

```bash
# Heatmap visualization
npm install @visx/heatmap @visx/scale @visx/tooltip
```

## Version Compatibility Matrix

| Package | Current (v1.1) | Required (v2.0) | Breaking Changes |
|---------|----------------|-----------------|------------------|
| langchain-openai | 1.1.7 | >=2.0.0 | `max_tokens` → `max_completion_tokens` for o3/o1; may affect existing model calls |
| FastAPI | 0.128.0 | 0.128.0 | No change |
| LangGraph | 1.0.6 | 1.0.6 | No change |
| Next.js | 16.1.6 | 16.1.6 | No change |
| NumPy | Not explicit | 2.1.x (optional) | New dependency; size risk |
| @visx/* | Not present | 3.12.0 | New dependency; no conflicts |

**Upgrade path:**
1. Test langchain-openai 2.x upgrade in isolation (may affect existing gpt-4o calls)
2. Add NumPy only if serverless size check passes (<200 MB after dependencies)
3. Add visx packages (low risk, frontend-only)

## Alternatives Considered

### Correlation Computation

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| NumPy `np.corrcoef()` | Pure Python/TypeScript implementation | If NumPy exceeds Vercel 250 MB limit; correlation is simple Σ(x-x̄)(y-ȳ) formula |
| Backend computation | Client-side computation | If size is issue OR if correlation matrices large (50+ items); browser has more memory than serverless function |
| NumPy | pandas `DataFrame.corr()` | Never for this use case - pandas is 3-5x heavier than NumPy for same correlation result |

### Literature Search

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Perplexity Academic mode | Semantic Scholar API | If need direct paper metadata (citations, authors); Perplexity better for full-text instrument extraction |
| Structured LLM extraction | Manual parsing | Never - LLM extraction already proven in existing Web Surfer agent |

### Visualization

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| visx heatmap | Custom React/SVG | If want full control + learning opportunity; heatmap is grid + color mapping |
| visx | Tremor | If need other chart types too; BUT Tremor lacks heatmap (would still need custom component) |
| visx | shadcn-calendar-heatmap | If want shadcn-native component; BUT designed for calendar data not correlation matrices |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pandas for correlation | 100-150 MB package; will exceed Vercel limit | NumPy `np.corrcoef()` or client-side JS |
| SciPy stats | Heavy dependency for basic correlation | NumPy sufficient |
| Embedding models (sentence-transformers) | Requires PyTorch (~500 MB); abandoned in v1.0 for LLM-as-judge | Existing Claude Opus validation pattern |
| Google Scholar scraping | ToS violation; unreliable | Perplexity Academic or Semantic Scholar API |
| D3.js directly | Lower-level than needed | visx (React-friendly D3 wrappers) |
| MUI X Charts | Different design system (Material vs Radix) | visx or custom component with shadcn styling |
| langchain-openai <2.0 with o3 | Missing `max_completion_tokens`; causes 400 errors | Upgrade to >=2.0.0 |
| Chat Completions API for reasoning models | Deprecated for GPT-5.2/o3 | Responses API (handled by langchain-openai 2.x) |

## Stack Patterns by Variant

**If serverless size limit exceeded (>250 MB):**
- Remove NumPy backend dependency
- Implement correlation computation client-side in TypeScript (~30 lines)
- Benefits: No backend size constraint, no serverless compute time, more scalable

**If need real-time literature search:**
- Keep existing Perplexity integration
- Add Semantic Scholar API as fallback for citation metadata
- Use parallel search (Perplexity for full-text, Semantic Scholar for citations)

**If GPT-5.2/o3 integration unstable:**
- Fallback to gpt-4o with existing langchain-openai 1.1.7
- Keep `reasoning_effort` config env var but ignore if model doesn't support
- Monitor LangChain GitHub issues (#29632, #29947) for compatibility fixes

**If need faster visualization prototyping:**
- Start with custom React/SVG heatmap (simple grid + d3-scale-chromatic for colors)
- Migrate to visx later if need interactivity (zoom, brush selection)

## Deployment Considerations

### Vercel Serverless Function Size

**Current known issues:**
- Python functions have 250 MB uncompressed limit (500 MB compressed)
- pandas + NumPy + sklearn often exceed this limit
- FastAPI + LangGraph + LangChain already consume ~80-100 MB

**Size budget for v2.0:**
- Existing dependencies: ~100 MB
- NumPy (if added): ~20-30 MB
- **Total estimate: ~130 MB** (within 250 MB limit, but leaves ~120 MB buffer)

**Mitigation strategies (if size exceeded):**
1. Use `excludeFiles` in `vercel.json` to exclude test files, examples, docs
2. Remove NumPy; implement correlation client-side
3. Use external service for heavy computation (e.g., Modal, AWS Lambda with 10 GB limit)

**Recommended approach for v2.0:**
1. Add NumPy to `pyproject.toml`
2. Deploy to Vercel preview
3. Check deployment logs for function size
4. If >200 MB warning: implement correlation client-side instead

### Frontend Bundle Size

**Current bundle (v1.1):** ~250 KB gzipped (Next.js + React + shadcn + TanStack Query)

**v2.0 additions:**
- visx packages: +28 KB gzipped
- **Total estimate:** ~278 KB gzipped (acceptable; <300 KB threshold)

**No optimization needed** - visx is tree-shakeable and lightweight.

## Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| NumPy for correlation | **HIGH** | Standard library, well-documented, already likely in transitive deps; size risk is main concern |
| Perplexity Academic search | **HIGH** | Already integrated and working; Academic mode is native feature |
| LLM-as-judge comparison | **HIGH** | Proven in v1.1 validation; direct reuse of existing pattern |
| langchain-openai 2.x for reasoning | **MEDIUM** | GitHub issues show ongoing compatibility problems; upgrade may break existing gpt-4o calls |
| visx for heatmap | **HIGH** | Mature library (Airbnb), 3+ years stable, widely used, good docs |
| Vercel size constraint | **MEDIUM-LOW** | Risk of exceeding 250 MB with NumPy; mitigation available (client-side) but adds complexity |

## Open Questions & Risks

1. **NumPy size risk (MEDIUM):** Will existing deps + NumPy exceed 250 MB?
   - **Mitigation:** Deploy to preview environment and check; fallback to client-side correlation

2. **langchain-openai 2.x stability (MEDIUM):** GitHub issues (#29632, #29947, #32714) show parameter compatibility problems with o3
   - **Mitigation:** Test upgrade thoroughly; keep gpt-4o fallback; monitor LangChain releases

3. **Perplexity full instrument retrieval (LOW-MEDIUM):** Can Perplexity Academic mode retrieve actual item text vs just citations?
   - **Mitigation:** Test with known instruments (IPIP-NEO, PHQ-9); fallback to Semantic Scholar + manual retrieval

4. **o3 reasoning cost (LOW):** High effort mode may 3-5x token costs vs gpt-4o
   - **Mitigation:** Use only for validation agent (not all agents); same pattern as existing Opus allocation

## Implementation Priority

**Phase 1 (Low Risk):**
1. Add visx packages (frontend-only, no backend risk)
2. Enhance Perplexity prompts for instrument extraction (uses existing API)
3. Extend ValidationAgent with ComparisonAgent (reuses existing pattern)

**Phase 2 (Medium Risk - Test First):**
1. Upgrade langchain-openai to 2.x in dev environment
2. Test GPT-5.2/o3 integration with reasoning parameters
3. Add fallback logic for gpt-4o if reasoning models unstable

**Phase 3 (High Risk - Size Dependent):**
1. Add NumPy to requirements
2. Deploy to Vercel preview
3. Check function size (<200 MB green, 200-240 MB yellow, >240 MB red)
4. If red: remove NumPy, implement client-side correlation

## Sources

### GPT-5.2 and Reasoning Models
- [Introducing GPT-5.2 | OpenAI](https://openai.com/index/introducing-gpt-5-2/)
- [GPT-5.2 Model | OpenAI API](https://developers.openai.com/api/docs/models/gpt-5.2)
- [Introducing OpenAI o3 and o4-mini | OpenAI](https://openai.com/index/introducing-o3-and-o4-mini/)
- [o3 Model | OpenAI API](https://platform.openai.com/docs/models/o3)
- [Reasoning models | OpenAI API](https://platform.openai.com/docs/guides/reasoning)
- [LangChain Issue #29632 - Extend support for OpenAI o3 style models](https://github.com/langchain-ai/langchain/issues/29632)
- [LangChain Issue #29947 - AzureChatOpenAI Reasoning models](https://github.com/langchain-ai/langchain/issues/29947)
- [LangChain Forum - reasoning_effort parameter with GPT-5.2](https://forum.langchain.com/t/reasoning-effort-parameter-not-working-with-gpt-5-2-in-playground/3069)

### Correlation Analysis
- [NumPy, SciPy, and pandas: Correlation With Python – Real Python](https://realpython.com/numpy-scipy-pandas-correlation-python/)
- [numpy.corrcoef — NumPy v2.4 Manual](https://numpy.org/doc/stable/reference/generated/numpy.corrcoef.html)
- [pandas.DataFrame.corr — pandas 3.0.1 documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html)
- [PyNetCor: high-performance Python package for large-scale correlation analysis](https://academic.oup.com/nargab/article/6/4/lqae177/7928179)

### Academic Search APIs
- [Perplexity API Platform — AI Search & Grounded LLM APIs](https://www.perplexity.ai/api-platform)
- [Introducing the Perplexity Search API](https://www.perplexity.ai/hub/blog/introducing-the-perplexity-search-api)
- [Semantic Scholar Academic Graph API](https://www.semanticscholar.org/product/api)
- [Semantic Scholar API Tutorial](https://www.semanticscholar.org/product/api/tutorial)

### React Visualization Libraries
- [visx GitHub - Airbnb visualization components](https://github.com/airbnb/visx)
- [visx/heatmap npm package](https://www.npmjs.com/package/@visx/heatmap)
- [React Heatmap chart - MUI X](https://mui.com/x/react-charts/heatmap/)
- [Best heatmap libraries for React (with demos) - LogRocket](https://blog.logrocket.com/best-heatmap-libraries-react/)
- [Tremor – Copy-and-Paste Tailwind CSS UI Components](https://www.tremor.so/)
- [shadcn/ui Chart components](https://ui.shadcn.com/docs/components/radix/chart)

### Vercel Deployment Constraints
- [Using the Python Runtime with Vercel Functions](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Functions Limits](https://vercel.com/docs/functions/limitations)
- [Troubleshooting "Serverless Function has exceeded 250 MB" - Vercel KB](https://vercel.com/kb/guide/troubleshooting-function-250mb-limit)
- [Vercel Community - Python Serverless functions: reducing size of dependencies](https://community.vercel.com/t/python-serverless-functions-reducing-size-of-dependencies/1765)

---

*Stack research for: MAPIG v2.0 Psychometric Rigor*
*Researched: 2026-03-14*
*Confidence: MEDIUM-HIGH (NumPy size risk, langchain-openai 2.x stability concerns)*
