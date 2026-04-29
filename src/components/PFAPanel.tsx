"use client";

import { useMemo } from "react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import type { PFAResult, FactorLoading } from "@/lib/types";

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
  if (c >= 0.7) return "text-amber-300";
  return "text-red-300";
}

/** SEM-style path diagram. Latent factors on the left (ellipses), items on
 * the right (rectangles), arrows from each factor to each item labeled with
 * the loading value. Strong loadings get thick green arrows, weak loadings
 * get thin grey arrows.
 */
function PathDiagram({ pfa }: { pfa: PFAResult }) {
  const layout = useMemo(() => {
    const factors = pfa.factor_labels.length > 0
      ? pfa.factor_labels
      : Array.from({ length: pfa.n_factors }, (_, i) => `Factor ${i + 1}`);
    const items = pfa.loadings;

    // Layout constants
    const factorBoxW = 180;
    const factorBoxH = 60;
    const itemBoxW = 360;
    const itemBoxH = 38;
    const itemGap = 14;
    const factorGap = 80;
    const colGap = 240; // space for the arrows
    const padX = 24;
    const padY = 24;

    const factorColX = padX;
    const itemColX = padX + factorBoxW + colGap;

    const totalH = Math.max(
      padY * 2 + factors.length * (factorBoxH + factorGap) - factorGap,
      padY * 2 + items.length * (itemBoxH + itemGap) - itemGap,
    );
    const totalW = itemColX + itemBoxW + padX;

    // Y positions
    const factorYs = factors.map((_, i) => {
      const blockH = factors.length * (factorBoxH + factorGap) - factorGap;
      const start = (totalH - blockH) / 2;
      return start + i * (factorBoxH + factorGap);
    });
    const itemYs = items.map((_, i) => {
      const blockH = items.length * (itemBoxH + itemGap) - itemGap;
      const start = (totalH - blockH) / 2;
      return start + i * (itemBoxH + itemGap);
    });

    return {
      factors,
      items,
      factorBoxW,
      factorBoxH,
      itemBoxW,
      itemBoxH,
      factorColX,
      itemColX,
      factorYs,
      itemYs,
      totalW,
      totalH,
    };
  }, [pfa]);

  // Threshold: only draw "weak" arrows above 0.10 to reduce visual noise
  const minArrowMagnitude = 0.10;

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${layout.totalW} ${layout.totalH}`}
        width="100%"
        style={{ minWidth: 600, maxWidth: layout.totalW, height: "auto" }}
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#a7d12b" opacity="0.65" />
          </marker>
          <marker
            id="arrow-weak"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" opacity="0.55" />
          </marker>
        </defs>

        {/* Arrows: factor → item (drawn first so boxes overlap them at endpoints) */}
        {layout.items.map((fl, itemIdx) => {
          const itemY = layout.itemYs[itemIdx] + layout.itemBoxH / 2;
          return fl.loadings.map((load, fi) => {
            const abs = Math.abs(load);
            if (abs < minArrowMagnitude) return null;
            const factorY = layout.factorYs[fi] + layout.factorBoxH / 2;
            const x1 = layout.factorColX + layout.factorBoxW;
            const x2 = layout.itemColX;
            const isPrimary = fi === fl.primary_factor && abs >= 0.30;
            const stroke = isPrimary ? "#a7d12b" : "#475569";
            const strokeWidth = isPrimary
              ? Math.min(1 + abs * 3, 4)
              : Math.min(0.5 + abs * 1.5, 2);
            const opacity = isPrimary ? 0.85 : 0.45;
            const marker = isPrimary ? "url(#arrow)" : "url(#arrow-weak)";

            // Place loading label slightly above the midpoint of the line
            const midX = (x1 + x2) / 2;
            const midY = (factorY + itemY) / 2;

            return (
              <g key={`${itemIdx}-${fi}`}>
                <line
                  x1={x1}
                  y1={factorY}
                  x2={x2}
                  y2={itemY}
                  stroke={stroke}
                  strokeWidth={strokeWidth}
                  opacity={opacity}
                  markerEnd={marker}
                />
                {isPrimary && (
                  <text
                    x={midX}
                    y={midY - 4}
                    fill="#a7d12b"
                    fontSize="11"
                    fontWeight="600"
                    textAnchor="middle"
                    style={{ paintOrder: "stroke", stroke: "#0f172a", strokeWidth: 3 }}
                  >
                    {load.toFixed(2)}
                  </text>
                )}
              </g>
            );
          });
        })}

        {/* Factor ellipses (latent variables) */}
        {layout.factors.map((label, fi) => {
          const cx = layout.factorColX + layout.factorBoxW / 2;
          const cy = layout.factorYs[fi] + layout.factorBoxH / 2;
          const rx = layout.factorBoxW / 2 - 4;
          const ry = layout.factorBoxH / 2 - 4;
          const cong = pfa.tuckers_congruence[fi];
          return (
            <g key={`factor-${fi}`}>
              <ellipse
                cx={cx}
                cy={cy}
                rx={rx}
                ry={ry}
                fill="rgba(167, 209, 43, 0.10)"
                stroke="#a7d12b"
                strokeWidth="1.5"
              />
              <text
                x={cx}
                y={cy - 4}
                textAnchor="middle"
                fill="#a7d12b"
                fontSize="13"
                fontWeight="600"
              >
                F{fi + 1}: {label.length > 18 ? label.slice(0, 18) + "…" : label}
              </text>
              {cong !== undefined && (
                <text
                  x={cx}
                  y={cy + 12}
                  textAnchor="middle"
                  fill="#94a3b8"
                  fontSize="10"
                >
                  congruence {cong.toFixed(2)}
                </text>
              )}
            </g>
          );
        })}

        {/* Item rectangles (manifest variables) */}
        {layout.items.map((fl, itemIdx) => {
          const x = layout.itemColX;
          const y = layout.itemYs[itemIdx];
          const isWell = fl.is_well_loaded;
          const trimmed = fl.item_text.length > 50 ? fl.item_text.slice(0, 50) + "…" : fl.item_text;
          return (
            <g key={`item-${itemIdx}`}>
              <rect
                x={x}
                y={y}
                width={layout.itemBoxW}
                height={layout.itemBoxH}
                rx="4"
                ry="4"
                fill="rgba(15, 23, 42, 0.7)"
                stroke={isWell ? "#a7d12b" : "#f59e0b"}
                strokeWidth="1.5"
              />
              <text
                x={x + 8}
                y={y + 14}
                fill="#cbd5e1"
                fontSize="10"
                fontWeight="600"
              >
                Item {fl.item_index + 1}
              </text>
              <text
                x={x + 8}
                y={y + 28}
                fill="#e2e8f0"
                fontSize="11"
              >
                {trimmed}
              </text>
              {!isWell && (
                <title>{`Retention violations: ${fl.retention_rule_violations.join(", ")}`}</title>
              )}
            </g>
          );
        })}
      </svg>
      <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-0.5 bg-[#a7d12b]"></span>
          primary loading (≥ 0.30)
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-0.5 bg-slate-500"></span>
          cross-loading
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full border-2 border-[#a7d12b]"></span>
          item passed retention
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full border-2 border-amber-500"></span>
          retention violation
        </span>
      </div>
    </div>
  );
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
            Pseudo-Factor Analysis (Pre-Calibration)
          </CardTitle>
          <Badge className={`gap-1.5 ${verdict.color}`}>
            {verdict.icon}
            {verdict.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        {/* Saturated-model banner */}
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
              loadings remain interpretable.
            </p>
          </div>
        )}

        {/* SEM-style path diagram (centerpiece) */}
        {pfa.loadings.length > 0 && (
          <div className="mb-6 rounded-lg border border-border/40 bg-slate-950/60 p-3">
            <h4 className="text-sm font-semibold text-slate-50 mb-2">
              Measurement model
            </h4>
            <PathDiagram pfa={pfa} />
          </div>
        )}

        {/* Summary statistics */}
        <div className="grid gap-3 sm:grid-cols-4 mb-5">
          <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
            <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
              Mean Tucker&apos;s congruence
            </span>
            <span className={`mt-1 block text-xl font-bold tabular-nums ${congruenceColor(meanCongruence)}`}>
              {meanCongruence.toFixed(3)}
            </span>
          </div>
          <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
            <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
              Factor recovery
            </span>
            <span className="mt-1 block text-xl font-bold tabular-nums text-[#a7d12b]">
              {(pfa.factor_recovery_rate * 100).toFixed(0)}%
            </span>
          </div>
          <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
            <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
              RMSR
            </span>
            <span className="mt-1 block text-xl font-bold tabular-nums text-[#a7d12b]">
              {pfa.rmsr.toFixed(3)}
            </span>
          </div>
          <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
            <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
              CAF
            </span>
            <span className="mt-1 block text-xl font-bold tabular-nums text-[#a7d12b]">
              {pfa.caf.toFixed(3)}
            </span>
          </div>
        </div>

        {/* Factor labels + congruence */}
        {pfa.factor_labels.length > 0 && (
          <div className="mb-5">
            <h4 className="text-sm font-semibold text-slate-50 mb-2">Factor labels (DAAL)</h4>
            <div className="flex flex-wrap gap-2">
              {pfa.factor_labels.map((label, idx) => (
                <Badge key={idx} variant="outline" className="border-[#a7d12b]/30 text-[#a7d12b]">
                  F{idx + 1}: {label}
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

        {/* Detailed loadings table (collapsible — diagram is the primary view) */}
        {pfa.loadings.length > 0 && (
          <details className="mb-5 rounded-lg border border-border/40 bg-slate-900/30 px-3 py-2">
            <summary className="cursor-pointer text-sm font-semibold text-slate-50">
              Loading matrix (numeric)
            </summary>
            <div className="mt-3 overflow-x-auto">
              <table className="text-xs w-full">
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
                        <td key={fi} className="px-2 py-1.5 text-center tabular-nums">
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
          </details>
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
