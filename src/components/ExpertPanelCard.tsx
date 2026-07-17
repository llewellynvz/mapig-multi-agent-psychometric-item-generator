"use client";

import { useState } from "react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Badge } from "@/components/ui/badge";
import {
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  CheckCircle2,
  Users,
  Info,
  Download,
} from "lucide-react";
import type { ExpertConsensus, ExpertEvaluation } from "@/lib/types";

export interface ExpertPanelCardProps {
  consensus: ExpertConsensus;
}

function irrColor(alpha: number | null | undefined): string {
  if (alpha == null) return "text-muted-foreground";
  if (alpha >= 0.8) return "text-[#a7d12b]";
  if (alpha >= 0.667) return "text-[#a7d12b]/80";
  if (alpha >= 0.4) return "text-amber-300";
  return "text-red-300";
}

function irrLabel(alpha: number | null | undefined): string {
  if (alpha == null) return "Unable to compute";
  if (alpha >= 0.8) return "Strong agreement";
  if (alpha >= 0.667) return "Acceptable";
  if (alpha >= 0.4) return "Weak";
  return "Poor";
}

function verdictBadgeColor(v: string): string {
  if (v === "accept") return "bg-[#a7d12b]/15 text-[#a7d12b] border-[#a7d12b]/30";
  if (v === "revise") return "bg-amber-500/15 text-amber-300 border-amber-500/30";
  return "bg-red-500/15 text-red-300 border-red-500/30";
}

function ScoreBadge({ score }: { score: number }) {
  let color = "border-red-500/30 text-red-300";
  if (score >= 4) color = "border-[#a7d12b]/30 text-[#a7d12b]";
  else if (score === 3) color = "border-amber-500/30 text-amber-300";
  return (
    <Badge variant="outline" className={`tabular-nums w-7 justify-center ${color}`}>
      {score}
    </Badge>
  );
}

function ExpertVerbatimSection({ ev }: { ev: ExpertEvaluation }) {
  const [open, setOpen] = useState(false);
  const itemEntries = Object.entries(ev.item_scores)
    .map(([k, v]) => ({ idx: parseInt(k, 10), score: v as number, comment: ev.item_comments[parseInt(k, 10)] || "" }))
    .sort((a, b) => a.idx - b.idx);

  const flaggedCount = itemEntries.filter((e) => e.comment).length;

  return (
    <div className="rounded-lg border border-border/40 bg-slate-900/30">
      <button
        type="button"
        onClick={() => setOpen((s) => !s)}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <div className="flex items-center gap-2">
          {open ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="text-sm font-semibold text-slate-50">
            {ev.expert_label}
          </span>
          <Badge className={verdictBadgeColor(ev.overall_verdict)}>
            {ev.overall_verdict}
          </Badge>
        </div>
        <span className="text-[10px] uppercase text-muted-foreground/70">
          {flaggedCount} item{flaggedCount === 1 ? "" : "s"} flagged · {itemEntries.length} rated
        </span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          {ev.overall_summary && (
            <div className="rounded border border-border/30 bg-slate-950/40 px-3 py-2">
              <p className="text-[11px] uppercase font-medium text-muted-foreground/70 mb-1">
                Overall summary
              </p>
              <p className="text-[12px] text-slate-100 leading-relaxed">
                {ev.overall_summary}
              </p>
            </div>
          )}
          <div>
            <p className="text-[11px] uppercase font-medium text-muted-foreground/70 mb-2">
              Per-item ratings
            </p>
            <div className="space-y-1.5">
              {itemEntries.map(({ idx, score, comment }) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 text-[12px]"
                >
                  <ScoreBadge score={score} />
                  <span className="text-muted-foreground/90 mt-0.5 shrink-0 w-16">
                    Item {idx + 1}
                  </span>
                  <span className="text-slate-100/90 leading-relaxed">
                    {comment || <span className="text-muted-foreground/60 italic">No specific concern.</span>}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function ExpertPanelCard({ consensus }: ExpertPanelCardProps) {
  const [showDebate, setShowDebate] = useState(false);
  const finalEvals: ExpertEvaluation[] =
    consensus.debate_revisions.length > 0 ? consensus.debate_revisions : consensus.evaluations;

  // Prefer verdict α as the headline metric — it's the meaningful one.
  // Fall back to per-item α if verdict α is unavailable for some reason.
  const headlineAlpha =
    consensus.irr_verdict_alpha != null
      ? consensus.irr_verdict_alpha
      : consensus.irr_alpha;

  return (
    <SurfaceCard className="mt-4 border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base md:text-lg flex items-center gap-2">
            <Users className="h-4 w-4 text-[#a7d12b]" />
            Expert Face/Content Validity
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={`tabular-nums ${irrColor(headlineAlpha)}`}>
              α (verdict) = {headlineAlpha != null ? headlineAlpha.toFixed(2) : "—"}
            </Badge>
            <span className="text-[11px] uppercase font-medium text-muted-foreground/80">
              {irrLabel(headlineAlpha)}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        {/* Reframe banner: explain what the IRR metric actually measures */}
        <div className="mb-4 rounded-lg border border-blue-500/30 bg-blue-500/5 px-3 py-2">
          <div className="flex items-start gap-2">
            <Info className="h-4 w-4 text-blue-300 mt-0.5 shrink-0" />
            <p className="text-[11px] text-blue-100/90 leading-relaxed">
              <strong>How to read these metrics:</strong> the three experts use
              <em> different rubrics</em> (psychometric vs. domain vs. localization),
              so per-item score disagreement is expected and informative. The
              headline α measures whether they agree on the <em>bottom-line
              verdict</em> (accept / revise / reject). Spearman ρ below shows
              whether they agree on which items are best vs. worst.
            </p>
          </div>
        </div>

        {/* IRR warning — only fires when verdict-level disagreement is genuinely concerning */}
        {consensus.irr_warning && (
          <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-300 mt-0.5 shrink-0" />
              <span className="text-xs text-amber-200 leading-relaxed">
                {consensus.irr_warning}
              </span>
            </div>
          </div>
        )}

        {/* Per-expert summary tiles — full text now (no line-clamp) */}
        <div className="grid gap-3 sm:grid-cols-3 mb-5">
          {finalEvals.map((ev, idx) => {
            const scores = Object.values(ev.item_scores);
            const meanScore =
              scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
            return (
              <div
                key={idx}
                className="flex flex-col rounded-lg border border-border/40 bg-slate-900/30 p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-slate-50">{ev.expert_label}</span>
                  <Badge className={verdictBadgeColor(ev.overall_verdict)}>
                    {ev.overall_verdict}
                  </Badge>
                </div>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className="text-2xl font-bold tabular-nums text-[#a7d12b]">
                    {meanScore.toFixed(2)}
                  </span>
                  <span className="text-[10px] uppercase text-muted-foreground/70">
                    mean / 5
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground/90 mt-1 leading-relaxed">
                  {ev.overall_summary || "No additional commentary."}
                </p>
              </div>
            );
          })}
        </div>

        {/* Per-expert verbatim — expandable per expert */}
        <div className="mb-5">
          <h4 className="text-sm font-semibold text-slate-50 mb-2">
            Full review — click any expert to expand
          </h4>
          <div className="space-y-2">
            {finalEvals.map((ev, idx) => (
              <ExpertVerbatimSection key={idx} ev={ev} />
            ))}
          </div>
          <p className="text-[10px] text-muted-foreground/70 mt-2 italic">
            Tip: the full panel review (every score + comment) is also included in
            the Markdown / JSON download from the Generated Items panel below.
          </p>
        </div>

        {/* Pairwise Spearman ρ — the meaningful pairwise metric for differing rubrics */}
        {consensus.irr_pairwise_spearman && Object.keys(consensus.irr_pairwise_spearman).length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-slate-50 mb-2">
              Pairwise Spearman ρ
              <span className="ml-2 text-[10px] uppercase text-muted-foreground/70">
                (relative item ordering — robust to rubric differences)
              </span>
            </h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(consensus.irr_pairwise_spearman).map(([pair, rho]) => (
                <Badge
                  key={pair}
                  variant="outline"
                  className={`text-[11px] ${rho == null ? "text-muted-foreground" : irrColor(rho)}`}
                >
                  {pair.replace("|", " ↔ ")}: ρ = {rho == null ? "— (not estimable)" : rho.toFixed(2)}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Pairwise Cohen's κ — kept as legacy/secondary signal */}
        {Object.keys(consensus.irr_pairwise).length > 0 && (
          <details className="mb-4 rounded border border-border/30 bg-slate-900/30 px-3 py-2">
            <summary className="cursor-pointer text-xs text-muted-foreground/80">
              Legacy: pairwise weighted Cohen&apos;s κ (fixed 1–5 scale) on raw scores (low values are expected with differing rubrics)
            </summary>
            <div className="flex flex-wrap gap-2 mt-2">
              {Object.entries(consensus.irr_pairwise).map(([pair, kappa]) => (
                <Badge
                  key={pair}
                  variant="outline"
                  className="text-[11px] text-muted-foreground"
                >
                  {pair.replace("|", " ↔ ")}: κ = {kappa == null ? "— (not estimable)" : kappa.toFixed(2)}
                </Badge>
              ))}
            </div>
          </details>
        )}

        {/* Dissent flags */}
        {consensus.dissent_flags.length > 0 && (
          <div className="mb-5 rounded-lg border border-border/40 bg-slate-900/30 px-4 py-3">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              <span className="text-sm font-semibold text-slate-50">
                {consensus.dissent_flags.length} item{consensus.dissent_flags.length === 1 ? "" : "s"} with cross-rubric disagreement (SD ≥ 1.0)
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground/80">
              Items: {consensus.dissent_flags.map((i) => i + 1).join(", ")}.
              These items provoke the strongest disagreement across the three lenses — worth reviewing manually.
            </p>
          </div>
        )}

        {/* Consensus revisions applied */}
        {consensus.consensus_revisions.edits.length > 0 ? (
          <div className="mb-4 rounded-lg border border-[#a7d12b]/30 bg-[#a7d12b]/10 px-4 py-3">
            <span className="text-sm font-semibold text-[#a7d12b]">
              {consensus.consensus_revisions.edits.length} consensus revision
              {consensus.consensus_revisions.edits.length === 1 ? "" : "s"} applied
            </span>
            <p className="text-[11px] text-muted-foreground/80 mt-1 leading-relaxed">
              {consensus.consensus_revisions.summary}
            </p>
          </div>
        ) : (
          <div className="mb-4 rounded-lg border border-[#a7d12b]/30 bg-[#a7d12b]/10 px-4 py-3 flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 text-[#a7d12b] mt-0.5 shrink-0" />
            <span className="text-sm text-[#a7d12b] leading-relaxed">
              {consensus.consensus_revisions.summary || "All items passed expert panel review."}
            </span>
          </div>
        )}

        {/* Debate diff (collapsible) */}
        {consensus.debate_revisions.length > 0 && (
          <button
            type="button"
            onClick={() => setShowDebate((s) => !s)}
            className="flex items-center gap-1 text-[11px] text-muted-foreground/80 hover:text-[#a7d12b] mt-2"
          >
            {showDebate ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            Show debate-round revisions
          </button>
        )}
        {showDebate && consensus.debate_revisions.length > 0 && (
          <div className="mt-3 space-y-2">
            {consensus.debate_revisions.map((ev, idx) => {
              const round1 = consensus.evaluations[idx];
              return (
                <div
                  key={idx}
                  className="rounded border border-border/30 bg-slate-900/30 px-3 py-2"
                >
                  <span className="text-[11px] font-semibold text-slate-50">
                    {ev.expert_label}
                  </span>
                  <p className="text-[10px] text-muted-foreground/80 mt-1">
                    Verdict: {round1?.overall_verdict || "—"} → {ev.overall_verdict}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </SurfaceCard>
  );
}
