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

Return JSON matching the `ExpertPanelOutput` schema. Include ALL items
(unchanged ones too) so we have a complete revised view:

```json
{
  "expert_role": "<your same role>",
  "expert_label": "<your same label>",
  "item_scores": {"0": 5, "1": 4, ...},
  "item_comments": {"1": "Revised down: Domain expert's concern about construct slippage is salient."},
  "overall_verdict": "accept" | "revise" | "reject_set",
  "overall_summary": "<one paragraph reflecting any updated view>"
}
```

Add `item_comments` only for items where your score CHANGED in this round
(one short sentence each, ≤30 words). For items unchanged, omit from comments.
