# 🧪 MAPIG – Multi-Agent Psychometric Item Generator

### Evidence-bounded, multi-agent item drafting for psychometric scale development

MAPIG is an implementation inspired by the LM-AIG conceptual framework for LLM-based multi-agent automatic item generation described by Lee, Son, and Jia (2025).  
It provides an auditable, schema-driven pipeline that drafts Likert-type items and iteratively improves them via specialised review agents.

![MAPIG orchestration diagram](./mapig_architecture.svg)

---

## 📌 What this project is

Psychometric item writing is sensitive to wording, context assumptions, and construct drift. MAPIG operationalises a conservative workflow:

- Strict JSON schemas between agents to reduce format drift and improve traceability
- Evidence-bounded retrieval with an approved-source policy
- Iterative review loops with explicit roles
- Audit metadata in every response for reproducibility

MAPIG produces **item drafts** and review artefacts. It does not replace human judgment, piloting, or validation.

---

## 🧠 How it works

### Inputs
You provide a `UserRequest` that must include:
- `construct_name`
- `construct_definition` (required)
- `target_population`
- `response_scale`

Optional inputs include:
- `item_count` (default 10)
- `example_item`
- `native_construct`
- `constraints`
- `approved_domains` (per-request allowlist for web retrieval)

### Agents
- **WebSurfer Agent**: retrieves construct-relevant academic evidence using Perplexity, constrained by an allowlist of approved domains.
- **Local retrieval**: pulls curated evidence from `data/approved_sources/*.md`.
- **Item Writer Agent**: drafts `DraftItem[]` with rationales and evidence citations.
- **Content Reviewer**: checks construct fidelity and contamination with neighbor constructs.
- **Linguistic Reviewer**: checks clarity, ambiguity, readability, and wording hazards.
- **Bias Reviewer**: flags bias risk and likely DIF drivers.
- **Meta Editor**: revises items using reviewer comments while preserving construct coverage.
- **Critic Agent (LLM)**: decides whether to iterate again or finalise, with explicit stop conditions.

---

## 🔒 Approved sources policy

MAPIG supports two evidence channels:

1) **Local approved sources**  
Markdown files in `data/approved_sources/` are treated as curated sources and cited as `local:<file>#<chunk>`.

2) **Web retrieval restricted to allowlisted domains**  
Perplexity retrieval is blocked unless an allowlist is provided.
- Set `PERPLEXITY_DOMAIN_FILTER` in `.env`, or
- Provide `approved_domains` in the API request

Recommendation:
- Use `SEARCH_PROVIDER=hybrid` so local item-writing standards remain available even when web retrieval is enabled.

---

## 🛠 Quickstart

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

### 2) Create `.env` in the project root

OpenAI:
```env
APP_MODE=openai
OPENAI_API_KEY=YOUR_KEY
OPENAI_MODEL=gpt-4o-mini
```

Perplexity retrieval (approved domains only):
```env
SEARCH_PROVIDER=hybrid
PERPLEXITY_API_KEY=YOUR_KEY
PERPLEXITY_BASE_URL=https://api.perplexity.ai/v2
PERPLEXITY_MODEL=sonar-pro
PERPLEXITY_SEARCH_MODE=academic
PERPLEXITY_MAX_RESULTS=8
PERPLEXITY_DOMAIN_FILTER=doi.org,psycnet.apa.org,link.springer.com,sciencedirect.com,onlinelibrary.wiley.com,tandfonline.com,journals.sagepub.com,academic.oup.com,cambridge.org
```

### 3) Run the API
```bash
uvicorn app.main:app --reload
```

Swagger UI:
- http://127.0.0.1:8000/docs

---

## 🧾 Example request

```json
{
  "construct_name": "Workplace belonging",
  "construct_definition": "A sustained sense of being accepted, included, and valued as a legitimate member of one’s work community.",
  "target_population": "Full-time employees in a hybrid work setting",
  "response_scale": "5-point Likert: Strongly disagree to Strongly agree",
  "item_count": 10,
  "example_item": "I feel like I belong in my team.",
  "constraints": ["No double-barrelled items", "Avoid idioms", "Minimise reading level"],
  "approved_domains": ["doi.org", "psycnet.apa.org", "link.springer.com"]
}
```

---

## ✅ What you get back

The API returns:
- `final_items`: item text, construct name, rationale, evidence citations
- `audit`: thread_id, run_id, timestamp, iteration_count, stop_reason, model_info, approved_sources

This structure is designed for audit trails and enterprise integration.

---

## 🧪 Testing

Run tests:
```bash
pytest -q
```

A healthy run:
- API starts cleanly
- `/v1/generate-items` returns 200 OK
- Response validates against schemas
- Audit block includes iteration counts and sources

---

## 📚 Adding curated local sources

Add markdown files to:
- `data/approved_sources/`

Guidance:
- Keep each file focused on one topic, such as a construct definition, item-writing standards, or a measurement standard.
- Prefer short excerpts and paraphrases with bibliographic notes.
- Do not copy proprietary item banks.

---

## 👨‍💻 **Who Maintains This?**  
This project was created by **Prof. Llewellyn E. van Zyl** .  

- 🌍 **Website:** [www.psynalytics.com](https://www.psynalytics.com)  
- 🔗 **GitHub:** [@llewellynvz](https://github.com/llewellynvz) 

🔥 If you’d like to **contribute**, feel free to fork this repo, submit a pull request, or report bugs!  

---

## 📜 License

This software is proprietary. Use and local modification are permitted for personal, academic, and internal research purposes only. Redistribution or commercial use is not permitted. See LICENSE for details.


---

## ⭐ If you found this useful

Star the repository ⭐

Share it with colleagues using Mplus

Contribute improvements or edge-case fixes