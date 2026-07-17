# LinkedIn Post

---

Writing psychometric scale items is slow, subjective, and hard to audit.

So I built a system where 11 AI agents do it together — in under 2 minutes.

It's called MAPIG (Multi-Agent Psychometric Item Generator), and here's what happens when you give it a construct definition:

1. An evidence retrieval agent searches peer-reviewed literature (constrained to domains like doi.org and APA PsycNet) and pulls theoretical frameworks, dimensions, and measurement precedents — with full citations.

2. An item writer drafts Likert-type items grounded in that evidence. Every item cites specific sources. Facet coverage is balanced across the theoretical dimensions. Reading level matches your target population.

3. A validation gate scores every item on construct correspondence, distinctiveness, clarity, and specificity. Items below threshold get selectively regenerated — only the failures, not the whole batch.

4. Three independent reviewers run in parallel:
   - A linguistic reviewer checks clarity, vague quantifiers, and double-barreled items
   - A bias reviewer evaluates 7 types of DIF risk (including intersectional bias)
   - A content reviewer simulates 5 naive judges rating correspondence and distinctiveness

5. A critic agent decides whether to accept or revise — using adaptive thresholds that progressively relax over iterations so the system converges instead of looping forever.

6. After finalization, the system estimates your inter-item correlation matrix using embedding cosine similarity — validated by Hommel & Arslan (2024) at r = .89 for scale-level predictions. A pseudo-alpha consistency estimate is calculated automatically and labeled as a pre-data signal.

7. It then searches academic databases for published convergent and discriminant instruments, scores validity using a dual-direction LLM-as-judge pattern, and runs plagiarism detection to ensure originality.

The result: a defensible first draft with preliminary psychometric indicators, a full audit trail, and every decision traceable — in about 90 seconds, for less than $2.

This doesn't replace empirical validation. You still need to pilot and collect real data. But it compresses weeks of item writing and expert review into minutes, with a level of systematic rigor that's hard to match manually.

Built with LangGraph, FastAPI, Next.js, Claude, GPT-4o, and OpenAI embeddings.

Live demo and repo link in the comments.

#Psychometrics #AI #ScaleDevelopment #MultiAgent #ResearchMethods #IOPsychology #MachineLearning #LLM #SurveyDesign #TestDevelopment

---

## First Comment (post immediately after)

```
Links:
- Live demo: https://lmaig-langgraph.vercel.app/
- GitHub: https://github.com/llewellynvz/lmaig-langgraph
- Reference: Hommel & Arslan (2024). Language models accurately infer correlations between psychological items and scales from text alone. European Journal of Psychological Assessment. https://doi.org/10.1027/1015-5759/a000838

Happy to answer questions about the architecture or the psychometric methodology behind it.
```
