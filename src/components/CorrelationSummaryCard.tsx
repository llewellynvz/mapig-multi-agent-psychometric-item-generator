"use client";

import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { AlertTriangle } from "lucide-react";
import type { CorrelationMatrix } from "@/lib/types";

export interface CorrelationSummaryCardProps {
  matrix: CorrelationMatrix;
}

function getOmegaColor(omega: number): string {
  return omega >= 0.70 ? "text-[#a7d12b]" : "text-[#a7d12b]/70";
}

function getOmegaLabel(omega: number): string {
  return omega >= 0.70 ? "Reliable" : "Below threshold";
}

function getMeanRColor(meanR: number): string {
  if (meanR >= 0.15 && meanR <= 0.50) return "text-[#a7d12b]";
  return "text-[#a7d12b]/70";
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
  return flag === 'optimal_range' ? 'text-[#a7d12b]' : 'text-[#a7d12b]/70';
}

export function CorrelationSummaryCard({ matrix }: CorrelationSummaryCardProps) {
  return (
    <SurfaceCard className="mt-4 border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-base">Quality Metrics</CardTitle>
      </CardHeader>
      <CardContent className="pt-5">
        <div className="grid gap-4 sm:grid-cols-3">
          {/* McDonald's Omega */}
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-slate-50">McDonald&apos;s Omega</h4>
            <span className={`mt-2 text-2xl font-bold tabular-nums ${getOmegaColor(matrix.mcdonalds_omega)}`}>
              {matrix.mcdonalds_omega.toFixed(3)}
            </span>
            <span className={`mt-1 text-[10px] font-medium uppercase ${getOmegaColor(matrix.mcdonalds_omega)}`}>
              {getOmegaLabel(matrix.mcdonalds_omega)}
            </span>
          </div>

          {/* Mean Inter-Item Correlation */}
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-slate-50">Mean Inter-Item r</h4>
            <span className={`mt-2 text-2xl font-bold tabular-nums ${getMeanRColor(matrix.mean_inter_item_correlation)}`}>
              {matrix.mean_inter_item_correlation.toFixed(3)}
            </span>
            <span className={`mt-1 text-[10px] font-medium uppercase ${getMeanRColor(matrix.mean_inter_item_correlation)}`}>
              {getMeanRLabel(matrix.mean_inter_item_correlation)}
            </span>
          </div>

          {/* Internal Consistency Assessment */}
          <div className="flex flex-col items-center text-center rounded-lg border border-border/40 bg-slate-900/30 p-4">
            <h4 className="text-sm font-semibold text-slate-50">Internal Consistency</h4>
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

        {matrix.redundancy_flags && matrix.redundancy_flags.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border/30">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-[#a7d12b]" />
              <span className="text-sm font-semibold text-[#a7d12b]">Redundancy Warnings</span>
            </div>
            <div className="space-y-1.5">
              {matrix.redundancy_flags.map((flag, idx) => (
                <div key={idx} className="rounded-lg bg-[#a7d12b]/10 border border-[#a7d12b]/20 px-3 py-2">
                  <span className="text-xs font-medium text-[#a7d12b]">{flag}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </SurfaceCard>
  );
}
