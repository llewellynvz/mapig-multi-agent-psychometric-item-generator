"""Multi-expert face/content validity panel.

Runs three expert agents (psychometric, domain, localization) in parallel:
- Round 1: independent ratings + comments.
- Round 2 (debate, optional): each expert sees others' anonymized scores
  and may revise.

Computes Krippendorff's α (overall) + pairwise Cohen's κ. Synthesizes a
RevisionPlan compatible with the existing meta-editor for one final pass.

Pipeline position: AFTER critic accepts and PFA pruning, BEFORE finalize.
"""

from __future__ import annotations

import concurrent.futures
import logging
import statistics
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from backend.agents.llm_utils import TokenUsage, invoke_structured_with_usage
from backend.agents.prompt_loader import load_prompt
from backend.analytics.krippendorff import (
    krippendorff_alpha,
    krippendorff_alpha_nominal,
    pairwise_kappa_matrix,
    pairwise_spearman_matrix,
)
from backend.schemas import (
    DraftItem,
    EvidenceChunk,
    ExpertConsensus,
    ExpertEvaluation,
    ExpertRole,
    PFAResult,
    RevisionEdit,
    RevisionPlan,
    UserRequest,
)
from backend.settings import settings

logger = logging.getLogger("lmaig.expert_panel")


# --- Inner-agent schemas (LLM I/O) ---


class _ExpertItemScore(BaseModel):
    """One expert's rating for a single item — flat schema for OpenAI strict mode.

    All fields required (no defaults) — strict mode rejects optionals. LLM must
    emit `comment=""` when there is no comment.
    """

    model_config = ConfigDict(extra="forbid")
    item_index: int = Field(..., ge=0)
    score: int = Field(..., ge=1, le=5)
    comment: str = Field(..., max_length=300)


class _ExpertPanelOutput(BaseModel):
    """LLM I/O schema. Uses List[_ExpertItemScore] (not Dict[str, conint(...)])
    because OpenAI strict structured-output rejects Dict-with-additionalProperties
    and fields with default_factory not present in `required`.

    All fields are required (no defaults) — OpenAI strict mode rejects optional
    fields. The LLM must always emit a value (use empty string when N/A).
    """

    model_config = ConfigDict(extra="forbid")
    expert_role: ExpertRole
    expert_label: str = Field(..., min_length=2)
    item_scores: List[_ExpertItemScore]
    overall_verdict: str = Field(..., min_length=2)
    overall_summary: str = Field(..., max_length=600)


def _to_evaluation(out: _ExpertPanelOutput) -> ExpertEvaluation:
    """Convert flat LLM list → ExpertEvaluation int-key dicts."""
    scores: Dict[int, int] = {}
    comments: Dict[int, str] = {}
    for s in out.item_scores:
        idx = int(s.item_index)
        # Defensive clamp in case LLM returns slightly out-of-range values
        scores[idx] = max(1, min(5, int(s.score)))
        if s.comment:
            comments[idx] = s.comment[:300]

    verdict = out.overall_verdict.strip().lower()
    if verdict not in {"accept", "revise", "reject_set"}:
        verdict = "revise"  # safe default

    return ExpertEvaluation(
        expert_role=out.expert_role,
        expert_label=out.expert_label,
        item_scores=scores,
        item_comments=comments,
        overall_verdict=verdict,  # type: ignore[arg-type]
        overall_summary=out.overall_summary or "",
    )


def _load_psychometric_reference_content() -> str:
    """Load item-writing guidelines + style reference for the Psychometric Expert.

    These files live in `data/` and are user-editable: researchers can add
    domain-specific rules (e.g., from APA Standards, DeVellis & Thorpe, or
    custom organizational style guides). The Psychometric Expert receives
    this content verbatim so its critique is grounded in the same rules the
    Item Writer was instructed to follow.

    Returns the concatenated content, or empty string if no files found.
    """
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    parts: List[str] = []
    candidates = [
        repo_root / "data" / "approved_sources" / "item_writing_guidelines.md",
        repo_root / "data" / "item_style_reference.md",
    ]
    for path in candidates:
        try:
            if path.exists():
                content = path.read_text(encoding="utf-8")
                # Cap at 8000 chars per file to keep prompt size sane
                if len(content) > 8000:
                    content = content[:8000] + "\n…(truncated)…"
                parts.append(f"## {path.name}\n\n{content.strip()}")
        except Exception as e:
            logger.warning(
                "Could not read psychometric reference %s: %s", path.name, e,
            )
    return "\n\n---\n\n".join(parts)


# Cache the reference content at module load — files don't change during a run
_PSYCHOMETRIC_REFERENCE = _load_psychometric_reference_content()
if _PSYCHOMETRIC_REFERENCE:
    logger.info(
        "EXPERT_PANEL_PSYCHOMETRIC_REF loaded chars=%d sources=%d",
        len(_PSYCHOMETRIC_REFERENCE),
        _PSYCHOMETRIC_REFERENCE.count("---"),
    )


def _expert_payload(
    role: ExpertRole,
    request: UserRequest,
    items: List[DraftItem],
    evidence: List[EvidenceChunk],
    pfa_result: Optional[PFAResult],
) -> dict:
    """Build LLM input payload for a single expert.

    Each role gets:
    - Common context (construct + items)
    - Domain expert: top-5 evidence chunks
    - Psychometric expert: PFA summary + scale-development reference content
      (item_writing_guidelines.md + item_style_reference.md from data/)
    """
    base = {
        "construct_name": request.construct_name,
        "construct_definition": request.construct_definition,
        "construct_exclusions": request.construct_exclusions,
        "target_population": request.target_population,
        "cultural_group": request.cultural_group,
        "response_scale": request.response_scale,
        "items": [
            {"item_index": i, "item_text": it.item_text, "facet_name": it.facet_name}
            for i, it in enumerate(items)
        ],
    }
    if role == "domain":
        base["evidence_top_5"] = [
            {
                "title": e.title,
                "snippet": e.snippet[:300],
                "theoretical_model": e.theoretical_model,
                "dimensions": e.dimensions,
            }
            for e in evidence[:5]
        ]
    if role == "psychometric":
        # Always inject the reference content so the expert evaluates against
        # the SAME rules the item writer was instructed to follow.
        if _PSYCHOMETRIC_REFERENCE:
            base["scale_development_reference"] = _PSYCHOMETRIC_REFERENCE
        if pfa_result:
            base["pfa_summary"] = {
                "factor_recovery_rate": pfa_result.factor_recovery_rate,
                "rmsr": pfa_result.rmsr,
                "verdict": pfa_result.fit_verdict,
                "items_with_loading_issues": [
                    fl.item_index for fl in pfa_result.loadings if not fl.is_well_loaded
                ],
            }
    return base


def _run_expert_round1(
    role: ExpertRole,
    label: str,
    request: UserRequest,
    items: List[DraftItem],
    evidence: List[EvidenceChunk],
    pfa_result: Optional[PFAResult],
) -> Tuple[ExpertEvaluation, TokenUsage]:
    """Run one expert agent for round 1."""
    if settings.APP_MODE == "mock":
        # Deterministic mock: psychometric scores 4s, domain scores 5s, localization scores 3s
        base_score = {"psychometric": 4, "domain": 5, "localization": 3}.get(role, 3)
        scores = {i: base_score for i in range(len(items))}
        comments = {0: f"{role} mock comment for item 0"} if items else {}
        return (
            ExpertEvaluation(
                expert_role=role,  # type: ignore[arg-type]
                expert_label=label,
                item_scores=scores,
                item_comments=comments,
                overall_verdict="accept",
                overall_summary=f"{label} mock summary.",
            ),
            TokenUsage(model_name="mock"),
        )

    prompt_file = {
        "psychometric": "expert_psychometric.md",
        "domain": "expert_domain.md",
        "localization": "expert_localization.md",
    }.get(role, "expert_psychometric.md")

    system = load_prompt(prompt_file)
    payload = _expert_payload(role, request, items, evidence, pfa_result)
    human = (
        f"Score every item on your rubric. Return ALL {len(items)} item_scores. "
        f"Use string keys for item indices.\n\nINPUT:\n{payload}"
    )

    agent_name = f"expert_panel_{role}"
    out, usage = invoke_structured_with_usage(
        _ExpertPanelOutput,
        [("system", system), ("human", human)],
        agent_name=agent_name,
        model_provider=request.model_provider,
    )
    return _to_evaluation(out), usage


def _run_expert_debate(
    eval_round1: ExpertEvaluation,
    other_evaluations: List[ExpertEvaluation],
    request: UserRequest,
    items: List[DraftItem],
) -> Tuple[ExpertEvaluation, TokenUsage]:
    """Run debate round for one expert given peers' anonymized round-1 scores."""
    if settings.APP_MODE == "mock":
        # In mock mode, pretend no revisions happened
        return eval_round1, TokenUsage(model_name="mock")

    system = load_prompt("expert_debate.md")
    peers_scores = [
        {
            "anonymized_role": f"peer_{idx + 1}",
            "item_scores": {str(k): v for k, v in e.item_scores.items()},
            "overall_verdict": e.overall_verdict,
        }
        for idx, e in enumerate(other_evaluations)
    ]
    payload = {
        "your_role": eval_round1.expert_role,
        "your_label": eval_round1.expert_label,
        "your_round1_scores": {str(k): v for k, v in eval_round1.item_scores.items()},
        "your_round1_summary": eval_round1.overall_summary,
        "peers_round1": peers_scores,
        "items": [
            {"item_index": i, "item_text": it.item_text} for i, it in enumerate(items)
        ],
    }
    human = (
        "Review peers' anonymized round-1 ratings. For each item where you "
        "differ by ≥ 2 points, decide whether to stand by or revise. Return "
        "ALL item scores (revised + unchanged).\n\nINPUT:\n" + str(payload)
    )

    agent_name = f"expert_panel_{eval_round1.expert_role}"
    out, usage = invoke_structured_with_usage(
        _ExpertPanelOutput,
        [("system", system), ("human", human)],
        agent_name=agent_name,
        model_provider=request.model_provider,
    )
    return _to_evaluation(out), usage


# --- Aggregation helpers ---


def _build_rating_matrix(
    evaluations: List[ExpertEvaluation],
    n_items: int,
) -> Tuple[np.ndarray, List[str]]:
    """Build (n_experts, n_items) array of scores. NaN for missing."""
    arr = np.full((len(evaluations), n_items), np.nan, dtype=float)
    labels: List[str] = []
    for r, ev in enumerate(evaluations):
        labels.append(ev.expert_role)
        for i, score in ev.item_scores.items():
            if 0 <= i < n_items:
                arr[r, i] = float(score)
    return arr, labels


def _dissent_flags(matrix: np.ndarray, sd_threshold: float) -> List[int]:
    flags: List[int] = []
    for j in range(matrix.shape[1]):
        col = matrix[:, j]
        valid = col[~np.isnan(col)]
        if len(valid) >= 2 and float(np.std(valid, ddof=0)) >= sd_threshold:
            flags.append(j)
    return flags


def synthesize_consensus(
    evaluations: List[ExpertEvaluation],
    items: List[DraftItem],
) -> RevisionPlan:
    """Build a RevisionPlan from expert evaluations.

    Heuristic: if mean score ≥ 4 and std ≤ 0.5 → accept. If any expert flagged
    overall_verdict='reject_set' or any single score == 1 → strong revise.
    Otherwise refine if at least 2 experts mention specific concerns.
    """
    n_items = len(items)
    matrix, _ = _build_rating_matrix(evaluations, n_items)
    edits: List[RevisionEdit] = []

    # Aggregate comment text per item across experts
    per_item_comments: Dict[int, List[Tuple[str, str]]] = {}
    for ev in evaluations:
        for i, c in ev.item_comments.items():
            per_item_comments.setdefault(i, []).append((ev.expert_role, c))

    set_rejected = any(ev.overall_verdict == "reject_set" for ev in evaluations)

    summaries: List[str] = []
    for i in range(n_items):
        col = matrix[:, i]
        valid = col[~np.isnan(col)]
        if len(valid) == 0:
            continue
        mean = float(np.mean(valid))
        sd = float(np.std(valid, ddof=0))
        any_critical = bool(np.any(valid == 1))

        # Decide whether to emit a revision
        emit = False
        if any_critical:
            emit = True
        elif mean < 3.0:
            emit = True
        elif mean < 4.0 and len(per_item_comments.get(i, [])) >= 2:
            emit = True

        if emit:
            comments = per_item_comments.get(i, [])
            reason_parts = [f"{role}: {comment}" for role, comment in comments[:3]]
            reason = " | ".join(reason_parts) if reason_parts else f"Mean expert score {mean:.1f}"
            # Truncate to schema limit (280 chars)
            reason = reason[:275] + "..." if len(reason) > 275 else reason
            edits.append(
                RevisionEdit(
                    item_index=i,
                    reason=reason,
                    before=items[i].item_text,
                    after=items[i].item_text,  # meta-editor will produce the after
                )
            )

    if set_rejected:
        summaries.append("At least one expert recommended rejecting the item set.")
    if edits:
        summaries.append(f"{len(edits)} of {n_items} items flagged for expert revision.")
    else:
        summaries.append(f"All {n_items} items passed expert panel review.")

    return RevisionPlan(summary=" ".join(summaries), edits=edits)


def run_expert_panel(
    request: UserRequest,
    items: List[DraftItem],
    evidence: List[EvidenceChunk],
    pfa_result: Optional[PFAResult] = None,
    time_budget_seconds: Optional[float] = None,
) -> Tuple[ExpertConsensus, TokenUsage]:
    """Run the full expert panel: round 1 → optional debate → consensus.

    When `time_budget_seconds` is provided, the panel degrades gracefully:
    - If budget < EXPERT_PANEL_DEBATE_MIN_REMAINING (default 15s): skip debate
      round but still run round 1 (3 parallel calls, ~5s).
    - If budget < EXPERT_PANEL_PARTIAL_MIN_REMAINING (default 8s): use a hard
      timeout on round 1 and return partial consensus with whatever evaluations
      completed by deadline.

    Returns:
        (ExpertConsensus, accumulated TokenUsage).
    """
    if not settings.EXPERT_PANEL_ENABLED or len(items) == 0:
        return (
            ExpertConsensus(
                consensus_revisions=RevisionPlan(summary="Expert panel disabled."),
            ),
            TokenUsage(),
        )

    # Decide degradation level up front for clear logging
    debate_enabled = settings.EXPERT_PANEL_DEBATE_ROUNDS >= 1
    partial_mode = False
    if time_budget_seconds is not None:
        if time_budget_seconds < settings.EXPERT_PANEL_PARTIAL_MIN_REMAINING:
            partial_mode = True
            debate_enabled = False
            logger.warning(
                "EXPERT_PANEL_DEGRADED reason=critical_budget time_budget=%.1fs "
                "decision=partial_round1_only",
                time_budget_seconds,
            )
        elif time_budget_seconds < settings.EXPERT_PANEL_DEBATE_MIN_REMAINING:
            debate_enabled = False
            logger.warning(
                "EXPERT_PANEL_DEGRADED reason=low_budget time_budget=%.1fs "
                "decision=skip_debate",
                time_budget_seconds,
            )

    logger.info(
        "EXPERT_PANEL start n_items=%d debate_enabled=%s partial_mode=%s time_budget=%s",
        len(items), debate_enabled, partial_mode,
        f"{time_budget_seconds:.1f}s" if time_budget_seconds is not None else "unbounded",
    )
    total_usage = TokenUsage(model_name="expert_panel")

    roles: List[Tuple[ExpertRole, str]] = [
        ("psychometric", "Psychometric Expert"),
        ("domain", "Domain Expert"),
        ("localization", "Localization Expert"),
    ]

    # Round 1: parallel — uses concurrent.futures.wait with timeout in partial_mode
    round1_results: List[ExpertEvaluation] = []
    failed_round1_roles: List[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(roles)) as ex:
        futures = {
            ex.submit(_run_expert_round1, r, label, request, items, evidence, pfa_result): r
            for r, label in roles
        }
        if partial_mode and time_budget_seconds is not None:
            # Hard deadline: take whatever completes within the budget minus a 2s
            # finalize buffer. Pending futures are cancelled below.
            timeout_per_round = max(2.0, time_budget_seconds - 2.0)
            done_set, not_done_set = concurrent.futures.wait(
                list(futures.keys()), timeout=timeout_per_round,
            )
            iteration_set = list(done_set)
            for fut in not_done_set:
                role = futures[fut]
                fut.cancel()
                failed_round1_roles.append(f"{role}:timeout")
                logger.warning(
                    "EXPERT_PANEL_PARTIAL_TIMEOUT role=%s timeout=%.1fs",
                    role, timeout_per_round,
                )
        else:
            iteration_set = list(concurrent.futures.as_completed(futures))

        for fut in iteration_set:
            try:
                ev, usage = fut.result()
                round1_results.append(ev)
                total_usage.input_tokens += usage.input_tokens
                total_usage.output_tokens += usage.output_tokens
                total_usage.total_tokens += usage.total_tokens
            except Exception as e:
                role = futures[fut]
                failed_round1_roles.append(f"{role}:{type(e).__name__}")
                logger.warning(
                    "EXPERT_PANEL_ROUND1_FAIL role=%s error_type=%s error=%s",
                    role, type(e).__name__, e,
                    exc_info=True,
                )

    if not round1_results:
        logger.warning(
            "EXPERT_PANEL_ABORT reason=no_round1_results failed_roles=%s",
            failed_round1_roles,
        )
        return (
            ExpertConsensus(
                consensus_revisions=RevisionPlan(summary="Expert panel failed; no evaluations."),
                irr_warning=(
                    f"All round-1 evaluations failed ({', '.join(failed_round1_roles)}). "
                    "Expert panel returned empty consensus."
                ) if failed_round1_roles else None,
            ),
            total_usage,
        )

    if len(round1_results) < len(roles):
        logger.warning(
            "EXPERT_PANEL_PARTIAL completed=%d expected=%d failed_roles=%s",
            len(round1_results), len(roles), failed_round1_roles,
        )

    # Round 2: debate — gated on debate_enabled (which incorporates budget check)
    debate_results: List[ExpertEvaluation] = []
    if debate_enabled and len(round1_results) >= 2:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(round1_results)) as ex:
            futures2 = {}
            for ev in round1_results:
                others = [e for e in round1_results if e is not ev]
                futures2[ex.submit(_run_expert_debate, ev, others, request, items)] = ev
            for fut in concurrent.futures.as_completed(futures2):
                try:
                    new_ev, usage = fut.result()
                    debate_results.append(new_ev)
                    total_usage.input_tokens += usage.input_tokens
                    total_usage.output_tokens += usage.output_tokens
                    total_usage.total_tokens += usage.total_tokens
                except Exception as e:
                    orig = futures2[fut]
                    logger.warning(
                        "EXPERT_PANEL_DEBATE_FAIL role=%s error_type=%s error=%s",
                        orig.expert_role, type(e).__name__, e,
                        exc_info=True,
                    )
                    debate_results.append(orig)  # fall back to round 1

    # Use debate-revised evaluations for IRR + consensus when available
    final_evals = debate_results if debate_results else round1_results
    matrix, role_labels = _build_rating_matrix(final_evals, len(items))

    # ---- IRR computation ----
    # NOTE: experts use DIFFERENT rubrics, so per-item score-level α is
    # conceptually wrong (it assumes parallel ratings of the same construct).
    # We compute three signals and treat verdict-level α as the meaningful one:
    #
    # 1. Verdict α (nominal):  do experts agree on the BOTTOM-LINE OUTCOME?
    #    This is what we should warn on.
    # 2. Pairwise Spearman ρ:  do experts agree on RELATIVE ITEM ORDERING?
    #    Robust to differing rubric scales.
    # 3. Per-item α + κ:        kept for backward-compat / informational only.
    #    Often LOW BY DESIGN — that's the point of having different lenses.

    # Legacy ordinal α + κ on per-item scores (informational only)
    try:
        irr_alpha = krippendorff_alpha(matrix, level="ordinal")
    except Exception as e:
        logger.warning("Krippendorff's α (per-item) failed: %s", e)
        irr_alpha = float("nan")

    irr_pairwise = pairwise_kappa_matrix(matrix, role_labels)

    # New: Spearman rank correlation per pair — robust to differing rubrics
    irr_pairwise_spearman = pairwise_spearman_matrix(matrix, role_labels)

    # New: verdict-level α — the meaningful agreement metric
    verdict_ratings: List[List[str]] = [[ev.overall_verdict for ev in final_evals]]
    # Reshape: krippendorff_alpha_nominal expects (n_raters, n_items)
    # Each expert is a "rater"; each "item" is the verdict on the item set as a whole.
    # Since each expert produces ONE verdict for the full set, we treat the verdict
    # as a single-item rating across n raters. To make α meaningful we need at least
    # 2 items — so we additionally rate the "majority severity" of each item as a
    # nominal high/medium/low to give α more data.
    #
    # Simpler approach: for each item, take each expert's score and bucket into
    # accept (≥4) / revise (3) / reject (≤2). Then compute nominal α on this
    # bucketed rating per item. This actually measures "do they agree on the
    # actionable judgment for each item?"
    bucketed_per_item: List[List[str]] = []
    for r_idx in range(matrix.shape[0]):
        row: List[str] = []
        for c_idx in range(matrix.shape[1]):
            v = matrix[r_idx, c_idx]
            if np.isnan(v):
                row.append(None)  # type: ignore[arg-type]
            elif v >= 4:
                row.append("accept")
            elif v >= 3:
                row.append("revise")
            else:
                row.append("reject")
        bucketed_per_item.append(row)

    try:
        irr_verdict_alpha = krippendorff_alpha_nominal(bucketed_per_item)
    except Exception as e:
        logger.warning("Verdict-level α failed: %s", e)
        irr_verdict_alpha = float("nan")

    irr_warning: Optional[str] = None
    # Warn only when the verdict-level agreement is low — this is the
    # meaningful signal. Per-item α can be low BY DESIGN with differing rubrics.
    if not np.isnan(irr_verdict_alpha) and irr_verdict_alpha < settings.EXPERT_PANEL_IRR_MIN:
        irr_warning = (
            f"Verdict-level Krippendorff's α = {irr_verdict_alpha:.2f} (threshold {settings.EXPERT_PANEL_IRR_MIN:.2f}). "
            f"Experts disagree on whether items should be accepted, revised, or rejected — "
            f"consider redrafting or recruiting human reviewers. "
            f"(Per-item score α was {irr_alpha:.2f}, but score-level disagreement is expected "
            f"with differing rubrics and is informational only.)"
        )
        logger.warning("EXPERT_PANEL_LOW_IRR %s", irr_warning)
    elif not np.isnan(irr_alpha) and irr_alpha < 0:
        # Per-item α negative — log as info (not a warning) so we have audit trail
        # but don't alarm the user.
        logger.info(
            "EXPERT_PANEL_PER_ITEM_α_LOW alpha=%.3f — expected with differing rubrics; "
            "see verdict α (%.3f) for actionable agreement signal",
            irr_alpha, irr_verdict_alpha if not np.isnan(irr_verdict_alpha) else float("nan"),
        )

    # Dissent flags — items where score SD is high. Still useful even with
    # differing rubrics: tells us which items provoke the strongest cross-rubric
    # disagreement.
    dissent = _dissent_flags(matrix, settings.EXPERT_PANEL_DISSENT_SD)

    # Consensus revisions
    consensus_plan = synthesize_consensus(final_evals, items)

    logger.info(
        "EXPERT_PANEL done verdict_α=%s per_item_α=%s spearman=%s dissent=%d revisions=%d",
        f"{irr_verdict_alpha:.3f}" if not np.isnan(irr_verdict_alpha) else "nan",
        f"{irr_alpha:.3f}" if not np.isnan(irr_alpha) else "nan",
        irr_pairwise_spearman, len(dissent), len(consensus_plan.edits),
    )

    return (
        ExpertConsensus(
            evaluations=round1_results,
            debate_revisions=debate_results,
            irr_alpha=None if np.isnan(irr_alpha) else float(round(irr_alpha, 4)),
            irr_verdict_alpha=None if np.isnan(irr_verdict_alpha) else float(round(irr_verdict_alpha, 4)),
            irr_pairwise=irr_pairwise,
            irr_pairwise_spearman=irr_pairwise_spearman,
            consensus_revisions=consensus_plan,
            dissent_flags=dissent,
            irr_warning=irr_warning,
        ),
        total_usage,
    )
