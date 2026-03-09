"use client";

import { Pill } from "@/components/ui/pill";

const STEPS = [
  "retrieval",
  "item_writer",
  "content_review",
  "linguistic_review",
  "bias_review",
  "meta_editor",
  "critic",
  "finalize",
] as const;

export interface RunTimelineProps {
  iterationCount: number;
}

export function RunTimeline({ iterationCount }: RunTimelineProps) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-muted-foreground">Run timeline</p>
      <div className="flex flex-wrap items-center gap-2">
        {STEPS.map((step, i) => (
          <span key={step} className="flex items-center gap-2">
            <Pill className="rounded-lg text-xs font-medium">
              {step.replace(/_/g, " ")}
            </Pill>
            {i < STEPS.length - 1 && (
              <span className="text-slate-200/80" aria-hidden>
                →
              </span>
            )}
          </span>
        ))}
        {iterationCount > 0 && (
          <Pill className="border-accent/60 bg-accent/30 text-xs font-medium">
            Looped × {1 + iterationCount}
          </Pill>
        )}
      </div>
    </div>
  );
}
