"use client";

import * as React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { InstrumentCard } from "./InstrumentCard";
import { MethodologyNote } from "./MethodologyNote";
import type { ComparisonInstrument, CrossConstructComparison } from "@/lib/types";

export interface ComparisonPanelProps {
  convergentInstrument: ComparisonInstrument;
  discriminantInstrument: ComparisonInstrument;
  convergentScore: number;
  crossConstruct?: CrossConstructComparison;
  defaultExpanded?: boolean;
}

export function ComparisonPanel({
  convergentInstrument,
  discriminantInstrument,
  convergentScore,
  crossConstruct,
  defaultExpanded = false
}: ComparisonPanelProps) {
  const [isExpanded, setIsExpanded] = React.useState(defaultExpanded);

  const discriminantCorrelation = crossConstruct?.construct_pairs?.[0]?.estimated_correlation;
  const showDiscriminantWarning = discriminantCorrelation !== undefined && discriminantCorrelation > 0.85;
  const discriminantWarningText = showDiscriminantWarning
    ? discriminantInstrument.validity_method === "embedding"
      ? `High overlap detected (similarity = ${discriminantCorrelation.toFixed(2)})`
      : `High overlap detected (LLM-estimated r = ${discriminantCorrelation.toFixed(2)})`
    : undefined;

  return (
    <SurfaceCard className="border-lime-300/70">
      <CardHeader
        className="cursor-pointer border-b border-border/60 hover:bg-surface-2/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base md:text-lg">
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
          <p className="text-sm text-muted-foreground mb-5">
            Convergent validity: items measure the same construct. Discriminant validity: items distinguish from related constructs.
          </p>

          {/* Stacked vertically */}
          <div className="space-y-4">
            <InstrumentCard
              instrument={convergentInstrument}
              label="Convergent Validity"
              score={convergentScore}
              scoreLabel="Convergent alignment (pre-data)"
            />

            <InstrumentCard
              instrument={discriminantInstrument}
              label="Discriminant Validity"
              score={discriminantCorrelation}
              scoreLabel="LLM-estimated r"
              showWarning={showDiscriminantWarning}
              warningText={discriminantWarningText}
            />
          </div>

          <MethodologyNote>
            Only instrument metadata is stored. No copyrighted item text is retrieved or displayed.
          </MethodologyNote>
        </CardContent>
      )}
    </SurfaceCard>
  );
}
