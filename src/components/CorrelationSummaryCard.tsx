"use client";

import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";
import { SurfaceCard } from "@/components/ui/surface-card";
import type { CorrelationMatrix } from "@/lib/types";

export interface CorrelationSummaryCardProps {
  matrix: CorrelationMatrix;
}

/**
 * Get status pill for McDonald's Omega
 */
function getOmegaStatus(omega: number): { label: string; className: string } {
  return omega >= 0.70
    ? { label: 'Pass', className: 'bg-green-500/20 text-green-400 border-green-500/40' }
    : { label: 'Warning', className: 'bg-amber-500/20 text-amber-400 border-amber-500/40' };
}

/**
 * Get status pill for mean inter-item correlation
 */
function getMeanRStatus(meanR: number): { label: string; className: string } {
  if (meanR >= 0.15 && meanR <= 0.50) {
    return { label: 'Optimal', className: 'bg-green-500/20 text-green-400 border-green-500/40' };
  }
  if (meanR < 0.15) {
    return { label: 'Low', className: 'bg-amber-500/20 text-amber-400 border-amber-500/40' };
  }
  return { label: 'High', className: 'bg-amber-500/20 text-amber-400 border-amber-500/40' };
}

/**
 * Get consistency assessment text based on flag
 */
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

export function CorrelationSummaryCard({ matrix }: CorrelationSummaryCardProps) {
  const omegaStatus = getOmegaStatus(matrix.mcdonalds_omega);
  const meanRStatus = getMeanRStatus(matrix.mean_inter_item_correlation);

  return (
    <SurfaceCard className="mt-4">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-base">Quality Metrics</CardTitle>
      </CardHeader>
      <CardContent className="pt-5">
        <div className="grid gap-4 md:grid-cols-2">
          {/* McDonald's Omega */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">
                McDonald's Omega:
              </span>
              <span className="text-lg font-bold text-foreground">
                {matrix.mcdonalds_omega.toFixed(3)}
              </span>
              <Pill className={omegaStatus.className}>{omegaStatus.label}</Pill>
            </div>
            <p className="text-xs text-muted-foreground">
              Measures how well items consistently measure the same construct
            </p>
          </div>

          {/* Mean Inter-Item Correlation */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">
                Mean Inter-Item r:
              </span>
              <span className="text-lg font-bold text-foreground">
                {matrix.mean_inter_item_correlation.toFixed(3)}
              </span>
              <Pill className={meanRStatus.className}>{meanRStatus.label}</Pill>
            </div>
            <p className="text-xs text-muted-foreground">
              Average correlation between all item pairs; 0.15-0.50 is optimal for broad constructs
            </p>
          </div>

          {/* Internal Consistency Assessment */}
          <div className="space-y-2 md:col-span-2">
            <div className="text-sm font-semibold text-foreground">
              Internal Consistency Assessment
            </div>
            <p className="text-sm text-muted-foreground">
              {getConsistencyText(matrix.internal_consistency_flag)}
            </p>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-4 border-t border-border/40 pt-4">
          <p className="text-xs italic text-muted-foreground">
            {matrix.disclaimer}
          </p>
        </div>
      </CardContent>
    </SurfaceCard>
  );
}
