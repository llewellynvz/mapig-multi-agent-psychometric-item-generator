# MAPIG: Multi-Agent Psychometric Item Generator

Evidence-bounded, human-in-the-loop item generation for psychometric scale development.

MAPIG is a multi-agent platform for designing and generating psychometrically sound assessment items, combining established test-development principles with modern LLM orchestration. It guides you from precise construct and constraint definition through a graph of specialized agents that draft, review, and revise items while recording an auditable evidence trail for every run. Human reviewers stay in the loop via feedback rounds that refine items against the construct definition, constraints, and approved sources, so the final output is transparent, reproducible, and ready for empirical validation.

![MAPIG architecture](./public/mapig_arc.png)

## Video Tutorial

[![MAPIG Tutorial](https://img.youtube.com/vi/E7Hq1bwF5sk/maxresdefault.jpg)](https://youtu.be/E7Hq1bwF5sk?si=FKhQORlNa61qjNcP)

Watch the full walkthrough tutorial showing how to use MAPIG to generate psychometric items.

## Overview

MAPIG is a multi-agent workflow for drafting and refining psychometric items with explicit auditability.

It is designed for teams that need:
- Transparent evidence usage
- Repeatable generation runs
- Structured review and revision loops
- Human feedback integration before finalization

MAPIG generates candidate items and review artifacts. It supports expert judgment; it does not replace validation, piloting, or psychometric evaluation.

## Product Highlights

![Landing Page](./public/landing_page.png)
- Guided UI flow: `Setup -> Run -> Results`
- Run recovery: active sessions can be restored after browser close/reopen
- Human feedback loop: rerun using prior items + reviewer feedback
- Evidence trail: grouped, clickable web sources and local curated references
- Audit metadata on every run: `thread_id`, `run_id`, `iteration_count`, `stop_reason`, model info
- Inter-item correlation heatmap with McDonald's omega and consistency metrics
- Instrument comparison: convergent/discriminant validity with published scales
- Score badges showing r-values and strength indicators with links to source papers

---

## The 13 Agents

MAPIG uses 13 specialized AI agents, each with a single job. Think of them as a team of experts passing work down an assembly line — one gathers evidence, another maps the construct's theoretical structure, one drafts items guided by that structure, others review, one decides if revisions are needed, and the final group checks how good the items really are.

### 🔍 Evidence Gathering

| Agent | What it does |
|-------|-------------|
| **Retrieval Agent** | Searches your **local approved sources** (curated research papers in `data/approved_sources/`) to find theoretical grounding for item writing. No LLM needed — pure text matching. |
| **Web Surfer** | Queries **Perplexity's academic search** to find published research — seminal papers, measurement precedents, and construct definitions from peer-reviewed journals. |

### 🧬 Construct Structure Analysis

| Agent | What it does |
|-------|-------------|
| **Facet Mapper** | The theoretical architect. Analyzes the retrieved evidence to **identify the construct's formal facet structure** before any items are written. For multi-dimensional constructs (e.g., Burnout), it identifies mutually exclusive sub-constructs and allocates items evenly across them. For unidimensional constructs (e.g., Life Satisfaction), it defines a strict "negative space fence" — what the construct is NOT — to prevent items from drifting into adjacent constructs. When running in unidimensional mode (the default), it also **flags any sub-constructs found in the literature** so users can generate items for those separately. This ensures every generated item has a clear theoretical home and prevents the common problem of all items being synonym substitutions of each other. |

### ✍️ Item Creation

| Agent | What it does |
|-------|-------------|
| **Item Writer** | The creative engine. Takes the construct definition, evidence, **facet mapping**, and constraints, then **drafts the actual Likert-type items** following psychometric best practices (no double-barreled items, appropriate reading level, positive keying, etc.). When facet mapping is provided, the writer is forced to distribute items across facets — ensuring semantic diversity and moderate inter-item correlations (r = 0.40–0.70) rather than near-identical items (r > 0.85). |
| **Validator** | The quality gate. **Scores every item on 4 dimensions** — correspondence (50%), distinctiveness (25%), clarity (15%), and specificity (10%). Items below 7.0/10 get sent back for regeneration. Detects and rejects "lazy" identical scores where all items receive the same rating — forces re-evaluation with a higher-accuracy model. |

### 🔬 Triple Review (runs in parallel)

| Agent | What it does |
|-------|-------------|
| **Linguistic Reviewer** | Hunts for **readability problems** — vague quantifiers ("often"), absolute terms ("always"), double-barreled items, ambiguous wording, and cultural idioms. |
| **Bias Reviewer** | Checks for **fairness across groups**. Detects 7 types of bias including cultural, socioeconomic, gender, and intersectional bias that could cause differential item functioning (DIF). |
| **Content Reviewer** | Tests **construct alignment** by simulating expert judges rating how well each item matches its intended construct — and whether it accidentally measures something else. |

### ⚖️ Decision & Revision

| Agent | What it does |
|-------|-------------|
| **Critic** | The decision-maker. Reads all reviewer feedback and decides: **accept the items or send them back for revision**. Uses adaptive thresholds that relax over iterations to prevent infinite loops. 90% of decisions are rule-based (zero tokens). |
| **Meta Editor** | The surgeon. When the critic says "revise", this agent **applies reviewer feedback precisely** — fixing only the flagged issues while preserving item count and facet balance. |

### 📊 Post-Finalization Analytics

| Agent | What it does |
|-------|-------------|
| **Correlation Estimator** | Estimates **how items relate to each other** using text embeddings and cosine similarity (validated method from Hommel & Arslan, 2024). Calculates McDonald's omega, mean inter-item correlation, and flags consistency issues — all without needing real survey data. |
| **Instrument Searcher** | Automatically **finds published scales** that measure the same or related constructs (e.g., finds the Satisfaction with Life Scale if you're building a life satisfaction measure). Used for benchmarking your items against established instruments. |
| **Validity Scorer** | Estimates **convergent and discriminant validity** — how well your items align with similar instruments (should be high) and how distinct they are from different constructs (should be low). Uses GPT-5.2 with high reasoning effort. |

---

## Pipeline Architecture

The generation pipeline flows through distinct phases, each handled by specialized agents:

```
START
  -> init_run
  -> retrieve_node          (evidence retrieval from local + Perplexity academic search)
  -> facet_mapper_node      (identify construct facets, allocate items per facet)
  -> item_writer_node       (draft items guided by facet structure)
  -> validation_node        (4-dimension scoring)
     -> [regenerate loop if items fail validation, up to 3 attempts]
  -> reviewers_fanout_node  (linguistic + bias + content review in parallel)
  -> critic_node            (accept / revise decision)
     -> [meta_editor -> reviewers -> critic loop, up to 3 iterations]
  -> finalize_node          (audit metadata, cost calculation)
  -> correlation_node       (embedding-based inter-item correlations)
  -> comparison_node        (find published instruments, score convergent validity)
  -> cross_construct_node   (discriminant validity against related constructs)
END
```

### Phase 1: Evidence Retrieval

Two channels provide the theoretical grounding that every generated item cites:

- **Local approved sources** (`data/approved_sources/*.md`): deterministic token-overlap search, no LLM needed
- **Perplexity academic search**: queries `sonar-pro` in academic mode with a domain allowlist (doi.org, psycnet.apa.org, etc.) to retrieve seminal papers, conceptual frameworks, measurement precedents, and boundary conditions

Evidence chunks are tagged with metadata — authors, theoretical model names, and identified dimensions — so the item writer can ground each item in specific literature.

### Phase 1.5: Facet Mapping

The **Facet Mapper Agent** analyzes the retrieved evidence to establish the construct's theoretical structure before any items are written. This is the key to generating diverse, non-redundant items.

**Why this matters**: Without facet mapping, LLMs tend to generate items that are synonym substitutions of each other (e.g., "I shift my thinking", "I change my methods", "I adjust my plans"). These produce inter-item correlations above 0.85 — essentially the same item asked 7 different ways. The facet mapper forces structural diversity by identifying distinct theoretical dimensions and allocating items across them.

**How it works**:
- **Unidimensional mode** (default): The construct is treated as a single factor. All items target the full construct. If the literature reveals sub-constructs (e.g., Burnout has Exhaustion, Cynicism, Inefficacy), they are **flagged as suggestions** for the user to generate items for separately — not split into sub-scales in the current run. A strict "negative space fence" defines what the construct is NOT, preventing drift into adjacent constructs.
- **Multi-dimensional mode** (user toggle): Items are distributed evenly across identified sub-constructs. Each facet gets `item_count / N` items with mutually exclusive descriptions and boundary exclusions.

The user controls this via a "Construct structure" toggle on the setup form.

### Phase 2: Item Drafting

The **Item Writer Agent** receives the construct definition, target population, constraints, **facet mapping**, and evidence chunks, then generates Likert-type items following five decades of psychometric principles:

- Facet-guided item generation: when facet mapping is provided, items are distributed across facets with explicit behavioral referent variation
- Unidimensional focus per item
- Positive keying only (no reverse-coded items, per current best practice)
- Reading level matched to population (6th-8th grade general, 5th-6th clinical, 10th-12th professional)
- No double-barreled items, idioms, or vague quantifiers
- Each item includes a rationale (max 50 words) citing specific evidence sources

The item writer always uses Claude Sonnet 4.5 for generation quality, regardless of the `APP_MODE` setting.

### Phase 3: Validation Gate

The **Validator Agent** acts as an LLM-as-judge, scoring every item on four weighted dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Correspondence | 50% | Does the item match the construct definition? |
| Distinctiveness | 25% | Is it clearly this construct, not a neighbor? |
| Clarity | 15% | Unambiguous, concise, comprehensible? |
| Specificity | 10% | Concrete language, avoids vague quantifiers? |

Items scoring below 7.0 (weighted) are regenerated — only the failed items, not the whole batch. This selective regeneration runs up to 3 attempts with escalating model power:

- Attempt 1: Claude Sonnet 4.5 (cost-effective)
- Attempts 2-3: Claude Opus 4.6 (highest accuracy when items are stubborn)

When the ChatGPT critics toggle is enabled, GPT-4o handles validation instead.

### Phase 4: Triple-Reviewer Fanout

Three independent reviewers run **in parallel** (ThreadPoolExecutor), each receiving an abbreviated request payload (60% smaller — no evidence, examples, or retrieval settings):

#### Linguistic Reviewer
Hunts down clarity and readability issues:
- Vague quantifiers without time anchors ("often", "sometimes")
- Absolute terms ("always", "never") — auto-flagged severity 4
- Double-barreled items, ambiguous referents, negative stems
- Cultural idioms (when a cultural group is specified)
- Simulates a 5-point appropriateness rating; mean < 4.0 triggers revision

Uses Claude Sonnet 4.5 (or GPT-4o with ChatGPT toggle).

#### Bias Reviewer
Detects differential item functioning (DIF) risks across 7 bias types:

1. **Construct bias**: culture-bound meanings (e.g., "independence" in collectivist cultures)
2. **Linguistic bias**: idioms, complex vocabulary
3. **Cultural reference bias**: assumes culture-specific knowledge
4. **Socioeconomic bias**: assumes resources (e.g., "private workspace at home")
5. **Context access bias**: assumes work arrangements (e.g., "in-person collaboration")
6. **Protected attribute bias**: gender, race, ethnicity stereotypes
7. **Intersectional bias**: compounding effects across multiple types (auto-escalated to severity 4+)

Uses GPT-4o-mini by default (20x cheaper, acceptable fairness detection accuracy). Switches to GPT-4o with ChatGPT toggle.

#### Content Reviewer
Evaluates construct alignment by simulating 5 naive judges rating each item on:
- **Correspondence** (1-7): does it match the construct definition?
- **Distinctiveness** (1-7): is it clearly this construct, not a competitor?

Decision thresholds: correspondence mean < 6.0 or distinctiveness mean < 5.0 triggers revision. Also tracks facet coverage — flags imbalance greater than a 2:1 ratio.

Near-neighbor constructs checked (organizational default): job satisfaction, engagement, commitment, psychological safety, inclusion, social support, fairness, team cohesion.

Uses Claude Sonnet 4.5 (or GPT-4o with ChatGPT toggle).

### Phase 5: Critic Decision

The **Critic Agent** decides whether items are ready or need another revision cycle. It uses **adaptive thresholds** that relax over iterations to prevent infinite loops:

| Iteration | Mode | Accept max severity | Medium+ count allowed |
|-----------|------|--------------------|-----------------------|
| 0 (Round 1) | Strict | 2 | 0 |
| 1 (Round 2) | Thorough | 3 | 1 |
| 2+ (Round 3) | Final | 4 | 3 |

**Cost optimization**: 90% of decisions use zero tokens via rule-based logic:
- Clear accept (all comments below threshold) — 0 tokens
- Clear reject (max severity >= 4) — 0 tokens
- Strict/thorough mode with severity >= 3 — 0 tokens
- Only borderline cases (severity = 3 in final mode) fall through to the LLM

Hard stop at `MAX_ITERATIONS=3` prevents runaway loops.

### Phase 6: Meta-Editor Revision

When the critic says "revise", the **Meta Editor Agent** applies reviewer feedback surgically:

- **Smart comment filtering**: only passes severity >= 3 comments (40-60% token reduction)
- **Facet coverage enforcement**: infers 3-5 facets from the construct definition, tracks distribution (target: each facet >= 20% of items), prioritizes replacing overcovered facet items
- **Conflict resolution**: construct fidelity > bias > linguistic
- Preserves item count (no additions or deletions)

After editing, the revised items go back through the triple-reviewer fanout for re-evaluation.

### Phase 7: Finalization

Once the critic accepts (or hard stop fires), the **Finalize Node** assembles audit metadata:
- All reviewer comments (linguistic, bias, content)
- Validation results per item
- Token usage across all models
- Cost breakdown (Opus, Sonnet, GPT-4o, GPT-4o-mini)
- Stop reason, iteration count, thread/run IDs

---

## Post-Finalization Analytics

After items are finalized, three analytics nodes run to provide psychometric quality indicators.

### Embedding-Based Correlation Matrix

**File**: `backend/agents/correlation_estimator.py`

Rather than requiring empirical data collection, MAPIG estimates inter-item correlations using the validated methodology from Hommel & Arslan (2024). Their research demonstrated that sentence transformer embeddings with cosine similarity accurately predict real correlations (r = .71 for items, r = .89 for scales, r = .86 for reliability estimates).

**How it works**:
1. All generated items are embedded in a single batch using OpenAI's `text-embedding-3-small` model (1536-dimensional vectors)
2. The embedding vectors are L2-normalized, then a full NxN cosine similarity matrix is computed via matrix multiplication
3. Values are clamped to [-1.0, 1.0] to handle IEEE 754 floating point overshoot (a known issue where identical vectors can produce similarity values like 1.0000000000000004)
4. Upper-triangular pairs are extracted — for N items, this produces N*(N-1)/2 correlation cells

From the similarity matrix, MAPIG calculates:
- **McDonald's omega** (internal consistency): `omega = (k * r_bar) / (1 + (k-1) * r_bar)` where k = number of items and r_bar = mean inter-item correlation
- **Mean inter-item correlation**: average of all pairwise similarities
- **Internal consistency flag**: "too_low" if mean r < 0.15, "too_high" if mean r > 0.50, "optimal_range" otherwise

This approach is fast (single API call, pure matrix math), deterministic, and grounded in published empirical validation — no LLM hallucination risk.

**Reference**: Hommel, B. E., & Arslan, R. C. (2024). Language models accurately infer correlations between psychological items and scales from text alone. *European Journal of Psychological Assessment*. https://doi.org/10.1027/1015-5759/a000838

### Instrument Comparison & Convergent Validity

**Files**: `backend/agents/instrument_searcher.py`, `backend/agents/validity_scorer.py`

MAPIG automatically locates established instruments to benchmark your generated items against, supporting both convergent and discriminant validity estimation.

**Step 1: Find comparison instruments**

The Instrument Searcher queries Perplexity's academic search to find:
- A **convergent instrument** — one that directly measures the same or very similar construct (e.g., the Satisfaction with Life Scale for a "Life Satisfaction" construct)
- A **discriminant instrument** — one that measures a related-but-theoretically-distinct construct (e.g., the Flourishing Scale)

The search filters out commercial publishers (Pearson, PAR, MHS, WPS, Hogrefe) and extracts structured metadata: instrument name, authors, publication year, construct measured, and psychometric properties.

If Perplexity is unavailable, hardcoded fallbacks cover 5 psychological domains (personality, clinical, organizational, social, cognitive) with well-known open-access instruments.

**Step 2: Score convergent validity**

The Validity Scorer uses a **dual-direction LLM-as-judge** pattern to mitigate position bias:
1. **Forward**: "How well do the generated items align with [comparison instrument]?"
2. **Reverse**: "How well does [comparison instrument] align with the generated items?"
3. The two scores are averaged for the final convergent validity estimate (0.0-1.0)

This runs on GPT-5.2 with high reasoning effort for maximum accuracy.

**Step 3: Plagiarism detection**

A sentence-transformer model (`all-mpnet-base-v2`) computes semantic similarity between generated items and any published item texts. Items exceeding a 0.85 similarity threshold are flagged. This ensures generated items are original, not paraphrased copies of existing scales.

### Cross-Construct Discriminant Validity

**File**: `backend/agents/validity_scorer.py`

The Cross-Construct Node estimates how distinct your target construct is from related constructs:

1. Takes the discriminant instrument found in the comparison step
2. Uses the same dual-direction LLM-as-judge pattern to estimate the expected correlation between the target construct and the comparison construct
3. Flags: "concern" if |r| > 0.85 (dangerously high overlap), "adequate" otherwise
4. Provides a construct pair analysis with reasoning about where the conceptual boundaries lie

This tells you whether your generated items are measuring what you claim — or accidentally measuring something else.

---

## LLM Allocation Strategy

MAPIG allocates different models to different agents based on task complexity and cost:

| Agent | Default Model | With ChatGPT Toggle | Notes |
|-------|---------------|---------------------|-------|
| Facet Mapper | Claude Sonnet 4.5 | Claude Sonnet 4.5 | Construct structure analysis |
| Item Writer | Claude Sonnet 4.5 | Claude Sonnet 4.5 | Always Sonnet (quality-critical) |
| Validator | Sonnet 4.5 / Opus 4.6 | GPT-4o | Smart tiering: Sonnet first, Opus on retries |
| Linguistic Reviewer | Claude Sonnet 4.5 | GPT-4o | |
| Bias Reviewer | **GPT-4o-mini** | GPT-4o | 20x cheaper, acceptable accuracy |
| Content Reviewer | Claude Sonnet 4.5 | GPT-4o | |
| Critic | **GPT-4o-mini** | GPT-4o | 90% rule-based (0 tokens) |
| Meta Editor | Claude Sonnet 4.5 | Claude Sonnet 4.5 | Always Sonnet |
| Correlation Estimator | OpenAI embeddings | OpenAI embeddings | `text-embedding-3-small` |
| Validity Scorer | **GPT-5.2** | **GPT-5.2** | Reasoning model, high effort |

### Cost Optimizations
- **Smart validation**: Sonnet on attempt 1 (80% cheaper), Opus only on retries
- **Agent overrides**: Bias reviewer and critic use GPT-4o-mini (20x cheaper)
- **Rule-based critic**: 90% of accept/reject decisions use 0 tokens
- **Prompt caching**: Claude system prompts cached with 5-minute TTL (50% input reduction)
- **Comment filtering**: Meta-editor only receives severity >= 3 comments (40-60% reduction)
- **Abbreviated requests**: Reviewers receive minimal context (60% payload reduction)
- **Selective regeneration**: Only failed items are regenerated, not the entire batch

**Typical run cost** (10 items, 1-2 iterations): $0.80-$1.50

---

## API Contract

### Request

Required fields:
- `construct_name` — name of the psychological construct
- `construct_definition` — precise definition of what the construct is
- `target_population` — who will respond to the items
- `response_scale` — e.g., "5-point Likert: Strongly disagree to Strongly agree"

Optional fields:
- `item_count` (default `10`, range `2-50`)
- `constraints` — additional rules beyond baseline (additive, not replacement)
- `construct_exclusions` — what this construct is not, overlap boundaries
- `native_construct` — original language if construct was translated
- `example_item` — reference only, will not be copied
- `approved_domains` — per-request domain allowlist
- `exclude_sources` — domains to block
- `human_feedback` — free-text feedback from previous round
- `previous_items` — items from previous round for refinement
- `model_provider` — `"claude"` or `"openai"`
- `use_chatgpt_critics` — use GPT-4o for reviewer agents
- `is_unidimensional` (default `true`) — construct structure: true = single scale (sub-constructs flagged for separate runs), false = multi-dimensional (items distributed across sub-constructs)

### Response

- `final_items[]` — generated items with text, rationale, evidence citations, validation scores
- `audit` — thread_id, run_id, iteration_count, stop_reason, cost breakdown, model info
- `correlation_matrix` — pairwise correlations, omega, mean r, consistency flag
- `comparison_instruments[]` — convergent and discriminant instruments found
- `convergent_validity_score` — 0.0-1.0
- `cross_construct_analysis` — discriminant validity results, construct pair analysis
- `plagiarism_flags` — any items flagged for similarity to published items
- `linguistic_feedback`, `bias_feedback`, `content_feedback` — all reviewer comments

### Constraints Model

MAPIG applies constraints in two layers:

1. **Standard baseline constraints** (always active):
   - No double-barreled items
   - Avoid idioms
   - Minimize reading level
   - Positively keyed only

2. **Additional user constraints**:
   - Anything provided in `constraints` is added on top of the baseline
   - User constraints are treated as additive, not replacements

### Approved Sources Policy

MAPIG supports two evidence channels:
- Local curated sources in `data/approved_sources/`
- Web retrieval constrained to an approved domain allowlist

Web retrieval is blocked without allowlisted domains:
- Configure `PERPLEXITY_DOMAIN_FILTER` in `.env`, or
- Send `approved_domains` per request

---

## Quickstart

### 1) Install dependencies
```bash
# Backend (Python, via Poetry)
poetry install

# Frontend (Next.js, at repo root)
npm install
```

### 2) Configure environment
Create `.env` in the repository root.

Example:
```env
APP_MODE=openai
OPENAI_API_KEY=YOUR_KEY
OPENAI_MODEL=gpt-5.2

SEARCH_PROVIDER=hybrid
PERPLEXITY_API_KEY=YOUR_KEY
PERPLEXITY_BASE_URL=https://api.perplexity.ai/v2
PERPLEXITY_MODEL=sonar-pro
PERPLEXITY_SEARCH_MODE=academic
PERPLEXITY_MAX_RESULTS=20
PERPLEXITY_DOMAIN_FILTER=doi.org,psycnet.apa.org,link.springer.com,sciencedirect.com,onlinelibrary.wiley.com,tandfonline.com,journals.sagepub.com,academic.oup.com,cambridge.org
```

### 3) Run API only
```bash
uvicorn backend.main:app --reload
```

### 4) Run frontend + backend together
```bash
npm run dev
```

Override ports:
```bash
BACKEND_PORT=8001 FRONTEND_PORT=3001 npm run dev
```

API docs:
- `http://127.0.0.1:8000/docs`

## Example Request
```json
{
  "construct_name": "Workplace belonging",
  "construct_definition": "A sustained sense of being accepted, included, and valued as a legitimate member of one's work community.",
  "construct_exclusions": "Exclude job satisfaction and work engagement; keep focus on social inclusion and acceptance.",
  "target_population": "Full-time employees in a hybrid work setting",
  "response_scale": "5-point Likert: Strongly disagree to Strongly agree",
  "item_count": 10,
  "constraints": [
    "Avoid references to organization-specific jargon",
    "Keep items under 20 words"
  ],
  "approved_domains": [
    "doi.org",
    "psycnet.apa.org",
    "link.springer.com"
  ]
}
```

## Human Feedback Reruns
The UI supports iterative refinement:
1. Generate the initial item set
2. Add reviewer feedback
3. Rerun with:
- `human_feedback`
- `previous_items`

Feedback history is tracked per round in the Results view.

## Repository Structure

```
lmaig-langgraph/
├── api/                    # Vercel serverless entry point
│   └── index.py           # Exports FastAPI app for Vercel
├── backend/               # FastAPI application code
│   ├── main.py           # FastAPI app, lifespan, routes
│   ├── graph.py          # LangGraph workflow definition
│   ├── agents/           # Agent implementations
│   │   ├── facet_mapper.py
│   │   ├── item_writer.py
│   │   ├── validator.py
│   │   ├── linguistic_reviewer.py
│   │   ├── bias_reviewer.py
│   │   ├── content_reviewer.py
│   │   ├── critic.py
│   │   ├── meta_editor.py
│   │   ├── retrieval_agent.py
│   │   ├── web_surfer.py
│   │   ├── correlation_estimator.py
│   │   ├── instrument_searcher.py
│   │   ├── validity_scorer.py
│   │   ├── llm_factory.py
│   │   └── llm_utils.py
│   ├── analytics/         # Post-finalization analytics
│   │   ├── omega_calculator.py
│   │   └── similarity_calculator.py
│   ├── prompts/           # Agent system prompts
│   ├── schemas.py         # Pydantic models
│   └── settings.py        # Environment configuration
├── src/                   # Next.js source (App Router)
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   └── lib/              # Utilities, API client, types
├── public/               # Static assets
├── data/                 # Approved sources for evidence retrieval
├── tests/                # Backend tests
├── next.config.js        # Next.js configuration
├── vercel.json           # Vercel serverless config
├── package.json          # Frontend dependencies + scripts
├── pyproject.toml        # Backend dependencies (Poetry)
└── README.md
```

## Testing
Frontend production build:
```bash
npm run build
```

Backend tests (if installed):
```bash
pytest -q
```

## Deployment (Vercel)

MAPIG deploys as a **single Vercel project** with unified frontend and backend.

### Architecture
- **Frontend**: Next.js at repository root (pages in `/src`, public assets in `/public`)
- **Backend**: Python serverless functions in `/api` directory
- **Single domain**: Both frontend and backend served from same URL
- **No CORS needed**: Same-origin requests from frontend to `/api/*` endpoints

### Prerequisites
- Vercel account (Pro plan recommended for 300s timeout)
- API keys: `CLAUDE_API_KEY` and/or `OPENAI_API_KEY`
- Optional: `PERPLEXITY_API_KEY` for web search

### Deployment Steps

1. **Connect Repository to Vercel**
   - Import project from GitHub/GitLab
   - Framework Preset: Next.js (auto-detected)
   - Root Directory: `.` (leave as root)
   - Build Command: `npm run build` (auto-detected)

2. **Configure Environment Variables** (Vercel Dashboard)
   ```
   CLAUDE_API_KEY=<your-anthropic-key>
   OPENAI_API_KEY=<your-openai-key>
   APP_MODE=claude
   SEARCH_PROVIDER=perplexity
   PERPLEXITY_API_KEY=<your-perplexity-key>
   PERPLEXITY_DOMAIN_FILTER=doi.org,psycnet.apa.org,...
   NEXT_PUBLIC_API_URL=https://your-project.vercel.app
   ```

3. **Deploy**
   - Push to `main` branch for auto-deploy
   - Preview deployments created for PRs automatically

### Notes
- **Checkpointing**: In-memory only (MemorySaver) — session resumption not available after cold start
- **SSE Streaming**: Fully supported within 300s timeout (typical runs: 20-40s)
- **Cold Starts**: First request may take 3-8s; subsequent requests are fast
- **Function Timeout**: 300s default (Pro plan), configurable up to 800s with Fluid Compute

## Known Warnings

### Python 3.14 + Pydantic V1 Compatibility
```
Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
```
Comes from `langchain_core` which still imports `pydantic.v1`. Upstream issue — harmless, everything works.

### OpenAI SDK Serialization Warnings
```
PydanticSerializationUnexpectedValue: Expected `none` - serialized value may not be as expected
```
The OpenAI Python SDK's `ParsedResponse` objects contain a 21-variant discriminated union. Pydantic V2's serializer warns when trying each variant. The actual data parses correctly — these are purely cosmetic warnings. Suppressed at three levels: global filter in `backend/__init__.py`, pytest config in `pyproject.toml`, and call-site `warnings.catch_warnings()` context managers. See [openai/openai-python#2872](https://github.com/openai/openai-python/issues/2872).

## Contributing
Issues and pull requests are welcome for:
- Stability fixes
- Prompt and reviewer quality improvements
- UX and accessibility improvements
- Performance and observability upgrades

## Maintainer
Created by Prof. Llewellyn E. van Zyl (Ph.D)  
Website: https://www.psynalytics.com  
Personal: https://www.llewellynvanzyl.com
GitHub: https://github.com/llewellynvz

## License
This is proprietary software. Personal, academic, and internal research use is permitted. Redistribution and commercial use are not permitted.

## References

Hommel, B. E., & Arslan, R. C. (2024). Language models accurately infer correlations between psychological items and scales from text alone. *European Journal of Psychological Assessment*. https://doi.org/10.1027/1015-5759/a000838

Lee, P., Son, M., & Jia, Z. (2025). AI-powered automatic item generation for psychological tests: A conceptual framework for an LLM-based multi-agent AIG system. *Journal of Business and Psychology*, 1-29.
