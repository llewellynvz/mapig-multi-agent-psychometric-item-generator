"use client";

import { useState } from "react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Download, FlaskConical } from "lucide-react";
import { MethodBadge } from "./MethodBadge";
import { exportSyntheticPilotToCsv } from "@/lib/export-correlation";
import type { SyntheticPilotResult } from "@/lib/types";

export interface SyntheticPilotPanelProps {
  pilot: SyntheticPilotResult;
  itemTexts?: string[];
}

function StatCell({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
      <span className="flex items-center justify-center gap-1.5 text-[10px] uppercase font-medium text-muted-foreground/70">
        {label}
        <MethodBadge variant="synthetic" className="px-1.5 text-[8px]" />
      </span>
      <span className="text-xl font-bold text-[#a7d12b] tabular-nums block mt-1">
        {value}
      </span>
      {hint && (
        <span className="text-[10px] text-muted-foreground/60 block mt-0.5">{hint}</span>
      )}
    </div>
  );
}

function fmt(value: number | null, digits = 3): string {
  return value == null ? "Not estimable" : value.toFixed(digits);
}

export function SyntheticPilotPanel({ pilot, itemTexts }: SyntheticPilotPanelProps) {
  const [expanded, setExpanded] = useState(true);
  const [showCorrelations, setShowCorrelations] = useState(false);

  const strongestCells = [...pilot.cells]
    .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
    .slice(0, 10);

  const bartlett =
    pilot.bartlett_chi2 == null || pilot.bartlett_p == null
      ? "Not estimable"
      : `χ² = ${pilot.bartlett_chi2.toFixed(1)}, p ${
          pilot.bartlett_p < 0.001 ? "< .001" : `= ${pilot.bartlett_p.toFixed(3)}`
        }`;

  const handleExportCsv = () => {
    const csv = exportSyntheticPilotToCsv(pilot, itemTexts ?? []);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "synthetic_pilot.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <SurfaceCard className="border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <button
          type="button"
          onClick={() => setExpanded((s) => !s)}
          className="w-full flex items-center justify-between text-left"
        >
          <CardTitle className="text-base md:text-lg flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-[#a7d12b]" />
            Synthetic-Respondent Pilot
            <MethodBadge variant="synthetic" />
          </CardTitle>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-[#a7d12b]/30 text-[#a7d12b]">
              N = {pilot.n_respondents}
            </Badge>
            {expanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </button>
      </CardHeader>
      {expanded && (
        <CardContent className="pt-5">
          <div className="flex items-start justify-between gap-3 mb-4">
            <p className="text-xs text-amber-200/90 border border-amber-500/30 bg-amber-500/10 rounded-lg p-3 flex-1">
              {pilot.disclaimer}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportCsv}
              className="shrink-0"
              aria-label="Export synthetic pilot statistics as CSV"
            >
              <Download className="h-3.5 w-3.5 mr-1.5" />
              CSV
            </Button>
          </div>

          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 mb-4">
            <StatCell
              label="Cronbach's α"
              value={fmt(pilot.cronbach_alpha)}
              hint="Internal consistency on the simulated matrix"
            />
            <StatCell
              label="Omega-total"
              value={fmt(pilot.omega_total)}
              hint="From a minres EFA on the simulated matrix"
            />
            <StatCell
              label="KMO"
              value={fmt(pilot.kmo, 2)}
              hint="Sampling adequacy"
            />
            <StatCell
              label="Bartlett sphericity"
              value={bartlett}
              hint="Correlations differ from identity"
            />
          </div>

          <div className="grid gap-2 sm:grid-cols-2 mb-4">
            <StatCell
              label="Parallel analysis"
              value={
                pilot.parallel_analysis_n_factors == null
                  ? "Not estimable"
                  : `${pilot.parallel_analysis_n_factors} factor${
                      pilot.parallel_analysis_n_factors === 1 ? "" : "s"
                    }`
              }
              hint="Horn's method, 95th percentile of random eigenvalues"
            />
            <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3">
              <span className="flex items-center gap-1.5 text-[10px] uppercase font-medium text-muted-foreground/70">
                Pilot details
              </span>
              <span className="text-xs text-muted-foreground block mt-1">
                {pilot.n_respondents} simulated respondents × {pilot.n_items} items on a{" "}
                {pilot.scale_points}-point scale ({pilot.model_name})
                {pilot.failed_respondents > 0 &&
                  `; ${pilot.failed_respondents} respondent call${
                    pilot.failed_respondents === 1 ? "" : "s"
                  } failed and were excluded`}
                .
              </span>
            </div>
          </div>

          {pilot.observed_eigenvalues.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-slate-50 mb-2 flex items-center gap-2">
                Eigenvalues vs random-data thresholds
                <MethodBadge variant="synthetic" className="px-1.5 text-[8px]" />
              </h4>
              <div className="overflow-x-auto">
                <table className="text-xs w-full">
                  <thead>
                    <tr className="text-muted-foreground/70 text-left">
                      <th className="pr-4 pb-1 font-medium">Component</th>
                      <th className="pr-4 pb-1 font-medium">Observed λ</th>
                      <th className="pr-4 pb-1 font-medium">Random 95th %ile</th>
                      <th className="pb-1 font-medium">Retained</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pilot.observed_eigenvalues.map((eig, i) => {
                      const threshold = pilot.threshold_eigenvalues[i];
                      const retained = threshold != null && eig > threshold;
                      return (
                        <tr key={i} className="border-t border-border/30">
                          <td className="pr-4 py-1 tabular-nums">{i + 1}</td>
                          <td className="pr-4 py-1 tabular-nums">{eig.toFixed(3)}</td>
                          <td className="pr-4 py-1 tabular-nums">
                            {threshold != null ? threshold.toFixed(3) : "—"}
                          </td>
                          <td className={retained ? "text-[#a7d12b]" : "text-muted-foreground/60"}>
                            {retained ? "Yes" : "No"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {strongestCells.length > 0 && (
            <div>
              <button
                type="button"
                onClick={() => setShowCorrelations((s) => !s)}
                className="text-sm font-semibold text-slate-50 mb-2 flex items-center gap-2"
              >
                Strongest inter-item correlations (Pearson, 95% CI)
                <MethodBadge variant="synthetic" className="px-1.5 text-[8px]" />
                {showCorrelations ? (
                  <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                )}
              </button>
              {showCorrelations && (
                <div className="overflow-x-auto">
                  <table className="text-xs w-full">
                    <thead>
                      <tr className="text-muted-foreground/70 text-left">
                        <th className="pr-4 pb-1 font-medium">Item pair</th>
                        <th className="pr-4 pb-1 font-medium">r</th>
                        <th className="pb-1 font-medium">95% CI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {strongestCells.map((cell) => (
                        <tr
                          key={`${cell.item_i_index}-${cell.item_j_index}`}
                          className="border-t border-border/30"
                        >
                          <td
                            className="pr-4 py-1"
                            title={
                              itemTexts
                                ? `${itemTexts[cell.item_i_index] ?? ""} × ${
                                    itemTexts[cell.item_j_index] ?? ""
                                  }`
                                : undefined
                            }
                          >
                            {cell.item_i_index + 1} × {cell.item_j_index + 1}
                          </td>
                          <td className="pr-4 py-1 tabular-nums">
                            {cell.correlation.toFixed(3)}
                          </td>
                          <td className="py-1 tabular-nums">
                            {cell.ci_low != null && cell.ci_high != null
                              ? `[${cell.ci_low.toFixed(3)}, ${cell.ci_high.toFixed(3)}]`
                              : "Not estimable"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </CardContent>
      )}
    </SurfaceCard>
  );
}
