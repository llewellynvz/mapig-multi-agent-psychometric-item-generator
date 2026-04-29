"use client";

import { AlertTriangle, AlertCircle } from "lucide-react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";
import { SurfaceCard } from "@/components/ui/surface-card";
import type { AuditMetadata, FinalItem } from "@/lib/types";

export interface QualityChecksPanelProps {
  items: FinalItem[];
  audit?: AuditMetadata;
}

function wordCount(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function getWarnings(item: FinalItem, index: number): { type: string; message: string }[] {
  const warnings: { type: string; message: string }[] = [];
  const lower = item.item_text.toLowerCase();

  if (lower.includes("and/or")) {
    warnings.push({ type: "and_or", message: "Contains 'and/or'" });
  }
  if (/\b(not|never|no)\b/.test(lower) || /n['’]t\b/.test(lower)) {
    warnings.push({ type: "negation", message: "Contains negation (not, never, no, n't)" });
  }
  if (wordCount(item.item_text) > 25) {
    warnings.push({ type: "length", message: `Over 25 words (${wordCount(item.item_text)})` });
  }
  return warnings;
}

export function QualityChecksPanel({ items, audit }: QualityChecksPanelProps) {
  const allWarnings = items.flatMap((item, i) =>
    getWarnings(item, i).map((w) => ({ itemIndex: i + 1, ...w }))
  );

  const auditWarnings = audit?.warnings ?? [];
  const forceAccepted = audit?.force_accepted_below_threshold === true;
  const forcedScores = audit?.forced_scores ?? [];

  // If nothing to surface, render nothing.
  if (allWarnings.length === 0 && auditWarnings.length === 0 && !forceAccepted) {
    return null;
  }

  return (
    <SurfaceCard>
      <CardHeader className="border-b border-border/60">
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="h-4 w-4 text-white" />
          Quality checks
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-5 space-y-4">
        {/* Force-accept banner — items shipped despite scoring below 7.0 */}
        {forceAccepted && (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="h-4 w-4 text-amber-300" />
              <span className="text-sm font-semibold text-amber-200">
                Items shipped below validation threshold
              </span>
            </div>
            <p className="text-[12px] text-amber-100/90">
              {forcedScores.length > 0
                ? `${forcedScores.length} item${forcedScores.length === 1 ? "" : "s"} fell below the 7.0 weighted-score threshold (scores: ${forcedScores
                    .map((s) => s.toFixed(2))
                    .join(", ")}). The pipeline kept the top-scoring set as a fallback. Consider refining the construct definition or constraints and re-running.`
                : "One or more items fell below the 7.0 weighted-score threshold. Consider refining the construct definition or constraints and re-running."}
            </p>
          </div>
        )}

        {/* Audit warnings (e.g., construct/definition mismatch) */}
        {auditWarnings.length > 0 && (
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 space-y-1.5">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-300" />
              <span className="text-sm font-semibold text-amber-200">Setup warnings</span>
            </div>
            {auditWarnings.map((w, i) => (
              <p key={i} className="text-[12px] text-amber-100/90">
                {w}
              </p>
            ))}
          </div>
        )}

        {/* Per-item heuristic warnings */}
        {allWarnings.length > 0 && (
          <div>
            <p className="mb-2 text-sm text-muted-foreground">
              Non-blocking client-side heuristics.
            </p>
            <ul className="space-y-1">
              {allWarnings.map((w, i) => (
                <li key={i} className="flex items-center gap-2 text-sm">
                  <Pill className="font-normal">Item {w.itemIndex}</Pill>
                  <span className="text-slate-100">{w.message}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </SurfaceCard>
  );
}
