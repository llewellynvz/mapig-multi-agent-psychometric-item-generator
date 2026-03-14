# Phase 8: Synthetic Correlation Analysis - Research

**Researched:** 2026-03-14
**Domain:** Psychometric correlation estimation, LLM-based reliability analysis, interactive data visualization
**Confidence:** MEDIUM-HIGH

## Summary

Phase 8 implements LLM-estimated inter-item correlation matrices with McDonald's omega reliability metrics and interactive heatmap visualization. The phase combines three technical domains: (1) GPT-5.2 reasoning for pairwise correlation estimation with confidence intervals, (2) McDonald's omega calculation from correlation matrices using factor-analytic methods, and (3) visx-based heatmap visualization with Psynalytics brand colors.

**Key Findings:**
- McDonald's omega is the modern replacement for Cronbach's alpha, requiring factor analysis via Schmid-Leiman transformation (reliabiliPy library provides Python implementation)
- LLM-based psychometric estimation shows r > 0.6 agreement with published scales when using reasoning models (GPT-5.2 "high" reasoning effort recommended)
- visx @visx/heatmap provides low-level React primitives for custom brand-consistent visualizations (15KB bundle size)
- Optimal mean inter-item correlation range: 0.15-0.50 for broad constructs; ω ≥ 0.70 threshold aligns with alpha conventions
- NumPy/SciPy serverless size risk is manageable (NumPy ~30 MB; Vercel limit 250 MB uncompressed; current stack ~100 MB leaves sufficient buffer)

**Primary recommendation:** Use GPT-5.2 with high reasoning effort for pairwise correlation estimation (batched prompts for N×N matrix), reliabiliPy for omega calculation from correlation matrix, and visx HeatmapRect with custom Psynalytics gradient. Validate on 5 published scales with known correlation matrices (r > 0.6 agreement benchmark). Implement confidence intervals via LLM linguistic uncertainty verbalization rather than token probabilities.

## User Constraints

<user_constraints>

### Locked Decisions (from CONTEXT.md)

**Heatmap design & placement:**
- Collapsible panel below GeneratedItemsTable, following QualityChecksPanel expand/collapse pattern
- Collapsed by default — items shown first, user expands correlation panel when ready
- Hover tooltips showing exact correlation value, CI range, and item pair text
- Click opens detail popover with full reasoning for that pair
- Brand-consistent color scale using Psynalytics palette (primary teal #008da1, accent lime #a7d12b) — not standard academic blue-white-red
- visx library for heatmap visualization (per UI-01 requirement)

**Reliability metric:**
- McDonald's omega (ω) replaces Cronbach's alpha as the primary reliability metric
- Phase 7 schema field `cronbachs_alpha` renamed to `mcdonalds_omega` (breaking schema change from Phase 7)
- Threshold: ω ≥ 0.70 = pass, ω < 0.70 = warning (same threshold, better metric)
- Rationale: Alpha assumes tau-equivalence (equal factor loadings) which is rarely true; omega is based on factor model and is the recommended modern alternative

**Warning & flag presentation:**
- Separate quality summary card below the heatmap (not a banner, not inline badges)
- Card shows: McDonald's omega value + pass/warning status, mean inter-item correlation + optimal range flag (0.15-0.50), internal consistency assessment
- Brief one-line explanations for each metric (educational, not just numbers)
- Warnings are informational only — no blocking action, no suggestions for revision
- LLM estimates are advisory — hard blocking would be overstepping given these are synthetic, not empirical

**Benchmark validation (CORR-04):**
- Fixed calibration scales: 5 well-published scales with known correlation matrices selected by researcher agent during research phase
- Scales should span different psychological domains (personality, clinical, organizational, etc.)
- Must have published correlation matrices available (not just alpha values)
- Validation runs as part of evaluation suite (/evaluation framework), not per-generation
- Proves the LLM estimation method works (system calibration) — separate from Phase 9's dynamic instrument comparison
- Benchmark: r > 0.6 agreement between LLM-estimated and published correlations

**Export format:**
- Square matrix CSV format with item text headers (truncated), one correlation value per cell — familiar to SPSS/R users
- Confidence intervals in a separate file (not inline in the square matrix CSV)
- Export button inside the correlation panel (contextual, not in the main export dropdown)
- Disclaimer ("LLM-estimated, not empirically validated") in JSON export only, not in CSV
- JSON export includes full CorrelationMatrix object with all cells, aggregates, omega, and disclaimer

### Claude's Discretion

- Exact Psynalytics brand color gradient for heatmap (derived from primary/accent CSS variables)
- visx component architecture (HeatmapRect vs HeatmapCircle, axis labels, responsive sizing)
- LLM prompt engineering for pairwise correlation estimation (single prompt vs batched)
- CI estimation method from LLM responses
- McDonald's omega calculation approach (factor loading extraction from correlation matrix)
- Calibration scale selection criteria during research phase
- Quality summary card layout and styling details
- Hover tooltip and click popover component implementation
- CI file format (separate CSV or included in JSON only)

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CORR-01 | System generates LLM-estimated inter-item correlation matrix for finalized item sets without requiring response data | GPT-5.2 with high reasoning effort; batched pairwise prompts; LLM psychometric studies show r > 0.6 agreement with empirical data |
| CORR-02 | System computes McDonald's omega from synthetic correlation matrix with minimum threshold flag (ω >= 0.70) | reliabiliPy library (omega_total via Schmid-Leiman transformation); omega_hierarchical for general factor reliability; 0.70 threshold standard |
| CORR-03 | System provides confidence intervals for each synthetic correlation estimate | LLM linguistic verbalized uncertainty (LVU) shows better calibration than token probabilities; prompt for explicit CI ranges; store ci_low/ci_high per CorrelationCell |
| CORR-04 | System validates synthetic correlations against 5+ published scales with known correlation matrices (benchmark: r > 0.6 agreement) | Validation via evaluation framework (backend/evaluation/); 5 scales across domains (personality, clinical, social, organizational, attitudes); Pearson r between LLM-estimated and published matrices |
| CORR-05 | System labels all synthetic correlations as "LLM-estimated, not empirically validated" in UI and exports | CorrelationMatrix.disclaimer field (default value); display in quality summary card; include in JSON exports; educational framing in UI |
| CORR-06 | System computes internal consistency flags (mean inter-item correlation in 0.15-0.50 optimal range) | Calculate mean of off-diagonal correlations; 0.15-0.50 for broad constructs (higher for narrow); internal_consistency_flag field ("optimal", "too_low", "too_high") |
| UI-01 | User can view correlation heatmap for generated item set using visx visualization | @visx/heatmap HeatmapRect component; custom color scale (scaleLinear with Psynalytics teal/lime gradient); responsive sizing; hover interactions |
| UI-05 | User can export correlation matrices in CSV and JSON formats with labeled rows/columns | CSV: square matrix with item text headers (truncated to 30 chars); separate CI file; JSON: full CorrelationMatrix object with disclaimer; export button in correlation panel |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| reliabiliPy | Latest (PyPI) | McDonald's omega calculation from correlation matrices | Only Python library implementing omega total/hierarchical via Schmid-Leiman; designed for correlation matrix input; handles factor analysis automatically |
| @visx/heatmap | 3.12.0 | Interactive heatmap visualization for React | Airbnb's production-grade D3 wrapper; low-level primitives for custom brand styling; 15KB bundle size; TypeScript support; Radix-compatible |
| @visx/scale | 3.12.0 | Color scale and axis scale creation | Required peer dependency for visx heatmap; provides scaleLinear for custom gradients |
| @visx/tooltip | 3.12.0 | Hover tooltip interactions | Visx-native tooltip system; integrates with heatmap hover events; portal-based positioning |
| NumPy | Latest (pip) | Correlation matrix numerical operations | Serverless-compatible (~30 MB); required by reliabiliPy for matrix algebra; standard scientific Python |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SciPy | Latest (if needed) | Advanced factor analysis (if reliabiliPy insufficient) | Only if reliabiliPy factor extraction proves inadequate; adds ~20 MB to serverless function |
| Pandas | Latest | DataFrame operations for reliabiliPy | reliabiliPy accepts pandas DataFrames for correlation matrices; may already be in dependencies |
| @visx/group | 3.12.0 | SVG grouping for heatmap layout | Positioning heatmap elements; required for visx patterns |
| @radix-ui/react-popover | 1.1.x | Detail popover for correlation cells | Click-to-expand reasoning display; matches existing Radix UI patterns |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| reliabiliPy | Manual Schmid-Leiman implementation | Custom code = higher risk; no maintained library; factor analysis from scratch is complex |
| visx | Recharts, Victory, Nivo | Pre-built charts lack brand customization; larger bundles (50-100 KB); less control over colors/interactions |
| GPT-5.2 high reasoning | GPT-4o standard | Cheaper but lower quality correlation estimates; reasoning models show better psychometric alignment per research |
| LLM linguistic uncertainty | Monte Carlo sampling | More compute-intensive; serverless timeout risk; linguistic verbalized uncertainty (LVU) shows better calibration per 2026 research |

**Installation:**

**Backend:**
```bash
pip install reliabilipy numpy pandas
```

**Frontend:**
```bash
npm install @visx/heatmap @visx/scale @visx/tooltip @visx/group @radix-ui/react-popover
```

## Architecture Patterns

### Recommended Project Structure

**Backend additions:**
```
backend/
├── agents/
│   └── correlation_estimator.py    # GPT-5.2 pairwise correlation estimation
├── analytics/
│   └── omega_calculator.py         # reliabiliPy wrapper for omega calculation
└── graph.py                         # correlation_node implementation (replace placeholder)
```

**Frontend additions:**
```
src/
├── components/
│   ├── CorrelationHeatmap.tsx       # Main heatmap component (visx HeatmapRect)
│   ├── CorrelationPanel.tsx         # Collapsible panel wrapper
│   ├── CorrelationSummaryCard.tsx   # Quality metrics card (omega, mean r, flags)
│   └── CorrelationTooltip.tsx       # Hover tooltip component
└── lib/
    └── export-correlation.ts        # CSV/JSON export functions for matrices
```

### Pattern 1: Batched Pairwise Correlation Estimation

**What:** GPT-5.2 estimates correlations for N×(N-1)/2 unique item pairs in batches to avoid timeout

**When to use:** For item counts > 10 (e.g., 20 items = 190 pairs)

**Example:**
```python
# backend/agents/correlation_estimator.py
from backend.agents.llm_factory import get_gpt52_analytics_model

async def estimate_pairwise_correlations(items: list[str], batch_size: int = 20) -> list[CorrelationCell]:
    """Estimate correlations using GPT-5.2 in batches.

    Args:
        items: List of item texts
        batch_size: Number of pairs per LLM call (default 20 to stay under token limits)

    Returns:
        List of CorrelationCell objects with correlation, ci_low, ci_high
    """
    llm = get_gpt52_analytics_model()

    # Generate all unique pairs
    pairs = [(i, j) for i in range(len(items)) for j in range(i+1, len(items))]

    cells = []
    for batch_start in range(0, len(pairs), batch_size):
        batch = pairs[batch_start:batch_start + batch_size]

        # Structured prompt requesting correlation + 95% CI
        prompt = f"""You are a psychometric expert estimating correlations between survey items.

For each item pair below, estimate:
1. Pearson correlation coefficient (-1 to +1)
2. 95% confidence interval [low, high]

Consider semantic similarity, construct overlap, and typical survey response patterns.

Items:
{format_items_for_prompt(items)}

Pairs to estimate:
{format_pairs_for_prompt(batch, items)}

Return JSON array:
[{{"i": 0, "j": 1, "r": 0.65, "ci_low": 0.52, "ci_high": 0.76, "reasoning": "..."}}]
"""

        response = await llm.ainvoke(prompt)
        batch_cells = parse_correlation_response(response.content)
        cells.extend(batch_cells)

    return cells
```

### Pattern 2: McDonald's Omega Calculation from Correlation Matrix

**What:** Use reliabiliPy to calculate omega_total from the LLM-estimated correlation matrix

**When to use:** After pairwise correlations are estimated, before returning FinalOutput

**Example:**
```python
# backend/analytics/omega_calculator.py
import pandas as pd
from reliabilipy import reliability_analysis
from backend.schemas import CorrelationMatrix, CorrelationCell

def calculate_omega(cells: list[CorrelationCell], num_items: int) -> dict:
    """Calculate McDonald's omega from correlation cells.

    Args:
        cells: List of CorrelationCell objects (upper triangle of matrix)
        num_items: Number of items in the scale

    Returns:
        Dict with omega_total, omega_hierarchical, mean_inter_item_correlation
    """
    # Build full correlation matrix (symmetric)
    matrix = [[1.0 if i == j else 0.0 for j in range(num_items)] for i in range(num_items)]

    for cell in cells:
        matrix[cell.item_i_index][cell.item_j_index] = cell.correlation
        matrix[cell.item_j_index][cell.item_i_index] = cell.correlation  # Symmetric

    # Convert to pandas DataFrame for reliabiliPy
    df = pd.DataFrame(matrix, columns=[f"Item_{i+1}" for i in range(num_items)])

    # Calculate reliability metrics
    analysis = reliability_analysis(correlations_matrix=df)
    analysis.fit()

    # Extract omega total (primary metric per user decision)
    omega_total = analysis.omega_total

    # Calculate mean inter-item correlation (exclude diagonal)
    off_diagonal = [cell.correlation for cell in cells]
    mean_r = sum(off_diagonal) / len(off_diagonal)

    # Internal consistency flag
    if mean_r < 0.15:
        flag = "too_low_redundancy_risk"
    elif mean_r > 0.50:
        flag = "too_high_homogeneity_concern"
    else:
        flag = "optimal_range"

    return {
        "omega_total": omega_total,
        "mean_inter_item_correlation": mean_r,
        "internal_consistency_flag": flag,
    }
```

### Pattern 3: Visx Heatmap with Custom Psynalytics Colors

**What:** Render correlation matrix as interactive heatmap using visx primitives with brand colors

**When to use:** In CorrelationPanel component when user expands the panel

**Example:**
```tsx
// src/components/CorrelationHeatmap.tsx
import { HeatmapRect } from '@visx/heatmap';
import { scaleLinear } from '@visx/scale';
import { Group } from '@visx/group';
import type { CorrelationMatrix } from '@/lib/types';

interface Props {
  matrix: CorrelationMatrix;
  itemTexts: string[];
}

export function CorrelationHeatmap({ matrix, itemTexts }: Props) {
  const numItems = itemTexts.length;
  const cellSize = 40; // pixels per cell

  // Build 2D data structure from flat cells list
  const heatmapData = Array.from({ length: numItems }, (_, i) => ({
    bin: i,
    bins: Array.from({ length: numItems }, (_, j) => {
      if (i === j) return { bin: j, count: 1.0 }; // Diagonal = 1.0
      const cell = matrix.cells.find(c =>
        (c.item_i_index === i && c.item_j_index === j) ||
        (c.item_i_index === j && c.item_j_index === i)
      );
      return { bin: j, count: cell?.correlation ?? 0 };
    })
  }));

  // Custom Psynalytics gradient: teal (negative) -> white (zero) -> lime (positive)
  const colorScale = scaleLinear<string>({
    domain: [-1, 0, 1],
    range: ['#008da1', '#ffffff', '#a7d12b'], // --primary, white, --accent
  });

  return (
    <svg width={numItems * cellSize} height={numItems * cellSize}>
      <HeatmapRect
        data={heatmapData}
        xScale={(d) => d.bin * cellSize}
        yScale={(d) => d.bin * cellSize}
        colorScale={colorScale}
        binWidth={cellSize}
        binHeight={cellSize}
      >
        {(heatmap) =>
          heatmap.map((bins) =>
            bins.map((bin) => (
              <rect
                key={`heatmap-rect-${bin.row}-${bin.column}`}
                width={bin.width}
                height={bin.height}
                x={bin.x}
                y={bin.y}
                fill={bin.color}
                stroke="#0b2a34"
                strokeWidth={1}
                onMouseEnter={() => showTooltip(bin)}
                onClick={() => showPopover(bin)}
                style={{ cursor: 'pointer' }}
              />
            ))
          )
        }
      </HeatmapRect>
    </svg>
  );
}
```

### Pattern 4: LLM Linguistic Verbalized Uncertainty for CI

**What:** Use GPT-5.2's natural language confidence expressions to extract CI bounds

**When to use:** When estimating correlations (more reliable than token probabilities per 2026 research)

**Example:**
```python
# backend/agents/correlation_estimator.py
def parse_correlation_response(response_text: str) -> list[CorrelationCell]:
    """Parse LLM response extracting correlations and linguistic uncertainty.

    LLM outputs: "I estimate r = 0.65 with 95% CI [0.52, 0.76]"
    We extract structured CI from linguistic markers.
    """
    import json

    # GPT-5.2 structured output (JSON mode)
    data = json.loads(response_text)

    cells = []
    for item in data:
        cell = CorrelationCell(
            item_i_index=item["i"],
            item_j_index=item["j"],
            correlation=item["r"],
            ci_low=item["ci_low"],
            ci_high=item["ci_high"],
        )
        cells.append(cell)

    return cells
```

### Anti-Patterns to Avoid

- **Computing omega from raw items without correlation matrix:** Omega requires factor analysis, which needs either response data OR correlation matrix. Cannot compute from item text alone (use correlation matrix from LLM estimates).

- **Using Cronbach's alpha instead of McDonald's omega:** User explicitly chose omega over alpha. Alpha assumes tau-equivalence (equal loadings) which is rarely true. Stick to omega.

- **Single LLM call for all N×(N-1)/2 pairs:** For 20 items (190 pairs), single prompt exceeds token limits and timeouts. Use batched estimation (20-30 pairs per call).

- **Standard academic heatmap colors (blue-red):** User wants Psynalytics brand colors (teal-white-lime gradient). Custom scaleLinear with CSS variable colors.

- **Blocking item generation on low omega:** Warnings are informational, not blocking. Synthetic correlations are estimates, not empirical data. Display flags but allow export.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| McDonald's omega calculation | Custom Schmid-Leiman transformation | reliabiliPy library | Factor analysis is mathematically complex; Schmid-Leiman requires multiple rotation steps; reliabiliPy handles edge cases (non-positive definite matrices, convergence issues) |
| Correlation matrix symmetry validation | Manual upper/lower triangle checks | reliabiliPy expects pandas DataFrame (auto-validates) | Library enforces matrix properties; handles numerical precision issues; validates positive-definiteness |
| Heatmap color interpolation | Manual RGB lerp | visx scaleLinear | D3-grade color science; perceptually uniform gradients; handles edge cases (NaN, infinity) |
| Confidence interval bootstrapping | Custom resampling logic | LLM linguistic verbalized uncertainty | No response data for bootstrap; LLM linguistic expressions better calibrated than token probs per 2026 research |
| CSV matrix export formatting | Custom string concatenation | Follow export.ts RFC 4180 patterns | Edge cases: quoted cells, commas in item text, encoding issues; existing export.ts handles these correctly |

**Key insight:** Factor analysis and correlation matrix operations are numerically sensitive with many edge cases (singular matrices, convergence failures, numerical instability). Psychometric libraries like reliabiliPy handle these professionally; custom implementations will hit edge cases in production.

## Common Pitfalls

### Pitfall 1: Non-Positive Definite Correlation Matrices

**What goes wrong:** LLM-estimated correlations may produce mathematically invalid matrices (e.g., Item A-B = 0.8, B-C = 0.8, A-C = 0.2 violates triangle inequality). Factor analysis fails with cryptic errors.

**Why it happens:** LLM estimates pairwise correlations independently without enforcing global matrix constraints.

**How to avoid:**
1. Use reliabiliPy's built-in matrix validation (raises clear error if non-positive definite)
2. Implement nearest positive-definite projection (SciPy `nearest_positive_definite` if needed)
3. Add retry logic: if matrix invalid, prompt LLM to revise inconsistent pairs

**Warning signs:**
- reliabiliPy raises `ValueError: correlation matrix must be positive definite`
- Omega values > 1.0 or < 0.0 (mathematically impossible)
- Factor analysis convergence warnings

### Pitfall 2: Serverless Function Size Exceeding 250 MB

**What goes wrong:** Adding NumPy + reliabiliPy + SciPy pushes serverless function over Vercel's 250 MB limit, blocking deployment.

**Why it happens:** NumPy (~30 MB), SciPy (~60 MB if added), plus existing stack (~100 MB) approaches limit.

**How to avoid:**
1. Deploy to Vercel preview FIRST in Phase 8 to check function size
2. Avoid adding SciPy unless reliabiliPy proves insufficient
3. Use `vercel inspect` to check deployment bundle size
4. Fallback plan: client-side omega calculation (WebAssembly NumPy) if serverless too large

**Warning signs:**
- Vercel build fails with "Serverless Function has exceeded the unzipped maximum size of 250 MB"
- Slow cold starts (>10s indicate large bundle)
- Local `du -sh .vercel/output/functions/` shows >200 MB

### Pitfall 3: Timeout on Large Item Sets

**What goes wrong:** Generating 50 items (1,225 pairs) times out Vercel's 300s limit with sequential LLM calls.

**Why it happens:** Each GPT-5.2 call takes 5-15s with reasoning effort; sequential processing for 1,225 pairs exceeds timeout.

**How to avoid:**
1. Batch pairs into groups of 20-30 (reduces LLM calls from 1,225 to ~50)
2. Use asyncio.gather for parallel batches (3-5 concurrent calls)
3. Stream partial results via SSE (show heatmap progressively as batches complete)
4. Document in UI: "Correlation analysis may take 60-120s for large item sets"

**Warning signs:**
- SSE stream stops mid-correlation estimation
- Frontend shows timeout error after 300s
- Backend logs show "Request timeout" during correlation_node

### Pitfall 4: Heatmap Color Accessibility

**What goes wrong:** Teal-white-lime gradient fails WCAG contrast requirements; colorblind users cannot distinguish positive/negative correlations.

**Why it happens:** User-specified brand colors optimized for aesthetics, not accessibility.

**How to avoid:**
1. Add color legend showing correlation scale (-1 to +1 with color samples)
2. Display correlation value on hover (not color-only)
3. Test with colorblindness simulator (Chrome DevTools)
4. Consider adding pattern overlays (stripes for negative, dots for positive) as optional toggle

**Warning signs:**
- User testing reveals confusion about positive vs negative correlations
- Low contrast ratios in automated accessibility audit
- Heatmap difficult to read in dark mode

### Pitfall 5: Exporting Correlation Matrix with Truncated Item Text

**What goes wrong:** CSV headers use full item text (80+ characters), breaking Excel column width and making matrix unreadable.

**Why it happens:** Item texts are verbose; CSV has no column width constraints.

**How to avoid:**
1. Truncate item text to 30 characters in CSV headers ("I feel confident when..." → "I feel confident when…")
2. Include full item text in separate column or metadata section
3. Add index numbers (Item 1, Item 2) as alternate headers
4. Document truncation in CSV metadata row

**Warning signs:**
- CSV opened in Excel shows overlapping headers
- User feedback: "Can't read the matrix"
- Item text wraps in spreadsheet, making matrix hard to interpret

## Code Examples

Verified patterns from official sources and established libraries:

### McDonald's Omega Calculation with reliabiliPy

```python
# Source: https://pypi.org/project/reliabiliPy/
# backend/analytics/omega_calculator.py

import pandas as pd
from reliabilipy import reliability_analysis

def calculate_omega_from_correlation_matrix(correlation_cells: list, num_items: int) -> dict:
    """Calculate McDonald's omega total from LLM-estimated correlations.

    Args:
        correlation_cells: List of CorrelationCell objects (upper triangle)
        num_items: Total number of items

    Returns:
        Dict with omega_total, omega_hierarchical, mean_inter_item_r
    """
    # Build symmetric correlation matrix
    matrix = [[1.0 if i == j else 0.0 for j in range(num_items)] for i in range(num_items)]

    for cell in correlation_cells:
        i, j = cell.item_i_index, cell.item_j_index
        matrix[i][j] = cell.correlation
        matrix[j][i] = cell.correlation  # Symmetric

    # Convert to pandas DataFrame (reliabiliPy requirement)
    df = pd.DataFrame(
        matrix,
        columns=[f"Item_{idx+1}" for idx in range(num_items)],
        index=[f"Item_{idx+1}" for idx in range(num_items)]
    )

    # Calculate reliability measures
    analysis = reliability_analysis(correlations_matrix=df)
    analysis.fit()

    # Extract omega total (primary metric)
    omega_total = float(analysis.omega_total)
    omega_hierarchical = float(analysis.omega_hierarchical)

    # Mean inter-item correlation (exclude diagonal)
    off_diagonal_sum = sum(cell.correlation for cell in correlation_cells)
    mean_r = off_diagonal_sum / len(correlation_cells)

    return {
        "omega_total": omega_total,
        "omega_hierarchical": omega_hierarchical,
        "mean_inter_item_correlation": mean_r,
    }
```

### Visx Heatmap with Psynalytics Brand Colors

```tsx
// Pattern derived from: https://codesandbox.io/examples/package/@visx/heatmap
// src/components/CorrelationHeatmap.tsx

import { HeatmapRect } from '@visx/heatmap';
import { scaleLinear } from '@visx/scale';
import { Group } from '@visx/group';
import type { CorrelationMatrix } from '@/lib/types';

interface HeatmapData {
  bin: number;
  bins: { bin: number; count: number }[];
}

interface CorrelationHeatmapProps {
  matrix: CorrelationMatrix;
  itemTexts: string[];
  onCellClick?: (i: number, j: number) => void;
}

export function CorrelationHeatmap({ matrix, itemTexts, onCellClick }: CorrelationHeatmapProps) {
  const numItems = itemTexts.length;
  const cellSize = 40;
  const width = numItems * cellSize;
  const height = numItems * cellSize;

  // Transform flat cells list to 2D heatmap data structure
  const heatmapData: HeatmapData[] = Array.from({ length: numItems }, (_, i) => ({
    bin: i,
    bins: Array.from({ length: numItems }, (_, j) => {
      if (i === j) {
        return { bin: j, count: 1.0 }; // Diagonal always 1.0
      }
      const cell = matrix.cells.find(
        c => (c.item_i_index === i && c.item_j_index === j) ||
             (c.item_i_index === j && c.item_j_index === i)
      );
      return { bin: j, count: cell?.correlation ?? 0 };
    })
  }));

  // Psynalytics brand color scale: teal (negative) -> white (zero) -> lime (positive)
  const colorScale = scaleLinear<string>({
    domain: [-1, 0, 1],
    range: [
      'hsl(188, 100%, 32%)',  // --primary (teal)
      'hsl(0, 0%, 100%)',      // white
      'hsl(72, 69%, 50%)',     // --accent (lime)
    ],
  });

  return (
    <svg width={width} height={height} className="correlation-heatmap">
      <Group>
        <HeatmapRect
          data={heatmapData}
          xScale={(d) => d.bin * cellSize}
          yScale={(d) => d.bin * cellSize}
          colorScale={colorScale}
          binWidth={cellSize}
          binHeight={cellSize}
        >
          {(heatmap) =>
            heatmap.map((bins) =>
              bins.map((bin) => (
                <rect
                  key={`cell-${bin.row}-${bin.column}`}
                  className="heatmap-cell"
                  width={bin.width}
                  height={bin.height}
                  x={bin.x}
                  y={bin.y}
                  fill={bin.color}
                  stroke="var(--color-surface-0)"
                  strokeWidth={1}
                  onClick={() => onCellClick?.(bin.row, bin.column)}
                  style={{ cursor: 'pointer' }}
                />
              ))
            )
          }
        </HeatmapRect>
      </Group>
    </svg>
  );
}
```

### GPT-5.2 Pairwise Correlation Estimation with CI

```python
# backend/agents/correlation_estimator.py
import json
from typing import List
from backend.agents.llm_factory import get_gpt52_analytics_model
from backend.schemas import CorrelationCell

async def estimate_correlations_batch(
    items: List[str],
    pairs: List[tuple[int, int]]
) -> List[CorrelationCell]:
    """Estimate correlations for a batch of item pairs using GPT-5.2.

    Args:
        items: Full list of item texts
        pairs: List of (i, j) index tuples to estimate

    Returns:
        List of CorrelationCell objects with correlation + 95% CI
    """
    llm = get_gpt52_analytics_model()  # Uses "high" reasoning effort

    # Format pairs for prompt
    pair_descriptions = []
    for i, j in pairs:
        pair_descriptions.append(
            f"Pair ({i+1}, {j+1}):\n"
            f"  Item {i+1}: {items[i]}\n"
            f"  Item {j+1}: {items[j]}"
        )

    prompt = f"""You are a psychometric expert estimating correlations between survey items.

For each item pair below, estimate the Pearson correlation coefficient and 95% confidence interval.
Consider:
- Semantic similarity (similar wording suggests higher correlation)
- Construct overlap (items measuring same facet correlate higher)
- Typical survey response patterns (Likert scales show .3-.7 inter-item correlations)

Return JSON array with this exact structure:
[
  {{
    "i": 0,
    "j": 1,
    "correlation": 0.65,
    "ci_low": 0.52,
    "ci_high": 0.76,
    "reasoning": "Both items assess confidence; high semantic overlap suggests strong positive correlation"
  }}
]

Item pairs to estimate:
{chr(10).join(pair_descriptions)}

Respond with ONLY the JSON array, no additional text.
"""

    response = await llm.ainvoke(prompt)

    # Parse JSON response
    data = json.loads(response.content)

    cells = []
    for item in data:
        cell = CorrelationCell(
            item_i_index=item["i"],
            item_j_index=item["j"],
            correlation=item["correlation"],
            ci_low=item["ci_low"],
            ci_high=item["ci_high"],
        )
        cells.append(cell)

    return cells
```

### Correlation Matrix CSV Export

```typescript
// src/lib/export-correlation.ts
// Extends existing export.ts patterns

import type { CorrelationMatrix } from './types';

function truncateItemText(text: string, maxLength: number = 30): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 1) + '…';
}

export function exportCorrelationMatrixToCsv(
  matrix: CorrelationMatrix,
  itemTexts: string[]
): string {
  // UTF-8 BOM for Excel compatibility
  let csv = '\uFEFF';

  // Metadata header
  csv += `CORRELATION MATRIX (LLM-ESTIMATED)\n`;
  csv += `McDonald's Omega,${matrix.mcdonalds_omega.toFixed(3)}\n`;
  csv += `Mean Inter-Item r,${matrix.mean_inter_item_correlation.toFixed(3)}\n`;
  csv += `Internal Consistency,${matrix.internal_consistency_flag}\n`;
  csv += '\n';

  // Column headers (truncated item text)
  const headers = [''] // Empty corner cell
    .concat(itemTexts.map((text, i) => `Item ${i+1}: ${truncateItemText(text)}`));
  csv += headers.join(',') + '\n';

  // Build full symmetric matrix
  const n = itemTexts.length;
  const fullMatrix: number[][] = Array.from({ length: n }, () => Array(n).fill(0));

  // Populate diagonal with 1.0
  for (let i = 0; i < n; i++) {
    fullMatrix[i][i] = 1.0;
  }

  // Populate from cells (symmetric)
  for (const cell of matrix.cells) {
    const { item_i_index, item_j_index, correlation } = cell;
    fullMatrix[item_i_index][item_j_index] = correlation;
    fullMatrix[item_j_index][item_i_index] = correlation;
  }

  // Write matrix rows
  for (let i = 0; i < n; i++) {
    const rowLabel = `Item ${i+1}: ${truncateItemText(itemTexts[i])}`;
    const rowValues = fullMatrix[i].map(v => v.toFixed(3));
    csv += [rowLabel, ...rowValues].join(',') + '\n';
  }

  return csv;
}

export function exportConfidenceIntervalsToCsv(
  matrix: CorrelationMatrix,
  itemTexts: string[]
): string {
  // Separate CI file for clarity
  let csv = '\uFEFF';
  csv += 'CONFIDENCE INTERVALS (95%)\n\n';
  csv += 'Item_i,Item_j,Correlation,CI_Low,CI_High\n';

  for (const cell of matrix.cells) {
    const i = cell.item_i_index;
    const j = cell.item_j_index;
    const itemI = truncateItemText(itemTexts[i]);
    const itemJ = truncateItemText(itemTexts[j]);

    csv += `"${itemI}","${itemJ}",${cell.correlation.toFixed(3)},${cell.ci_low.toFixed(3)},${cell.ci_high.toFixed(3)}\n`;
  }

  return csv;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Cronbach's alpha as default reliability metric | McDonald's omega (total & hierarchical) | ~2015-2020 psychometric literature | Omega doesn't assume tau-equivalence (equal loadings); more accurate for multidimensional scales; Flora (2020) tutorial formalized best practices |
| Token probability for LLM confidence | Linguistic Verbalized Uncertainty (LVU) | 2024-2026 research | LVU shows better calibration and discrimination; linguistic hedging captures uncertainty token probs miss (Xiong et al., 2024) |
| Pre-built chart libraries (Recharts, Victory) | Low-level visx primitives | Ongoing (2020+) | visx provides D3-level control with React patterns; better for custom brand styling; smaller bundles (15KB vs 50-100KB) |
| Manual factor analysis for omega | reliabiliPy library | 2021+ (library release) | Handles Schmid-Leiman transformation automatically; validates matrix properties; production-grade edge case handling |
| Sequential LLM calls for large tasks | Batched + parallel async calls | 2023+ (serverless timeout awareness) | Reduces timeout risk; maintains cost efficiency; enables progress streaming |

**Deprecated/outdated:**
- **Cronbach's alpha as sole reliability metric:** Still widely used but psychometrically inferior to omega; assumes equal loadings which is rarely true; omega is recommended replacement (Flora, 2020; McNeish, 2018)
- **Factor analysis from scratch in Python:** reliabiliPy provides maintained, tested implementation; custom Schmid-Leiman is error-prone
- **Blue-white-red heatmap colors:** Academic convention but not accessible; brand-specific palettes + explicit legends are better UX

## Validation Architecture

> Nyquist validation enabled per .planning/config.json

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None — pytest auto-discovery in tests/ directory |
| Quick run command | `pytest tests/test_correlation.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORR-01 | GPT-5.2 generates pairwise correlation matrix from item texts | integration | `pytest tests/test_correlation_estimation.py::test_estimate_correlations -x` | ❌ Wave 0 |
| CORR-02 | reliabiliPy calculates omega_total from correlation matrix with ω ≥ 0.70 threshold | unit | `pytest tests/test_omega_calculator.py::test_calculate_omega -x` | ❌ Wave 0 |
| CORR-03 | Each CorrelationCell includes ci_low and ci_high fields | unit | `pytest tests/test_schemas.py::test_correlation_cell_ci -x` | ❌ Wave 0 |
| CORR-04 | Benchmark validation: LLM-estimated correlations vs published matrices achieve r > 0.6 | integration | `pytest tests/test_correlation_calibration.py::test_benchmark_agreement -x` | ❌ Wave 0 |
| CORR-05 | CorrelationMatrix.disclaimer field populated with default text | unit | `pytest tests/test_schemas.py::test_correlation_disclaimer -x` | ❌ Wave 0 |
| CORR-06 | Internal consistency flag computed from mean inter-item r (0.15-0.50 range) | unit | `pytest tests/test_omega_calculator.py::test_internal_consistency_flag -x` | ❌ Wave 0 |
| UI-01 | Visx heatmap renders with Psynalytics brand colors | manual-only | N/A — requires visual inspection of gradient | Manual QA |
| UI-05 | Correlation matrix CSV export produces square matrix with truncated headers | unit | `pytest tests/test_export_correlation.py::test_csv_matrix_export -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_correlation_estimation.py tests/test_omega_calculator.py -x` (core correlation logic)
- **Per wave merge:** `pytest tests/ -v` (full suite including integration)
- **Phase gate:** Full suite green + manual heatmap visual QA before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_correlation_estimation.py` — covers CORR-01 (GPT-5.2 pairwise estimation)
- [ ] `tests/test_omega_calculator.py` — covers CORR-02, CORR-06 (omega calculation, consistency flags)
- [ ] `tests/test_correlation_calibration.py` — covers CORR-04 (benchmark validation)
- [ ] `tests/test_export_correlation.py` — covers UI-05 (CSV export)
- [ ] Extend `tests/test_schemas.py` — add CORR-03, CORR-05 test cases for CorrelationCell/CorrelationMatrix
- [ ] Framework already installed (pytest 9.0.2) — no installation needed

## Open Questions

### 1. Calibration Scale Selection Criteria

**What we know:** Need 5 published scales with known correlation matrices across domains (personality, clinical, social, organizational, attitudes)

**What's unclear:**
- Which specific scales have published correlation matrices (not just alpha values)?
- Are correlation matrices available in peer-reviewed literature or only in test manuals?
- Should scales be open-access (IPIP, PHQ-9) or include proprietary scales with published psychometrics?

**Recommendation:**
- Start with well-documented open-access scales (IPIP-NEO for personality, PHQ-9 for clinical)
- Use backend/evaluation/benchmark_loader.py's Web Surfer integration to search for published correlation matrices
- Validate scale selection in Wave 0: manually verify 5 scales have accessible correlation matrix data before implementing estimation logic

### 2. Non-Positive Definite Matrix Handling

**What we know:** LLM pairwise estimates may produce invalid correlation matrices that violate mathematical constraints

**What's unclear:**
- How often does this occur in practice with GPT-5.2 reasoning?
- Should we use nearest-positive-definite projection (adds SciPy dependency) or retry with LLM?
- Does reliabiliPy have built-in matrix correction, or does it fail hard?

**Recommendation:**
- Implement try/catch around reliabiliPy with clear error message
- Log non-positive definite cases to monitor frequency
- If rare (<5% of runs), fail gracefully with null correlation_matrix in FinalOutput
- If common (>10%), add SciPy nearest-positive-definite projection in Wave 1

### 3. Confidence Interval Calibration

**What we know:** LLM linguistic verbalized uncertainty (LVU) is better than token probabilities, but absolute calibration unknown

**What's unclear:**
- Are GPT-5.2's self-reported 95% CIs actually 95% coverage in practice?
- Should we validate CI calibration against benchmark scales?
- How wide are typical CIs (narrow = overconfident, wide = underconfident)?

**Recommendation:**
- Accept LLM-reported CIs as-is for Phase 8 (display them without adjustment)
- Add CI width analysis to benchmark validation (CORR-04): measure actual coverage vs claimed 95%
- Document in UI: "Confidence intervals are LLM self-assessments, not empirically validated"
- Defer CI recalibration to future work if coverage systematically poor

### 4. Serverless Bundle Size with NumPy

**What we know:** NumPy ~30 MB, current stack ~100 MB, Vercel limit 250 MB (120 MB buffer)

**What's unclear:**
- Does reliabiliPy add significant transitive dependencies beyond NumPy?
- Will Vercel's Python bundler tree-shake unused NumPy modules?
- Should we test serverless size in Wave 0 or wait until full implementation?

**Recommendation:**
- Deploy to Vercel preview EARLY in Phase 8 (after Wave 0 schema changes)
- Use `vercel inspect` to check actual function size before full correlation implementation
- If >200 MB, investigate alternatives: client-side omega calculation, lighter omega library, or factor analysis simplification
- Document fallback plan: if serverless too large, correlation analysis becomes client-side TypeScript with TensorFlow.js

## Sources

### Primary (HIGH confidence)

- [reliabiliPy PyPI](https://pypi.org/project/reliabiliPy/) - McDonald's omega implementation details, correlation matrix input format
- [reliabiliPy GitHub](https://github.com/rafaelvalero/reliabiliPy) - Source code, Schmid-Leiman methodology
- [McDonald's Omega: Test Reliability Guide | Cogn-IQ](https://www.cogn-iq.org/learn/theory/mcdonalds-omega/) - Omega definition, threshold guidance
- [Use Omega Rather than Cronbach's Alpha for Estimating Reliability (Hayes & Coutts, 2020)](https://www.tandfonline.com/doi/abs/10.1080/19312458.2020.1718629) - Rationale for omega over alpha
- [Your Coefficient Alpha Is Probably Wrong (Flora, 2020)](https://journals.sagepub.com/doi/full/10.1177/2515245920951747) - Omega tutorial, best practices
- [visx/heatmap npm](https://www.npmjs.com/package/@visx/heatmap) - Installation, version 3.12.0
- [visx/heatmap documentation](https://airbnb.io/visx/docs/heatmap) - HeatmapRect API, examples
- [Vercel Serverless Function Size Limit](https://vercel.com/kb/guide/troubleshooting-function-250mb-limit) - 250 MB uncompressed limit, NumPy sizing

### Secondary (MEDIUM confidence)

- [A psychometric framework for evaluating LLMs (Nature Machine Intelligence, 2025)](https://www.nature.com/articles/s42256-025-01115-6) - LLM psychometric validation methodology, reliability metrics
- [Psychometric properties and detectability of GPT-4o items (npj Digital Medicine, 2026)](https://www.nature.com/articles/s41746-025-02313-7) - Item difficulty parameters, GPT-4o vs human-authored
- [Uncertainty Quantification in LLMs (ACM SIGKDD, 2026)](https://dl.acm.org/doi/10.1145/3711896.3736569) - Confidence calibration, linguistic verbalized uncertainty
- [Can LLMs Express Their Uncertainty? (OpenReview, 2023)](https://openreview.net/forum?id=gjeQKFxFpZ) - LVU vs token probabilities, empirical calibration
- [Internal consistency measurement (Wikipedia)](https://en.wikipedia.org/wiki/Internal_consistency) - Mean inter-item correlation optimal ranges
- [Does item homogeneity indicate internal consistency (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/019188699190115R) - 0.15-0.50 range for inter-item r, redundancy concerns

### Tertiary (LOW confidence)

- [visx heatmap examples (CodeSandbox)](https://codesandbox.io/examples/package/@visx/heatmap) - Community examples, not official docs
- [8 Top React Chart Libraries (Querio, 2026)](https://querio.ai/articles/top-react-chart-libraries-data-visualization) - visx bundle size comparison
- [LLM Benchmarks 2026](https://llm-stats.com/benchmarks) - General benchmarking trends
- [Leveraging LLM-Respondents for Item Evaluation (arXiv, 2024)](https://arxiv.org/html/2407.10899) - LLM as synthetic respondents, item parameter estimates

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM-HIGH - reliabiliPy and visx are established libraries with clear documentation; NumPy serverless sizing needs empirical validation via Vercel preview
- Architecture: HIGH - Patterns verified against existing MAPIG codebase (llm_factory.py, export.ts, QualityChecksPanel.tsx); reliabiliPy usage confirmed via PyPI docs
- Pitfalls: MEDIUM - Non-positive definite matrices and serverless timeouts are known issues in psychometrics/serverless domains but specific frequency with GPT-5.2 unknown until implementation

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days — stable psychometric domain, but LLM capabilities evolve rapidly)

---

*Phase: 08-synthetic-correlation-analysis*
*Researcher: Claude Sonnet 4.5*
*Context: User decisions from CONTEXT.md constrain research scope (McDonald's omega over alpha, Psynalytics brand colors, visx library locked)*
