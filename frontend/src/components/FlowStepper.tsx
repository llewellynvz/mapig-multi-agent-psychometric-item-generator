"use client";

import { ClipboardList, LoaderCircle, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

type StepId = "setup" | "run" | "results";

interface StepDef {
  id: StepId;
  label: string;
  description: string;
}

const STEPS: StepDef[] = [
  { id: "setup", label: "Instrument Setup", description: "Define the construct and constraints" },
  { id: "run", label: "Generation Run", description: "Agent workflow and quality checks" },
  { id: "results", label: "Results and Refinement", description: "Review output and provide feedback" },
];

const ICONS: Record<StepId, typeof ClipboardList> = {
  setup: ClipboardList,
  run: LoaderCircle,
  results: Sparkles,
};

function getStepIndex(step: StepId): number {
  return STEPS.findIndex((s) => s.id === step);
}

export interface FlowStepperProps {
  current: StepId;
}

export function FlowStepper({ current }: FlowStepperProps) {
  const currentIndex = getStepIndex(current);

  return (
    <section className="animate-fade-up rounded-3xl border border-border/80 bg-card/95 p-4 shadow-sm backdrop-blur md:p-6">
      <div className="grid gap-3 md:grid-cols-3">
        {STEPS.map((step, index) => {
          const Icon = ICONS[step.id];
          const status =
            index < currentIndex ? "done" : index === currentIndex ? "active" : "pending";

          return (
            <article
              key={step.id}
              className={cn(
                "rounded-2xl border p-4 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-sm",
                status === "done" && "border-primary/40 bg-gradient-to-br from-primary/10 to-primary/5",
                status === "active" &&
                  "border-primary bg-gradient-to-br from-primary/20 via-primary/10 to-background shadow-md",
                status === "pending" && "border-border/80 bg-background/70"
              )}
              style={{ animationDelay: `${index * 70}ms` }}
            >
              <div className="mb-2 flex items-center gap-2">
                <span
                  className={cn(
                    "inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold",
                    status === "pending" && "bg-muted text-muted-foreground",
                    status === "active" && "bg-primary text-primary-foreground",
                    status === "done" && "bg-primary text-primary-foreground"
                  )}
                >
                  {index + 1}
                </span>
                <Icon className={cn("h-4 w-4", status === "active" ? "animate-spin" : "")} />
                <p className="text-sm font-semibold md:text-base">{step.label}</p>
              </div>
              <p className="text-xs text-muted-foreground md:text-sm">{step.description}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
