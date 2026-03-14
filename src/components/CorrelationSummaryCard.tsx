"use client";

import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import type { CorrelationMatrix } from "@/lib/types";

export interface CorrelationSummaryCardProps {
  matrix: CorrelationMatrix;
}

function getOmegaColor(omega: number): string {
  return omega >= 0.70 ? "text-emerald-400" : "text-amber-400";
}

function getOmegaLabel(omega: number): string {
  return omega >= 0.70 ? "Reliable" : "Below threshold";
}

function getMeanRColor(meanR: number): string {
  if (meanR >= 0.15 && meanR <= 0.50) return "text-emerald-400";
  return "text-amber-400";
}

function getMeanRLabel(meanR: number): string {
  if (meanR >= 0.15 && meanR <= 0.50) return "Optimal";
  if (meanR < 0.15) return "Low";
  return "High";
}

function getConsistencyText(flag: string): string {
  switch (flag) {
    case 'optimal_range':
      return 'Items show good internal consistency';
    case 'too_low':
      return 'Items may measure different constructs';
    case 'too_high':
      return 'Items may be redundant or overly similar';
    case 'calculation_failed':
      return 'Unable to calculate consistency metrics';
    default:
      return flag;
  }
}

function getConsistencyColor(flag: string): string {
  return flag === 'optimal_range' ? 'text-emerald-400' : 'text-amber-400';
}

export function CorrelationSummaryCard({ matrix }: CorrelationSummaryCardProps) {
  return (
    <SurfaceCard className="mt-4">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-base">Quality Metrics</CardTitle>
      </CardHeader>
      <CardContent className="pt-5">
        <div className="grid gap-4 sm:grid-cols-3">
          {/* McDonald's Omega */}
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-foreground">McDonald&apos;s Omega</h4>
            <span className={`mt-2 text-2xl font-bold tabular-nums ${getOmegaColor(matrix.mcdonalds_omega)}`}>
              {matrix.mcdonalds_omega.toFixed(3)}
            </span>
            <span className={`mt-1 text-[10px] font-medium uppercase ${getOmegaColor(matrix.mcdonalds_omega)}`}>
              {getOmegaLabel(matrix.mcdonalds_omega)}
            </span>
          </div>

          {/* Mean Inter-Item Correlation */}
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-foreground">Mean Inter-Item r</h4>
            <span className={`mt-2 text-2xl font-bold tabular-nums ${getMeanRColor(matrix.mean_inter_item_correlation)}`}>
              {matrix.mean_inter_item_correlation.toFixed(3)}
            </span>
            <span className={`mt-1 text-[10px] font-medium uppercase ${getMeanRColor(matrix.mean_inter_item_correlation)}`}>
              {getMeanRLabel(matrix.mean_inter_item_correlation)}
            </span>
          </div>

          {/* Internal Consistency Assessment */}
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-foreground">Internal Consistency</h4>
            <span className={`mt-2 text-xs font-medium ${getConsistencyColor(matrix.internal_consistency_flag)}`}>
              {getConsistencyText(matrix.internal_consistency_flag)}
            </span>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-4 pt-4 border-t border-border/30">
          <p className="text-[11px] italic text-muted-foreground/70">
            {matrix.disclaimer}
          </p>
        </div>
      </CardContent>
    </SurfaceCard>
  );
}
