"use client";

import { useState } from "react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronUp, Users } from "lucide-react";
import type { PersonaValidationResponse } from "@/lib/types";

export interface PersonaValidationCardProps {
  validation: PersonaValidationResponse;
}

export function PersonaValidationCard({ validation }: PersonaValidationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const personaCount = validation.personas.length;
  const flaggedCount = validation.flagged_items.length;
  const totalItems = new Set(validation.ratings.map((r) => r.item_index)).size;

  // Compute mean rating per persona for the summary table
  const byPersona = new Map<string, number[]>();
  validation.ratings.forEach((r) => {
    const arr = byPersona.get(r.persona_label) ?? [];
    arr.push(r.rating);
    byPersona.set(r.persona_label, arr);
  });

  return (
    <SurfaceCard className="mt-4 border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <button
          type="button"
          onClick={() => setExpanded((s) => !s)}
          className="w-full flex items-center justify-between text-left"
        >
          <CardTitle className="text-base md:text-lg flex items-center gap-2">
            <Users className="h-4 w-4 text-[#a7d12b]" />
            Persona Validation
          </CardTitle>
          <div className="flex items-center gap-3">
            <Badge
              variant="outline"
              className={
                flaggedCount > 0
                  ? "border-amber-500/30 text-amber-300"
                  : "border-[#a7d12b]/30 text-[#a7d12b]"
              }
            >
              {flaggedCount}/{totalItems} flagged
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
          <p className="text-sm text-muted-foreground/90 mb-4">{validation.summary}</p>

          <div className="grid gap-2 sm:grid-cols-3 mb-4">
            <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
              <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
                Personas
              </span>
              <span className="text-xl font-bold text-[#a7d12b] tabular-nums">
                {personaCount}
              </span>
            </div>
            <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
              <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
                Items rated
              </span>
              <span className="text-xl font-bold text-[#a7d12b] tabular-nums">{totalItems}</span>
            </div>
            <div className="rounded-lg border border-border/40 bg-slate-900/30 p-3 text-center">
              <span className="text-[10px] uppercase font-medium text-muted-foreground/70 block">
                Interpretive variance
              </span>
              <span className="text-xl font-bold text-[#a7d12b] tabular-nums">
                {validation.interpretive_variance.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted-foreground/80">
                  <th className="text-left px-2 py-1">Persona</th>
                  <th className="text-right px-2 py-1">Mean rating</th>
                  <th className="text-right px-2 py-1">N items</th>
                </tr>
              </thead>
              <tbody>
                {Array.from(byPersona.entries()).map(([label, ratings]) => {
                  const mean = ratings.reduce((a, b) => a + b, 0) / ratings.length;
                  return (
                    <tr key={label} className="border-t border-border/30">
                      <td className="px-2 py-1.5 text-slate-100">{label}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums">{mean.toFixed(2)}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums">{ratings.length}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {flaggedCount > 0 && (
            <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
              <p className="text-[11px] text-amber-200">
                Items flagged for ambiguity (SD ≥ 2 across personas):{" "}
                {validation.flagged_items.map((i) => i + 1).join(", ")}.
              </p>
            </div>
          )}
        </CardContent>
      )}
    </SurfaceCard>
  );
}
