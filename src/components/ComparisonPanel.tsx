"use client";

import * as React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { InstrumentCard } from "./InstrumentCard";
import type { ComparisonInstrument, CrossConstructComparison } from "@/lib/types";

export interface ComparisonPanelProps {
  convergentInstrument: ComparisonInstrument;
  discriminantInstrument: ComparisonInstrument;
  convergentScore: number;
  crossConstruct?: CrossConstructComparison;
}

export function ComparisonPanel({
  convergentInstrument,
  discriminantInstrument,
  convergentScore,
  crossConstruct
}: ComparisonPanelProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // Check if discriminant correlation is high (> 0.85)
  const discriminantCorrelation = crossConstruct?.construct_pairs?.[0]?.estimated_correlation;
  const showDiscriminantWarning = discriminantCorrelation !== undefined && discriminantCorrelation > 0.85;
  const discriminantWarningText = showDiscriminantWarning
    ? `High overlap detected (r = ${discriminantCorrelation.toFixed(2)})`
    : undefined;

  return (
    <SurfaceCard className="mt-4">
      <CardHeader
        className="cursor-pointer border-b border-border/60"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            Instrument Comparison
          </CardTitle>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-5">
          {/* Educational one-liner */}
          <p className="text-sm text-muted-foreground mb-4">
            Convergent validity: Items measure the same construct. Discriminant validity: Items distinguish from related constructs.
          </p>

          {/* Two-column grid */}
          <div className="grid gap-4 md:grid-cols-2">
            {/* Convergent instrument */}
            <InstrumentCard
              instrument={convergentInstrument}
              label="Convergent Validity"
              score={convergentScore}
              scoreLabel="Convergent Score"
            />

            {/* Discriminant instrument */}
            <InstrumentCard
              instrument={discriminantInstrument}
              label="Discriminant Validity"
              showWarning={showDiscriminantWarning}
              warningText={discriminantWarningText}
            />
          </div>

          {/* Copyright disclaimer footer */}
          <div className="mt-4 pt-4 border-t border-border/40">
            <p className="text-xs italic text-muted-foreground">
              Only instrument metadata is stored. No copyrighted item text is retrieved or displayed.
            </p>
          </div>
        </CardContent>
      )}
    </SurfaceCard>
  );
}
