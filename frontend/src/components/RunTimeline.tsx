"use client";

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
            <span className="rounded-lg bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
              {step.replace(/_/g, " ")}
            </span>
            {i < STEPS.length - 1 && (
              <span className="text-muted-foreground" aria-hidden>
                →
              </span>
            )}
          </span>
        ))}
        {iterationCount > 0 && (
          <span className="rounded-full bg-accent/20 px-2 py-0.5 text-xs font-medium text-accent-foreground">
            Looped × {1 + iterationCount}
          </span>
        )}
      </div>
    </div>
  );
}
