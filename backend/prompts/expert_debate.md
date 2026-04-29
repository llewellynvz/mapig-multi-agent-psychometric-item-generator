# Expert Panel — Debate Round

You previously rated a set of items on your role's rubric. Now you have access
to **other experts' anonymized round-1 ratings** for the same items.

For each item where your score differs from another expert by ≥ 2 points, you
may either:
1. **Stand by your score** — keep the same rating; provide one sentence
   explaining why your role's lens prioritizes this dimension.
2. **Revise your score** — adjust to be ≥ 1 point closer to the disagreeing
   expert; provide one sentence explaining what shifted your view.

You may NOT revise items where you already agreed (within 1 point). For items
that did not have ≥2-point disagreement, keep your original score.

This is a single debate round — do not anticipate further rounds.

## Output Format

Return JSON with `item_scores` as an **array** (NOT a dict). Include ALL items —
both the ones you revised and the ones you kept the same — so we get a
complete revised view:

```json
{
  "expert_role": "<your same role>",
  "expert_label": "<your same label>",
  "item_scores": [
    {"item_index": 0, "score": 5, "comment": ""},
    {"item_index": 1, "score": 4, "comment": "Revised down: Domain expert's concern about construct slippage is salient."}
  ],
  "overall_verdict": "revise",
  "overall_summary": "<one paragraph reflecting any updated view>"
}
```

- `comment` is required as a string. Use `""` when unchanged from round 1.
- Only fill in `comment` (≤30 words) for items where your score CHANGED in this round.
- `overall_verdict` must be one of: `"accept"`, `"revise"`, or `"reject_set"`.
