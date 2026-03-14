"use client";

import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";
import { InsetPanel, SurfaceCard } from "@/components/ui/surface-card";
import type { InstrumentSetupFormValues } from "@/lib/schemas";

export interface SetupSnapshotCardProps {
  values: InstrumentSetupFormValues | null;
}

export function SetupSnapshotCard({ values }: SetupSnapshotCardProps) {
  if (!values) {
    return (
      <SurfaceCard className="border-lime-300/70">
        <CardHeader className="border-b border-border/60">
          <CardTitle className="text-base md:text-lg">Instrument Setup Snapshot</CardTitle>
        </CardHeader>
        <CardContent className="pt-5">
          <InsetPanel className="rounded-2xl p-4">
            <p className="text-sm text-muted-foreground">Run generation to see the submitted setup.</p>
          </InsetPanel>
        </CardContent>
      </SurfaceCard>
    );
  }

  return (
    <SurfaceCard className="border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-base md:text-lg">Instrument Setup Snapshot</CardTitle>
      </CardHeader>
      <CardContent className="pt-5">
        <div className="grid gap-3 sm:grid-cols-2">
          <InsetPanel className="col-span-full rounded-xl p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Construct</p>
            <p className="mt-1 text-sm font-semibold">{values.construct_name}</p>
          </InsetPanel>

          <InsetPanel className="col-span-full rounded-xl p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Definition</p>
            <p className="mt-1 text-sm leading-relaxed">{values.construct_definition}</p>
          </InsetPanel>

          <InsetPanel className="rounded-xl p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Population</p>
            <p className="mt-1 text-sm">{values.target_population}</p>
          </InsetPanel>

          <InsetPanel className="rounded-xl p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Response Scale</p>
            <p className="mt-1 text-sm">{values.response_scale}</p>
          </InsetPanel>

          <InsetPanel className="rounded-xl p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Item Count</p>
            <p className="mt-1 text-sm font-medium">{values.item_count}</p>
          </InsetPanel>

          <InsetPanel className="rounded-xl p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Constraints</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {values.constraints.length === 0 ? (
                <span className="text-sm text-muted-foreground">None</span>
              ) : (
                values.constraints.map((constraint, index) => (
                  <Pill key={`${constraint}-${index}`} className="font-normal text-xs">
                    {constraint}
                  </Pill>
                ))
              )}
            </div>
          </InsetPanel>

          {values.construct_exclusions?.trim() && (
            <InsetPanel className="col-span-full rounded-xl p-3">
              <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Boundary Exclusions</p>
              <p className="mt-1 text-sm leading-relaxed">{values.construct_exclusions}</p>
            </InsetPanel>
          )}
        </div>
      </CardContent>
    </SurfaceCard>
  );
}
