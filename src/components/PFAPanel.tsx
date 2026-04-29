"use client";

import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import type { PFAResult } from "@/lib/types";

export interface PFAPanelProps {
  pfa: PFAResult;
}

function verdictBadge(v: string): { color: string; icon: React.ReactNode; label: string } {
  if (v === "good") {
    return {
      color: "bg-[#a7d12b]/15 text-[#a7d12b] border-[#a7d12b]/30",
      icon: <CheckCircle2 className="h-3.5 w-3.5" />,
      label: "Good fit",
    };
  }
  if (v === "acceptable") {
    return {
      color: "bg-amber-500/15 text-amber-300 border-amber-500/30",
      icon: <AlertTriangle className="h-3.5 w-3.5" />,
      label: "Acceptable fit",
    };
  }
  return {
    color: "bg-red-500/15 text-red-300 border-red-500/30",
    icon: <XCircle className="h-3.5 w-3.5" />,
    label: "Poor fit — consider redrafting",
  };
}

function congruenceColor(c: number): string {
  if (c >= 0.95) return "text-[#a7d12b]";
  if (c >= 0.85) return "text-[#a7d12b]/80";
  if (c >= 0.70) return "text-amber-300";
  return "text-red-300";
}

function loadingHeatColor(loading: number): string {
  const abs = Math.min(Math.abs(loading), 1.0);
  // Map abs(loading) to opacity of #a7d12b
  const opacity = Math.round(abs * 100);
  return `rgba(167, 209, 43, ${opacity / 100})`;
}

export function PFAPanel({ pfa }: PFAPanelProps) {
  const verdict = verdictBadge(pfa.fit_verdict);
  const meanCongruence =
    pfa.tuckers_congruence.length > 0
      ? pfa.tuckers_congruence.reduce((a, b) => a + b, 0) / pfa.tuckers_congruence.length
      : 0;

  return (
    <SurfaceCard className="mt-4 border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base md:text-lg">
            Factor Structure (Pre-Calibration)
          </CardTitle>
          <Badge className={`gap-1.5 ${verdict.color}`}>
            {verdict.icon}
            {verdict.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        {/* Saturated-model banner — RMSR=0 / CAF=1 are uninformative when n_items is too small */}
        {pfa.model_identifiability === "saturated" && (
          <div className="mb-4 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-amber-300" />
              <span className="text-sm font-semibold text-amber-200">
                Saturated model — fit indices uninformative
              </span>
            </div>
            <p className="text-[12px] text-amber-100/90">
              With {pfa.n_items} item{pfa.n_items === 1 ? "" : "s"} on {pfa.n_factors} factor
              {pfa.n_factors === 1 ? "" : "s"}, the model has zero degrees of freedom, so the
              correlation matrix is reproduced exactly (RMSR = 0, CAF = 1) by construction. The
              loadings remain interpretable, but Tucker&apos;s congruence and recovery are the
              meaningful signals here. Generate more items per factor for diagnostic fit.
            </p>
          </div>
        )}

        {/* Summary cards */}
        <div className="grid gap-4 sm:grid-cols-3 mb-6">
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-slate-50">Mean Tucker&apos;s Congruence</h4>
            <span className={`mt-2 text-2xl font-bold tabular-nums ${congruenceColor(meanCongruence)}`}>
              {meanCongruence.toFixed(3)}
            </span>
            <span className="mt-1 text-[10px] uppercase font-medium text-muted-foreground/70">
              {meanCongruence >= 0.95 ? "Excellent" : meanCongruence >= 0.85 ? "Fair" : "Below threshold"}
            </span>
          </div>
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-slate-50">Factor Recovery</h4>
            <span className="mt-2 text-2xl font-bold tabular-nums text-[#a7d12b]">
              {(pfa.factor_recovery_rate * 100).toFixed(0)}%
            </span>
            <span className="mt-1 text-[10px] uppercase font-medium text-muted-foreground/70">
              of {pfa.n_factors} factor{pfa.n_factors === 1 ? "" : "s"} recovered
            </span>
          </div>
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-slate-50">RMSR / CAF</h4>
            <span className="mt-2 text-lg font-bold tabular-nums text-[#a7d12b]">
              {pfa.rmsr.toFixed(3)} / {pfa.caf.toFixed(3)}
            </span>
            <span className="mt-1 text-[10px] uppercase font-medium text-muted-foreground/70">
              residual / common-part
            </span>
          </div>
        </div>

        {/* Factor labels */}
        {pfa.factor_labels.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-slate-50 mb-2">Factor Labels (DAAL)</h4>
            <div className="flex flex-wrap gap-2">
              {pfa.factor_labels.map((label, idx) => (
                <Badge
                  key={idx}
                  variant="outline"
                  className="border-[#a7d12b]/30 text-[#a7d12b]"
                >
                  Factor {idx + 1}: {label}
                  {pfa.tuckers_congruence[idx] !== undefined && (
                    <span className={`ml-2 ${congruenceColor(pfa.tuckers_congruence[idx])}`}>
                      ({pfa.tuckers_congruence[idx].toFixed(2)})
                    </span>
                  )}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Loading heatmap */}
        {pfa.loadings.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-slate-50 mb-3">
              Item × Factor Loadings
            </h4>
            <div className="overflow-x-auto">
              <table className="text-xs">
                <thead>
                  <tr>
                    <th className="text-left px-2 py-1 text-muted-foreground/80">Item</th>
                    <th className="text-left px-2 py-1 text-muted-foreground/80">Facet</th>
                    {pfa.factor_labels.map((label, fi) => (
                      <th key={fi} className="px-2 py-1 text-center text-muted-foreground/80">
                        F{fi + 1}
                      </th>
                    ))}
                    <th className="px-2 py-1 text-center text-muted-foreground/80">OK</th>
                  </tr>
                </thead>
                <tbody>
                  {pfa.loadings.map((fl) => (
                    <tr key={fl.item_index} className="border-t border-border/30">
                      <td className="px-2 py-1.5 max-w-md truncate" title={fl.item_text}>
                        {fl.item_index + 1}. {fl.item_text}
                      </td>
                      <td className="px-2 py-1.5 text-muted-foreground/80">
                        {fl.facet_name || "—"}
                      </td>
                      {fl.loadings.map((load, fi) => (
                        <td
                          key={fi}
                          className="px-2 py-1.5 text-center tabular-nums"
                          style={{ backgroundColor: loadingHeatColor(load) }}
                        >
                          {load.toFixed(2)}
                        </td>
                      ))}
                      <td className="px-2 py-1.5 text-center">
                        {fl.is_well_loaded ? (
                          <CheckCircle2 className="inline h-4 w-4 text-[#a7d12b]" />
                        ) : (
                          <span title={fl.retention_rule_violations.join(", ")}>
                            <AlertTriangle className="inline h-4 w-4 text-amber-400" />
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Items dropped during pruning */}
        {pfa.items_dropped.length > 0 && (
          <div className="mb-4 rounded-lg border border-border/40 bg-slate-900/30 px-4 py-3">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              <span className="text-sm font-semibold text-slate-50">
                {pfa.items_dropped.length} items dropped during PFA pruning
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground/80">
              Original indices: {pfa.items_dropped.map((i) => i + 1).join(", ")}.
              Items failed the 4-rule retention check (Suárez-Álvarez et al., 2026).
            </p>
          </div>
        )}

        {/* Eigenvalues / scree (textual) */}
        {pfa.eigenvalues.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-slate-50 mb-2">Eigenvalues (top {pfa.eigenvalues.length})</h4>
            <div className="flex flex-wrap gap-1.5">
              {pfa.eigenvalues.map((e, idx) => (
                <Badge
                  key={idx}
                  variant="outline"
                  className={
                    e >= 1.0
                      ? "border-[#a7d12b]/30 text-[#a7d12b]"
                      : "border-border/30 text-muted-foreground"
                  }
                >
                  λ{idx + 1} = {e.toFixed(2)}
                </Badge>
              ))}
            </div>
            <p className="text-[10px] italic text-muted-foreground/70 mt-1">
              Kaiser criterion: factors with λ ≥ 1.0 are typically retained.
            </p>
          </div>
        )}

        {/* Disclaimer */}
        <div className="mt-4 pt-4 border-t border-border/30">
          <p className="text-[11px] italic text-muted-foreground/70">
            {pfa.disclaimer}
          </p>
        </div>
      </CardContent>
    </SurfaceCard>
  );
}
