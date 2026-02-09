"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { InstrumentSetupFormValues } from "@/lib/schemas";

export interface SetupSnapshotCardProps {
  values: InstrumentSetupFormValues | null;
}

export function SetupSnapshotCard({ values }: SetupSnapshotCardProps) {
  if (!values) {
    return (
      <Card className="glass-panel shadow-sm">
        <CardHeader className="border-b border-border/60">
          <CardTitle className="text-base md:text-lg">Instrument Setup Snapshot</CardTitle>
        </CardHeader>
        <CardContent className="pt-5">
          <p className="text-sm text-muted-foreground">Run generation to see the submitted setup.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-panel shadow-sm">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-base md:text-lg">Instrument Setup Snapshot</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 pt-5">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Construct</p>
          <p className="text-sm font-semibold">{values.construct_name}</p>
        </div>
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Definition</p>
          <p className="text-sm leading-relaxed">{values.construct_definition}</p>
        </div>
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Population</p>
          <p className="text-sm">{values.target_population}</p>
        </div>
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Response Scale</p>
          <p className="text-sm">{values.response_scale}</p>
        </div>
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Constraints</p>
          <div className="flex flex-wrap gap-2">
            {values.constraints.length === 0 ? (
              <span className="text-sm text-muted-foreground">None</span>
            ) : (
              values.constraints.map((constraint, index) => (
                <Badge key={`${constraint}-${index}`} variant="secondary" className="bg-white/15 font-normal text-slate-100">
                  {constraint}
                </Badge>
              ))
            )}
          </div>
        </div>
        {values.construct_exclusions?.trim() && (
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Boundary Exclusions</p>
            <p className="text-sm leading-relaxed">{values.construct_exclusions}</p>
          </div>
        )}
        <p className="text-xs text-muted-foreground">
          Requested item count: <span className="font-medium text-white">{values.item_count}</span>
        </p>
      </CardContent>
    </Card>
  );
}
