"use client";

import { useMemo } from "react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { MethodBadge } from "./MethodBadge";
import { MethodologyNote } from "./MethodologyNote";
import type { PFAResult, FactorLoading, EGAResult } from "@/lib/types";

export interface PFAPanelProps {
  pfa: PFAResult;
  egaSemantic?: EGAResult;
  egaSynthetic?: EGAResult;
  itemTexts?: string[];
}

const COMMUNITY_COLORS = [
  "#a7d12b",
  "#4db8c9",
  "#e0a83c",
  "#c96fb0",
  "#8a91f0",
  "#6fc98f",
];

function EGANetworkView({ ega, itemTexts }: { ega: EGAResult; itemTexts?: string[] }) {
  return (
    <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-slate-50">
          {ega.method === "semantic_threshold" ? "Semantic network" : "Synthetic-pilot network"}
        </span>
        <MethodBadge
          variant={ega.method === "semantic_threshold" ? "semantic" : "synthetic"}
          className="px-1.5 text-[8px]"
        />
        <span className="text-[10px] text-muted-foreground/70">
          {ega.n_dimensions} communit{ega.n_dimensions === 1 ? "y" : "ies"}
        </span>
      </div>
      <svg viewBox="0 0 100 100" className="w-full max-w-[280px] mx-auto" role="img" aria-label="Item network diagram">
        {ega.edges.map((edge, i) => {
          const a = ega.nodes.find((n) => n.item_index === edge.source);
          const b = ega.nodes.find((n) => n.item_index === edge.target);
          if (!a || !b) return null;
          return (
            <line
              key={i}
              x1={a.x * 88 + 6}
              y1={a.y * 88 + 6}
              x2={b.x * 88 + 6}
              y2={b.y * 88 + 6}
              stroke="#64748b"
              strokeWidth={Math.max(0.3, Math.min(1.5, Math.abs(edge.weight) * 2))}
              opacity={0.5}
            />
          );
        })}
        {ega.nodes.map((node) => (
          <g key={node.item_index}>
            <circle
              cx={node.x * 88 + 6}
              cy={node.y * 88 + 6}
              r={3.2}
              fill={COMMUNITY_COLORS[node.community % COMMUNITY_COLORS.length]}
            >
              <title>
                {itemTexts?.[node.item_index] ?? `Item ${node.item_index + 1}`}
              </title>
            </circle>
            <text
              x={node.x * 88 + 6}
              y={node.y * 88 + 6.9}
              textAnchor="middle"
              fontSize="2.6"
              fill="#0f172a"
              fontWeight="bold"
            >
              {node.item_index + 1}
            </text>
          </g>
        ))}
      </svg>
      <p className="text-[10px] text-muted-foreground/60 mt-2">{ega.disclaimer}</p>
    </div>
  );
}

function verdictBadge(v: string): { color: string; icon: React.ReactNode; label: string } {
  if (v === "not_estimable") {
    return {
      color: "bg-slate-500/15 text-slate-300 border-slate-500/30",
      icon: <AlertTriangle className="h-3.5 w-3.5" />,
      label: "Not estimable",
    };
  }
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
    const factorBoxW = 200;
    const factorBoxH = 70;
    const itemBoxW = 340;
    const itemBoxH = 42;
    const itemGap = 20;
    const factorGap = 100;
    const colGap = 280; // space for the loading arrows (factor → item)
    const residualGap = 60; // space for residual circles to the right of items
    const residualR = 22;
    const padX = 30;
    const padY = 36;

    const factorColX = padX;
    const itemColX = padX + factorBoxW + colGap;
    const residualColX = itemColX + itemBoxW + residualGap;

    const totalH = Math.max(
      padY * 2 + factors.length * (factorBoxH + factorGap) - factorGap,
      padY * 2 + items.length * (itemBoxH + itemGap) - itemGap,
    );
    const totalW = residualColX + residualR * 2 + padX;

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
      residualR,
      factorColX,
      itemColX,
      residualColX,
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
        style={{ minWidth: 720, maxWidth: layout.totalW, height: "auto" }}
        role="img"
        aria-label="Pseudo-EFA loading diagram with latent factor, item indicators, and residual variances"
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
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#a7d12b" opacity="0.85" />
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
          <marker
            id="arrow-residual"
            viewBox="0 0 10 10"
            refX="2"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" opacity="0.7" />
          </marker>
        </defs>

        {/* === LOADING ARROWS (η → x_i, labeled with λ) === */}
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
              ? Math.min(1.2 + abs * 3, 4.2)
              : Math.min(0.5 + abs * 1.5, 2);
            const opacity = isPrimary ? 0.9 : 0.5;
            const marker = isPrimary ? "url(#arrow)" : "url(#arrow-weak)";

            // Place loading label at ~35% from factor (avoid clutter at item end)
            const midX = x1 + (x2 - x1) * 0.42;
            const midY = factorY + (itemY - factorY) * 0.42;

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
                  <g>
                    {/* λ label with stroke halo for legibility */}
                    <text
                      x={midX}
                      y={midY - 6}
                      fill="#a7d12b"
                      fontSize="12"
                      fontWeight="700"
                      textAnchor="middle"
                      style={{ paintOrder: "stroke", stroke: "#0f172a", strokeWidth: 4 }}
                    >
                      λ = {load.toFixed(2)}
                    </text>
                  </g>
                )}
              </g>
            );
          });
        })}

        {/* === RESIDUAL ARROWS (ε_i → x_i, drawn going right-to-left into item) === */}
        {layout.items.map((fl, itemIdx) => {
          const itemY = layout.itemYs[itemIdx] + layout.itemBoxH / 2;
          const itemRightX = layout.itemColX + layout.itemBoxW;
          const residualCx = layout.residualColX + layout.residualR;
          const residualCy = itemY;
          // Uniqueness = 1 - λ^2 (assumes standardized solution)
          const primaryLoad = fl.primary_loading;
          const uniqueness = Math.max(0, 1 - primaryLoad * primaryLoad);
          return (
            <g key={`residual-${itemIdx}`}>
              {/* Arrow from residual circle back to item */}
              <line
                x1={residualCx - layout.residualR}
                y1={residualCy}
                x2={itemRightX}
                y2={residualCy}
                stroke="#94a3b8"
                strokeWidth="1.2"
                opacity="0.7"
                markerEnd="url(#arrow-residual)"
              />
              {/* Residual circle */}
              <circle
                cx={residualCx}
                cy={residualCy}
                r={layout.residualR}
                fill="rgba(148, 163, 184, 0.08)"
                stroke="#94a3b8"
                strokeWidth="1.2"
              />
              {/* ε_n notation */}
              <text
                x={residualCx}
                y={residualCy + 4}
                textAnchor="middle"
                fill="#cbd5e1"
                fontSize="13"
                fontStyle="italic"
                fontWeight="600"
              >
                ε{fl.item_index + 1}
              </text>
              {/* Uniqueness label below */}
              <text
                x={residualCx}
                y={residualCy + layout.residualR + 12}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize="9"
              >
                {uniqueness.toFixed(2)}
              </text>
            </g>
          );
        })}

        {/* === LATENT FACTOR ELLIPSES (η) === */}
        {layout.factors.map((label, fi) => {
          const cx = layout.factorColX + layout.factorBoxW / 2;
          const cy = layout.factorYs[fi] + layout.factorBoxH / 2;
          const rx = layout.factorBoxW / 2 - 4;
          const ry = layout.factorBoxH / 2 - 4;
          const cong = pfa.tuckers_congruence[fi];
          // Truncate long labels for fit
          const displayLabel = label.length > 22 ? label.slice(0, 22) + "…" : label;
          return (
            <g key={`factor-${fi}`}>
              <ellipse
                cx={cx}
                cy={cy}
                rx={rx}
                ry={ry}
                fill="rgba(167, 209, 43, 0.12)"
                stroke="#a7d12b"
                strokeWidth="2"
              />
              {/* η_n notation top-left of ellipse */}
              <text
                x={cx - rx + 12}
                y={cy - ry + 16}
                fill="#a7d12b"
                fontSize="14"
                fontStyle="italic"
                fontWeight="700"
              >
                η{layout.factors.length > 1 ? fi + 1 : ""}
              </text>
              {/* Factor label centered */}
              <text
                x={cx}
                y={cy - 2}
                textAnchor="middle"
                fill="#a7d12b"
                fontSize="13"
                fontWeight="600"
              >
                {displayLabel}
              </text>
              {cong !== undefined && (
                <text
                  x={cx}
                  y={cy + 14}
                  textAnchor="middle"
                  fill="#94a3b8"
                  fontSize="10"
                >
                  c = {Math.abs(cong).toFixed(2)}
                </text>
              )}
            </g>
          );
        })}

        {/* === ITEM RECTANGLES (manifest indicators x_i) === */}
        {layout.items.map((fl, itemIdx) => {
          const x = layout.itemColX;
          const y = layout.itemYs[itemIdx];
          const isWell = fl.is_well_loaded;
          const trimmed = fl.item_text.length > 46 ? fl.item_text.slice(0, 46) + "…" : fl.item_text;
          return (
            <g key={`item-${itemIdx}`}>
              <rect
                x={x}
                y={y}
                width={layout.itemBoxW}
                height={layout.itemBoxH}
                rx="4"
                ry="4"
                fill="rgba(15, 23, 42, 0.85)"
                stroke={isWell ? "#a7d12b" : "#f59e0b"}
                strokeWidth="1.6"
              />
              {/* x_n notation top-left */}
              <text
                x={x + 8}
                y={y + 14}
                fill={isWell ? "#a7d12b" : "#f59e0b"}
                fontSize="11"
                fontStyle="italic"
                fontWeight="700"
              >
                x{fl.item_index + 1}
              </text>
              {/* Item text */}
              <text
                x={x + 36}
                y={y + 14}
                fill="#cbd5e1"
                fontSize="10"
                fontWeight="600"
              >
                Item {fl.item_index + 1}
              </text>
              <text
                x={x + 8}
                y={y + 32}
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
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-5 h-3 rounded-full border-2 border-[#a7d12b] bg-[#a7d12b]/10"></span>
          <em>η</em> latent factor
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded border border-[#a7d12b] bg-slate-950/85"></span>
          <em>x<sub>i</sub></em> item indicator
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-full border border-slate-400 bg-slate-400/10"></span>
          <em>ε<sub>i</sub></em> residual (uniqueness = 1 − λ²)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-4 h-0.5 bg-[#a7d12b]"></span>
          λ ≥ 0.30 (primary loading)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 bg-slate-500"></span>
          cross-loading
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full border-2 border-[#a7d12b]"></span>
          retained
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full border-2 border-amber-500"></span>
          retention flag
        </span>
      </div>
    </div>
  );
}


/** Measurement equations as a textual companion to the path diagram.
 * Renders one equation per item: x_i = λ_i · η + ε_i with concrete values. */
function MeasurementEquations({ pfa }: { pfa: PFAResult }) {
  if (pfa.loadings.length === 0) return null;
  return (
    <div className="mt-4 rounded-lg border border-border/40 bg-slate-950/40 p-3">
      <h4 className="text-xs font-semibold text-slate-50 mb-2 uppercase tracking-wide">
        Measurement equations
      </h4>
      <div className="space-y-1 font-mono text-[11px] leading-relaxed">
        {pfa.loadings.map((fl) => {
          const lambda = fl.primary_loading;
          const uniqueness = Math.max(0, 1 - lambda * lambda);
          const factorLabel =
            pfa.factor_labels.length > 1
              ? `η${fl.primary_factor + 1}`
              : "η";
          return (
            <div key={fl.item_index} className="text-slate-200">
              <span className="text-[#a7d12b]">x{fl.item_index + 1}</span>
              <span className="text-muted-foreground"> = </span>
              <span className="text-[#a7d12b]">{lambda.toFixed(3)}</span>
              <span className="text-muted-foreground"> · </span>
              <span className="text-[#a7d12b]">{factorLabel}</span>
              <span className="text-muted-foreground"> + </span>
              <span className="text-slate-400 italic">ε{fl.item_index + 1}</span>
              <span className="text-muted-foreground"> </span>
              <span className="text-muted-foreground/60 text-[10px]">
                (Var(ε) ≈ {uniqueness.toFixed(3)})
              </span>
            </div>
          );
        })}
      </div>
      <p className="mt-2 text-[10px] italic text-muted-foreground/70">
        Standardized solution: each item is the latent factor weighted by its
        loading λ, plus a residual ε with variance 1 − λ². Loadings ≥ 0.30 are
        meaningful indicators; uniqueness {">"} 0.70 means the item is mostly
        unique noise relative to the factor.
      </p>
    </div>
  );
}

export function PFAPanel({ pfa, egaSemantic, egaSynthetic, itemTexts }: PFAPanelProps) {
  const verdict = verdictBadge(pfa.fit_verdict);
  const meanCongruence =
    pfa.tuckers_congruence.length > 0
      ? pfa.tuckers_congruence.reduce((a, b) => a + b, 0) / pfa.tuckers_congruence.length
      : 0;

  return (
    <SurfaceCard className="mt-4 border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base md:text-lg">
            Pseudo-Factor Analysis (Pre-Calibration)
            <MethodBadge variant="predata" />
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

        {/* SEM/CFA-style path diagram (centerpiece) */}
        {pfa.loadings.length > 0 && (
          <div className="mb-6 rounded-lg border border-border/40 bg-slate-950/60 p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-slate-50">
                Pseudo-EFA loading diagram (semantic)
              </h4>
              <span className="text-[10px] uppercase text-muted-foreground/70 tracking-wide">
                pre-calibration estimate
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground/80 mb-3 leading-relaxed">
              Latent factor (<em>η</em>) → item indicators (<em>x<sub>i</sub></em>)
              ← residuals (<em>ε<sub>i</sub></em>). Standardized loadings (λ)
              shown on each path. Tucker&apos;s congruence (c) inside each ellipse.
            </p>
            <PathDiagram pfa={pfa} />
            <MeasurementEquations pfa={pfa} />
          </div>
        )}

        {/* Summary statistics */}
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5 mb-5">
          <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
            <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
              Mean facet-target congruence
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
              {pfa.factor_recovery_rate != null
                ? `${(pfa.factor_recovery_rate * 100).toFixed(0)}%`
                : <span className="text-sm font-medium text-muted-foreground">Not estimable</span>}
            </span>
          </div>
          <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
            <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
              RMSR
            </span>
            <span className="mt-1 block text-xl font-bold tabular-nums text-[#a7d12b]">
              {pfa.rmsr != null
                ? pfa.rmsr.toFixed(3)
                : <span className="text-sm font-medium text-muted-foreground">Not estimable</span>}
            </span>
          </div>
          <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
            <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
              CAF
            </span>
            <span className="mt-1 block text-xl font-bold tabular-nums text-[#a7d12b]">
              {pfa.caf != null
                ? pfa.caf.toFixed(3)
                : <span className="text-sm font-medium text-muted-foreground">Not estimable</span>}
            </span>
          </div>
          <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
            <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
              Pseudo-omega (loadings)
            </span>
            {pfa.pseudo_omega != null ? (
              <span className="mt-1 block text-xl font-bold tabular-nums text-[#a7d12b]">
                {pfa.pseudo_omega.toFixed(3)}
              </span>
            ) : (
              <span className="mt-1 block text-sm font-medium text-muted-foreground">
                — not estimable
              </span>
            )}
            <span className="mt-0.5 block text-[9px] text-muted-foreground/60">
              from PFA solution — pre-data
            </span>
          </div>
        </div>

        {pfa.solver && pfa.solver !== "factor_analyzer:oblimin" && (
          <p className="-mt-3 mb-5 text-[10px] italic text-muted-foreground/70">
            {pfa.solver === "pca_eigh_fallback"
              ? "Unrotated PCA fallback (factor analysis failed)"
              : pfa.solver === "oblimin_phi_missing"
                ? "Factor correlations unavailable — fit computed with Φ=I"
                : pfa.solver}
          </p>
        )}

        {/* Dimensionality signals: LLM facet count vs data-driven Kaiser rule */}
        <div className="mb-5 rounded-lg border border-border/40 bg-slate-900/30 px-3 py-2 text-[11px] text-muted-foreground">
          <span className="font-semibold text-slate-50">Dimensionality signals: </span>
          Facet mapping k = {pfa.n_factors}
          {pfa.n_factors_suggested_kaiser != null && (
            <>
              {" · "}Eigenvalue rule (λ &gt; 1) suggests {pfa.n_factors_suggested_kaiser}
              {pfa.n_factors_suggested_kaiser !== pfa.n_factors && (
                <span className="text-amber-300/90">
                  {" "}— signals disagree; inspect the loading pattern before trusting either.
                </span>
              )}
            </>
          )}
          {pfa.kmo_semantic != null && (
            <>{" · "}Semantic KMO = {pfa.kmo_semantic.toFixed(2)} (factorability heuristic)</>
          )}
          {egaSemantic && (
            <>{" · "}Semantic EGA communities = {egaSemantic.n_dimensions}</>
          )}
          {egaSynthetic && (
            <>{" · "}Synthetic-pilot EGA dimensions = {egaSynthetic.n_dimensions}</>
          )}
        </div>

        {/* EGA network views + UVA redundancy (Phase 19) */}
        {(egaSemantic || egaSynthetic) && (
          <div className="mb-5">
            <h4 className="text-sm font-semibold text-slate-50 mb-2">
              Exploratory Graph Analysis
            </h4>
            <div className="grid gap-3 sm:grid-cols-2">
              {egaSemantic && <EGANetworkView ega={egaSemantic} itemTexts={itemTexts} />}
              {egaSynthetic && <EGANetworkView ega={egaSynthetic} itemTexts={itemTexts} />}
            </div>
            {egaSemantic && egaSemantic.redundant_pairs.length > 0 && (
              <div className="mt-3">
                <span className="text-xs font-semibold text-slate-50">
                  Redundant item pairs (UVA, wTO ≥ 0.25):
                </span>
                <ul className="mt-1 space-y-0.5">
                  {egaSemantic.redundant_pairs.slice(0, 8).map((pair, i) => (
                    <li key={i} className="text-[11px] text-amber-300/90">
                      Item {pair.item_i_index + 1} × Item {pair.item_j_index + 1}{" "}
                      (wTO = {pair.wto.toFixed(2)}) — consider keeping only one.
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

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
            <h4 className="text-sm font-semibold text-slate-50 mb-2">Eigenvalues (all {pfa.eigenvalues.length})</h4>
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

        <MethodologyNote embeddingModel={pfa.embedding_model}>
          {pfa.disclaimer}
        </MethodologyNote>
      </CardContent>
    </SurfaceCard>
  );
}
