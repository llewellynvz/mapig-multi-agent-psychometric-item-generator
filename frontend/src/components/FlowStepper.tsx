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
    <section className="animate-fade-up rounded-3xl border border-border/60 bg-gradient-to-br from-[#0B2A34] via-[#0F3743] to-[#1A4A53] p-4 text-white shadow-sm backdrop-blur md:p-6">
      <div className="grid gap-3 md:grid-cols-3">
        {STEPS.map((step, index) => {
          const Icon = ICONS[step.id];
          const status =
            index < currentIndex ? "done" : index === currentIndex ? "active" : "pending";

          return (
            <article
              key={step.id}
              className={cn(
                "bubble-panel rounded-2xl p-4 transition-all duration-300 hover:-translate-y-0.5",
                status === "active" && "border-accent bg-white/15 shadow-md",
                status === "pending" && "bg-white/10"
              )}
              style={{ animationDelay: `${index * 70}ms` }}
            >
              <div className="mb-2 flex items-center gap-2">
                <span
                  className={cn(
                    "inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold",
                    status === "pending" && "bg-white/15 text-slate-100",
                    status === "active" && "bg-accent text-white",
                    status === "done" && "bg-accent/80 text-white"
                  )}
                >
                  {index + 1}
                </span>
                <Icon className={cn("h-4 w-4 text-white", status === "active" ? "animate-spin" : "")} />
                <p className="text-sm font-semibold text-white md:text-base">{step.label}</p>
              </div>
              <p className="text-xs text-slate-100/80 md:text-sm">{step.description}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
