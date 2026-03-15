"use client";

import { ArrowLeft, Sliders } from "lucide-react";
import { PrimaryButton } from "@/components/ui/action-buttons";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";
import { InsetPanel, SurfaceCard } from "@/components/ui/surface-card";
import type { InstrumentSetupFormValues } from "@/lib/schemas";

export interface SetupSnapshotCardProps {
  values: InstrumentSetupFormValues | null;
  horizontal?: boolean;
  onEditSetup?: () => void;
}

export function SetupSnapshotCard({ values, horizontal = false, onEditSetup }: SetupSnapshotCardProps) {
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

  if (horizontal) {
    return (
      <SurfaceCard className="border-lime-300/70">
        <CardHeader className="border-b border-border/60 py-2.5 px-4">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base md:text-lg">
              <Sliders className="h-5 w-5 text-white" />
              Instrument Setup
            </CardTitle>
            {onEditSetup && (
              <PrimaryButton type="button" size="sm" onClick={onEditSetup}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Edit Setup
              </PrimaryButton>
            )}
          </div>
        </CardHeader>
        <CardContent className="py-3 px-4">
          <div className="grid gap-x-4 gap-y-2 sm:grid-cols-3 lg:grid-cols-6 text-sm">
            <InsetPanel className="rounded-lg px-2.5 py-1.5 lg:col-span-2">
              <p className="text-[10px] font-medium uppercase tracking-wide text-accent">Construct</p>
              <p className="mt-0.5 font-semibold text-slate-50">{values.construct_name}</p>
            </InsetPanel>
            <InsetPanel className="rounded-lg px-2.5 py-1.5 lg:col-span-2">
              <p className="text-[10px] font-medium uppercase tracking-wide text-accent">Population</p>
              <p className="mt-0.5 text-muted-foreground">{values.target_population}</p>
            </InsetPanel>
            <InsetPanel className="rounded-lg px-2.5 py-1.5">
              <p className="text-[10px] font-medium uppercase tracking-wide text-accent">Scale</p>
              <p className="mt-0.5 text-muted-foreground">{values.response_scale}</p>
            </InsetPanel>
            <InsetPanel className="rounded-lg px-2.5 py-1.5">
              <p className="text-[10px] font-medium uppercase tracking-wide text-accent">Items</p>
              <p className="mt-0.5 text-muted-foreground">{values.item_count}</p>
            </InsetPanel>
            <InsetPanel className="rounded-lg px-2.5 py-1.5">
              <p className="text-[10px] font-medium uppercase tracking-wide text-accent">Language</p>
              <p className="mt-0.5 text-muted-foreground">{values.language || "English"}</p>
            </InsetPanel>
            {values.cultural_group?.trim() && (
              <InsetPanel className="rounded-lg px-2.5 py-1.5">
                <p className="text-[10px] font-medium uppercase tracking-wide text-accent">Cultural Group</p>
                <p className="mt-0.5 text-muted-foreground">{values.cultural_group}</p>
              </InsetPanel>
            )}
            {values.construct_exclusions?.trim() && (
              <InsetPanel className="rounded-lg px-2.5 py-1.5 sm:col-span-2">
                <p className="text-[10px] font-medium uppercase tracking-wide text-accent">Exclusions</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{values.construct_exclusions}</p>
              </InsetPanel>
            )}
          </div>
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

          {values.language && values.language !== "English" && (
            <InsetPanel className="rounded-xl p-3">
              <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Language</p>
              <p className="mt-1 text-sm">{values.language}</p>
            </InsetPanel>
          )}

          {values.cultural_group?.trim() && (
            <InsetPanel className="rounded-xl p-3">
              <p className="text-[11px] font-medium uppercase tracking-wide text-accent">Cultural Group</p>
              <p className="mt-1 text-sm">{values.cultural_group}</p>
            </InsetPanel>
          )}

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
