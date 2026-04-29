"use client";

import { useState } from "react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronUp, AlertTriangle, CheckCircle2, Users } from "lucide-react";
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

export function ExpertPanelCard({ consensus }: ExpertPanelCardProps) {
  const [showDebate, setShowDebate] = useState(false);
  const finalEvals: ExpertEvaluation[] =
    consensus.debate_revisions.length > 0 ? consensus.debate_revisions : consensus.evaluations;

  return (
    <SurfaceCard className="mt-4 border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base md:text-lg flex items-center gap-2">
            <Users className="h-4 w-4 text-[#a7d12b]" />
            Expert Face/Content Validity
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={`tabular-nums ${irrColor(consensus.irr_alpha)}`}>
              α = {consensus.irr_alpha != null ? consensus.irr_alpha.toFixed(2) : "—"}
            </Badge>
            <span className="text-[11px] uppercase font-medium text-muted-foreground/80">
              {irrLabel(consensus.irr_alpha)}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        {consensus.irr_warning && (
          <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-300" />
              <span className="text-xs text-amber-200">{consensus.irr_warning}</span>
            </div>
          </div>
        )}

        {/* Per-expert summary */}
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
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="text-2xl font-bold tabular-nums text-[#a7d12b]">
                    {meanScore.toFixed(2)}
                  </span>
                  <span className="text-[10px] uppercase text-muted-foreground/70">
                    mean / 5
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground/80 mt-1 line-clamp-3">
                  {ev.overall_summary || "No additional commentary."}
                </p>
              </div>
            );
          })}
        </div>

        {/* Pairwise IRR */}
        {Object.keys(consensus.irr_pairwise).length > 0 && (
          <div className="mb-5">
            <h4 className="text-sm font-semibold text-slate-50 mb-2">Pairwise Cohen&apos;s κ</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(consensus.irr_pairwise).map(([pair, kappa]) => (
                <Badge
                  key={pair}
                  variant="outline"
                  className={`text-[11px] ${irrColor(kappa)}`}
                >
                  {pair.replace("|", " ↔ ")}: {kappa.toFixed(2)}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Dissent flags */}
        {consensus.dissent_flags.length > 0 && (
          <div className="mb-5 rounded-lg border border-border/40 bg-slate-900/30 px-4 py-3">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              <span className="text-sm font-semibold text-slate-50">
                {consensus.dissent_flags.length} item{consensus.dissent_flags.length === 1 ? "" : "s"} with expert disagreement
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground/80">
              Items: {consensus.dissent_flags.map((i) => i + 1).join(", ")}.
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
            <p className="text-[11px] text-muted-foreground/80 mt-1">
              {consensus.consensus_revisions.summary}
            </p>
          </div>
        ) : (
          <div className="mb-4 rounded-lg border border-[#a7d12b]/30 bg-[#a7d12b]/10 px-4 py-3 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-[#a7d12b]" />
            <span className="text-sm text-[#a7d12b]">
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
