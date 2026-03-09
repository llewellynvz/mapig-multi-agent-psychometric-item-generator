# MAPIG: Multi-Agent Psychometric Item Generator

Evidence-bounded, human-in-the-loop item generation for psychometric scale development.

MAPIG is a multi-agent platform for designing and generating psychometrically sound assessment items, combining established test-development principles with modern LLM orchestration. It guides you from precise construct and constraint definition through a graph of specialized agents that draft, review, and revise items while recording an auditable evidence trail for every run. Human reviewers stay in the loop via feedback rounds that refine items against the construct definition, constraints, and approved sources, so the final output is transparent, reproducible, and ready for empirical validation.

![MAPIG architecture](./mapig_arc.png)

## Overview
MAPIG is a multi-agent workflow for drafting and refining psychometric items with explicit auditability.

It is designed for teams that need:
- Transparent evidence usage
- Repeatable generation runs
- Structured review and revision loops
- Human feedback integration before finalization

MAPIG generates candidate items and review artifacts. It supports expert judgment; it does not replace validation, piloting, or psychometric evaluation.

## Product Highlights

![Landing Page](./landing_page.png)
- Guided UI flow: `Setup -> Run -> Results`
- Run recovery: active sessions can be restored after browser close/reopen
- Human feedback loop: rerun using prior items + reviewer feedback
- Evidence trail: grouped, clickable web sources and local curated references
- Audit metadata on every run: `thread_id`, `run_id`, `iteration_count`, `stop_reason`, model info

## Architecture
Core agents:

- Web Surfer Agent.
The academic detective. Scours peer-reviewed literature and psychometric databases to ground your construct in real science, identifies boundary conditions with similar constructs, and surfaces measurement precedents without reproducing copyrighted items.

- Item Writer Agent.
The master craftsperson. Generates Likert-type items following five decades of psychometric principles: unidimensional, bias-minimized, facet-balanced, and written at the right reading level for your population.

- Content Reviewer Agent
The construct purist. Simulates five independent judges rating each item on correspondence (does it measure what you claim?) and distinctiveness (or is it actually measuring something else?) with brutal honesty about contamination risks.

- Linguistic Reviewer Agent
The clarity enforcer. Hunts down ambiguous referents, vague quantifiers, double-barreled questions, and unnecessary abstractions that force respondents to guess what you mean.

- Bias Reviewer Agent
The fairness sentinel. Detects construct equivalence risks, flags differential item functioning concerns across demographic groups, and catches assumptions about work context, culture, language, and socioeconomic status that systematically disadvantage populations.

- Meta Editor Agent
The diplomatic synthesizer. Reconciles conflicting reviewer feedback, applies surgical edits while preserving construct coverage, and ensures the item set remains balanced across facets and psychometrically defensible.

- Critic Agent
The quality gatekeeper. Decides whether the item set is ready to ship, needs another revision cycle, has hit iteration limits, or requires human judgment on policy questions the agents can't resolve alone.


Execution model:
- Typed schemas between agents
- Iterative review/revision until acceptance or stop condition
- Streaming progress events for frontend status updates

## API Contract
Required request fields:
- `construct_name`
- `construct_definition`
- `target_population`
- `response_scale`

Optional request fields:
- `item_count` (default `10`, range `2-50`)
- `constraints`
- `construct_exclusions` (what this construct is not / overlap boundaries)
- `native_construct`
- `example_item`
- `approved_domains`
- `exclude_sources`
- `human_feedback`
- `previous_items`

Response:
- `final_items[]`
- `audit`

## Constraints Model (Important)
MAPIG applies constraints in two layers:

1. Standard baseline constraints (always active)
- No double-barrelled items
- Avoid idioms
- Minimize reading level
- Positively keyed only

2. Additional user constraints
- Anything provided in `constraints` is added on top of the baseline.
- User constraints are treated as additive, not replacements.

## Approved Sources Policy
MAPIG supports two evidence channels:
- Local curated sources in `data/approved_sources/`
- Web retrieval constrained to an approved domain allowlist

Web retrieval is blocked without allowlisted domains:
- Configure `PERPLEXITY_DOMAIN_FILTER` in `.env`, or
- Send `approved_domains` per request

Recommended mode:
- `SEARCH_PROVIDER=hybrid`

## Quickstart
### 1) Install dependencies
```bash
# Backend (Python, via Poetry)
poetry install

# Frontend (Next.js)
cd frontend
npm install
cd ..
```

### 2) Configure environment
Create `.env` in the repository root.

Example:
```env
APP_MODE=openai
OPENAI_API_KEY=YOUR_KEY
OPENAI_MODEL=gpt-4o-mini

SEARCH_PROVIDER=hybrid
PERPLEXITY_API_KEY=YOUR_KEY
PERPLEXITY_BASE_URL=https://api.perplexity.ai/v2
PERPLEXITY_MODEL=sonar-pro
PERPLEXITY_SEARCH_MODE=academic
PERPLEXITY_MAX_RESULTS=8
PERPLEXITY_DOMAIN_FILTER=doi.org,psycnet.apa.org,link.springer.com,sciencedirect.com,onlinelibrary.wiley.com,tandfonline.com,journals.sagepub.com,academic.oup.com,cambridge.org
```

### 3) Run API only
```bash
uvicorn app.main:app --reload
```

### 4) Run frontend + backend together
```bash
npm run dev
```

Override ports:
```bash
BACKEND_PORT=8001 FRONTEND_PORT=3001 npm run dev
```

Alternative shell runner:
```bash
./run_dev.sh
```

API docs:
- `http://127.0.0.1:8000/docs`

## Example Request
```json
{
  "construct_name": "Workplace belonging",
  "construct_definition": "A sustained sense of being accepted, included, and valued as a legitimate member of one’s work community.",
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

## Testing
Frontend production build:
```bash
npm --prefix frontend run build
```

Backend tests (if installed):
```bash
pytest -q
```

## Deployment (Vercel)

MAPIG can be deployed to Vercel serverless infrastructure with the following setup:

### Prerequisites

- Vercel account (free or Pro plan)
- Vercel Pro plan recommended for longer execution timeouts (300s default, up to 800s with Fluid Compute)
- API keys: `CLAUDE_API_KEY` and/or `OPENAI_API_KEY`

### Architecture

- **Backend**: Python serverless function at `api/index.py` (FastAPI with native ASGI support)
- **Frontend**: Next.js standalone mode deployed to Vercel
- **Checkpointing**: In-memory only (MemorySaver) - session resumption not available after cold start
- **SSE Streaming**: Supported within 300s timeout (typical runs: 20-40s)

### Backend Deployment

1. Create new Vercel project from repository
2. Configure project settings:
   - **Framework Preset**: Other
   - **Root Directory**: Leave as `.` (monorepo root)
   - **Build Command**: `echo 'No build needed for Python'`
   - **Output Directory**: Leave empty
3. Configure environment variables in Vercel dashboard:
   - `CLAUDE_API_KEY`: Your Anthropic API key
   - `OPENAI_API_KEY`: Your OpenAI API key (optional)
   - `APP_MODE`: `claude` or `openai` (default: `mock`)
   - `SEARCH_PROVIDER`: `perplexity` (optional)
   - `PERPLEXITY_API_KEY`: Your Perplexity API key (if using web search)
4. Deploy: Vercel auto-detects `api/index.py` and creates serverless function

Backend URL: `https://your-project.vercel.app/api/index`

### Frontend Deployment

1. Create separate Vercel project for frontend (or use same project with monorepo detection)
2. Configure project settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
3. Configure environment variables:
   - `NEXT_PUBLIC_API_URL`: Backend Vercel Function URL (e.g., `https://your-backend.vercel.app`)
4. Deploy: Vercel builds Next.js frontend automatically

Frontend URL: `https://your-frontend.vercel.app`

### Monorepo Linking (Optional)

Use Vercel's "Related Projects" feature to automatically link frontend preview deployments to corresponding backend preview URLs:

1. In frontend project settings, go to "Git"
2. Enable "Related Projects"
3. Select backend project
4. Preview deployments will automatically use corresponding backend preview URL

### Verification

After deployment:

1. Visit backend health check: `https://your-backend.vercel.app/healthz`
   - Should return: `{"status": "healthy"}`
2. Visit frontend: `https://your-frontend.vercel.app`
   - Setup form should load
   - Generate items to test end-to-end flow

### Known Limitations (v1)

- **Session resumption**: Not available after serverless function cold start (checkpoints are in-memory only)
- **Cold start time**: Initial request may take 3-8 seconds (Python serverless cold start)
- **Timeout**: Maximum 300s execution time (configurable up to 800s on Pro plan with Fluid Compute)

Most item generation runs complete in 20-40 seconds well within timeout limits.

### Troubleshooting

**CORS errors in browser console:**
- Verify NEXT_PUBLIC_API_URL matches backend domain exactly
- Check backend CORS configuration allows frontend domain

**Environment variables not found:**
- Verify exact spelling in Vercel dashboard (e.g., `CLAUDE_API_KEY` not `ANTHROPIC_API_KEY`)
- Redeploy after adding new environment variables

**Function timeout errors:**
- Check Vercel dashboard for actual timeout setting (default 300s on Pro)
- Complex constructs may take longer; consider increasing maxDuration in vercel.json

**Approved sources not found:**
- Verify `data/approved_sources/` directory is committed to git
- Check .vercelignore doesn't exclude data/ directory

## Contributing
Issues and pull requests are welcome for:
- Stability fixes
- Prompt and reviewer quality improvements
- UX and accessibility improvements
- Performance and observability upgrades

## Maintainer
Created by Prof. Llewellyn E. van Zyl  
Website: https://www.psynalytics.com  
GitHub: https://github.com/llewellynvz

## License
Proprietary software.  
Personal, academic, and internal research use is permitted.  
Redistribution and commercial use are not permitted.
