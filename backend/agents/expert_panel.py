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
from pydantic import BaseModel, ConfigDict, Field, conint

from backend.agents.llm_utils import TokenUsage, invoke_structured_with_usage
from backend.agents.prompt_loader import load_prompt
from backend.analytics.krippendorff import (
    krippendorff_alpha,
    pairwise_kappa_matrix,
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


class _ExpertPanelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expert_role: ExpertRole
    expert_label: str = Field(..., min_length=2)
    # JSON requires string keys; convert to int post-validation
    item_scores: Dict[str, conint(ge=1, le=5)] = Field(default_factory=dict)  # type: ignore[valid-type]
    item_comments: Dict[str, str] = Field(default_factory=dict)
    overall_verdict: str = Field(..., min_length=2)
    overall_summary: str = Field(default="", max_length=600)


def _to_evaluation(out: _ExpertPanelOutput) -> ExpertEvaluation:
    """Convert LLM string-key dicts → ExpertEvaluation int-key dicts."""
    scores: Dict[int, int] = {}
    for k, v in out.item_scores.items():
        try:
            scores[int(k)] = int(v)
        except (TypeError, ValueError):
            continue
    comments: Dict[int, str] = {}
    for k, v in out.item_comments.items():
        try:
            comments[int(k)] = str(v)[:300]
        except (TypeError, ValueError):
            continue

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


def _expert_payload(
    role: ExpertRole,
    request: UserRequest,
    items: List[DraftItem],
    evidence: List[EvidenceChunk],
    pfa_result: Optional[PFAResult],
) -> dict:
    """Build LLM input payload for a single expert. Domain expert gets evidence."""
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
    if pfa_result and role == "psychometric":
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
) -> Tuple[ExpertConsensus, TokenUsage]:
    """Run the full expert panel: round 1 → optional debate → consensus.

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

    logger.info(
        "EXPERT_PANEL start n_items=%d debate_rounds=%d",
        len(items), settings.EXPERT_PANEL_DEBATE_ROUNDS,
    )
    total_usage = TokenUsage(model_name="expert_panel")

    roles: List[Tuple[ExpertRole, str]] = [
        ("psychometric", "Psychometric Expert"),
        ("domain", "Domain Expert"),
        ("localization", "Localization Expert"),
    ]

    # Round 1: parallel
    round1_results: List[ExpertEvaluation] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(roles)) as ex:
        futures = {
            ex.submit(_run_expert_round1, r, label, request, items, evidence, pfa_result): r
            for r, label in roles
        }
        for fut in concurrent.futures.as_completed(futures):
            try:
                ev, usage = fut.result()
                round1_results.append(ev)
                total_usage.input_tokens += usage.input_tokens
                total_usage.output_tokens += usage.output_tokens
                total_usage.total_tokens += usage.total_tokens
            except Exception as e:
                role = futures[fut]
                logger.warning("Expert panel round-1 call failed for %s: %s", role, e)

    if not round1_results:
        logger.warning("Expert panel: no round-1 results; aborting")
        return (
            ExpertConsensus(
                consensus_revisions=RevisionPlan(summary="Expert panel failed; no evaluations."),
            ),
            total_usage,
        )

    # Round 2: debate
    debate_results: List[ExpertEvaluation] = []
    if settings.EXPERT_PANEL_DEBATE_ROUNDS >= 1 and len(round1_results) >= 2:
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
                    logger.warning("Expert panel debate call failed for %s: %s", orig.expert_role, e)
                    debate_results.append(orig)  # fall back to round 1

    # Use debate-revised evaluations for IRR + consensus when available
    final_evals = debate_results if debate_results else round1_results
    matrix, role_labels = _build_rating_matrix(final_evals, len(items))

    # IRR
    try:
        irr_alpha = krippendorff_alpha(matrix, level="ordinal")
    except Exception as e:
        logger.warning("Krippendorff's α computation failed: %s", e)
        irr_alpha = float("nan")

    irr_pairwise = pairwise_kappa_matrix(matrix, role_labels)

    irr_warning: Optional[str] = None
    if not np.isnan(irr_alpha) and irr_alpha < settings.EXPERT_PANEL_IRR_MIN:
        irr_warning = (
            f"Krippendorff's α = {irr_alpha:.2f} < threshold {settings.EXPERT_PANEL_IRR_MIN:.2f}. "
            "Experts disagree substantially; consider redrafting or recruiting human experts."
        )
        logger.warning("EXPERT_PANEL_LOW_IRR %s", irr_warning)

    # Dissent flags
    dissent = _dissent_flags(matrix, settings.EXPERT_PANEL_DISSENT_SD)

    # Consensus revisions
    consensus_plan = synthesize_consensus(final_evals, items)

    logger.info(
        "EXPERT_PANEL done irr_alpha=%s pairwise=%s dissent=%d revisions=%d",
        f"{irr_alpha:.3f}" if not np.isnan(irr_alpha) else "nan",
        irr_pairwise, len(dissent), len(consensus_plan.edits),
    )

    return (
        ExpertConsensus(
            evaluations=round1_results,
            debate_revisions=debate_results,
            irr_alpha=None if np.isnan(irr_alpha) else float(round(irr_alpha, 4)),
            irr_pairwise=irr_pairwise,
            consensus_revisions=consensus_plan,
            dissent_flags=dissent,
            irr_warning=irr_warning,
        ),
        total_usage,
    )
