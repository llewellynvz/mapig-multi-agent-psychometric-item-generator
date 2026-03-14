# MAPIG YouTube Video Script

**Target length**: 6-8 minutes
**Tone**: Enthusiastic but credible. Speaking to psychometricians, I/O psychologists, scale developers, and research methodologists.

---

## [0:00 - 0:30] HOOK

What if I told you that building a psychometric scale — the part that used to take weeks of writing, reviewing, and rewriting items — could be done in under two minutes, with every single item grounded in peer-reviewed evidence, reviewed for bias across seven dimensions, and validated against published instruments... automatically?

That's what I built. It's called MAPIG — the Multi-Agent Psychometric Item Generator — and today I'm going to show you exactly how it works under the hood.

---

## [0:30 - 1:30] WHAT IS MAPIG AND WHY IS IT DIFFERENT

So what actually is MAPIG?

It's an open platform where multiple AI agents — each one specialized for a different part of the scale development process — work together in a coordinated pipeline to draft, review, revise, and validate psychometric items.

Now, you might be thinking: "Can't I just ask ChatGPT to write me some survey items?" And yes, you can. But here's what you don't get: you don't get evidence grounding, you don't get structured bias review, you don't get iterative quality control, you don't get inter-item correlation estimates, and you definitely don't get convergent and discriminant validity checks against published instruments.

MAPIG isn't a chatbot writing survey questions. It's an orchestrated system of specialized agents that mirrors the actual psychometric development process — the same process you'd follow if you were doing this by hand, except each step is handled by a purpose-built AI agent with explicit instructions drawn from psychometric best practice.

Let me walk you through the pipeline.

---

## [1:30 - 2:15] STEP 1: EVIDENCE RETRIEVAL

Everything starts with evidence. Before a single item gets written, MAPIG's Web Surfer agent searches the academic literature through Perplexity's academic search API, constrained to peer-reviewed domains — think doi.org, APA PsycNet, Springer, Wiley, SAGE.

It's looking for three things: theoretical definitions of your construct, conceptual frameworks that identify the dimensions or facets, and measurement precedents — what instruments already exist in this space.

All of this gets structured into evidence chunks with citations, author names, and theoretical model tags. So when the item writer starts drafting, it isn't hallucinating construct definitions — it's citing Keyes, or Diener, or whoever the seminal authors are for your specific construct.

---

## [2:15 - 3:00] STEP 2: ITEM WRITING + VALIDATION

Next, the Item Writer agent generates your items. It follows established psychometric principles: unidimensional items, positive keying only, reading level matched to your target population, no double-barreled items, no idioms, and balanced facet coverage across the theoretical dimensions the evidence identified.

Every item comes with a rationale that cites the evidence — so you can trace exactly why each item was written the way it was.

But we don't just trust the writer. Every item immediately goes through a Validation Gate — an LLM-as-judge that scores each item on four dimensions: construct correspondence, discriminant distinctiveness, semantic clarity, and population specificity. Items scoring below the threshold get selectively regenerated — only the ones that failed, not the whole batch. And if the first attempt doesn't fix them, the system escalates to a more powerful model for retries.

---

## [3:00 - 4:15] STEP 3: TRIPLE REVIEW

Now here's where it gets interesting. Every item goes through three independent reviewers running in parallel.

The Linguistic Reviewer checks for clarity issues — vague quantifiers like "often" without time anchors, absolute terms, ambiguous referents, double negatives.

The Bias Reviewer evaluates seven types of differential item functioning risk: construct bias, linguistic bias, cultural reference bias, socioeconomic bias, context access bias, protected attribute bias, and intersectional bias. That last one — intersectional — automatically escalates if multiple bias types compound on the same item.

And the Content Reviewer simulates five naive judges rating each item on construct correspondence and distinctiveness, checking whether the item actually measures what you claim or whether it's drifting into a neighboring construct.

All three reviewers produce structured comments with severity ratings. Then the Critic agent decides: are we good, or do we need another revision round?

---

## [4:15 - 4:45] STEP 4: ADAPTIVE REVISION

The Critic uses adaptive thresholds that relax over iterations. Round one is strict — any medium-severity issue forces a revision. Round two is thorough — it'll accept if the items are reasonably clean. Round three is the safety net — it accepts almost anything except critical blockers.

If revision is needed, the Meta Editor applies surgical fixes — only touching the items that were flagged, preserving facet coverage, resolving conflicts between reviewers by prioritizing construct fidelity over bias over linguistic concerns.

And then it goes back through the reviewers again. This loop runs until the Critic accepts or we hit the hard stop at three iterations.

---

## [4:45 - 5:45] STEP 5: CORRELATION MATRIX

Once items are finalized, MAPIG estimates your inter-item correlation matrix — without collecting a single data point.

How? Using the validated methodology from Hommel and Arslan, published in 2024 in the European Journal of Psychological Assessment. They demonstrated that sentence transformer embeddings with cosine similarity accurately predict real inter-item correlations — with validities of point-seven-one at the item level and point-eight-nine at the scale level.

Here's how it works: all your items get embedded into 1536-dimensional vectors using OpenAI's text-embedding-3-small model. Those vectors get normalized, and then we compute a full cosine similarity matrix — pure linear algebra, no LLM hallucination risk. From that matrix, MAPIG calculates McDonald's omega for internal consistency and the mean inter-item correlation, flagging whether your scale falls in the optimal range or whether items are too similar or too dissimilar.

---

## [5:45 - 6:45] STEP 6: VALIDITY ESTIMATION

But we're not done. MAPIG also estimates convergent and discriminant validity.

The Instrument Searcher queries academic databases to find published instruments — one that measures the same construct as yours for convergent validity, and one that measures a related but distinct construct for discriminant validity.

For example, if you're generating a Life Satisfaction scale, it might find the Satisfaction with Life Scale as the convergent benchmark and the Flourishing Scale as the discriminant one.

Then the Validity Scorer uses a dual-direction LLM-as-judge pattern: it asks "how well do the generated items align with the comparison instrument?" and then reverses it — "how well does the comparison instrument align with the generated items?" Averaging both directions mitigates position bias and gives you a robust convergent validity estimate.

For discriminant validity, it estimates the expected correlation between your target construct and the comparison construct, flagging if the overlap is dangerously high.

On top of all that, there's a plagiarism detector using sentence-transformer embeddings to make sure your items are original — not just paraphrased copies of existing scales.

---

## [6:45 - 7:15] WRAP-UP

So that's MAPIG. Evidence-grounded item writing. Four-dimension validation. Triple parallel review for linguistic quality, bias, and content validity. Adaptive revision loops. Embedding-based correlation matrices. And automated convergent and discriminant validity estimation against published instruments.

The entire pipeline runs in under two minutes, costs less than two dollars, and produces a full audit trail — every decision, every revision, every citation traceable.

It doesn't replace empirical validation. You still need to pilot your items and collect real data. But it gets you from "I have a construct definition" to "I have a defensible first draft with preliminary psychometric indicators" faster than anything else out there.

Link to the repo and the live demo is in the description. I'd love to hear what you think.

---

*[END]*
