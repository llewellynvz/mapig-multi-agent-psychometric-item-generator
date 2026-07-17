"use client";

import { Check, ClipboardList, LoaderCircle, Sparkles } from "lucide-react";
import { InsetPanel } from "@/components/ui/surface-card";
import { cn } from "@/lib/utils";

export type StepId = "setup" | "run" | "results";

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

const STEP_COLORS: Record<
  StepId,
  {
    cardAccent: string;
    circleActive: string;
    circleDone: string;
  }
> = {
  setup: {
    cardAccent: "border-cyan-300/70 bg-cyan-400/10",
    circleActive: "border-lime-100 bg-accent text-slate-950 shadow-[0_0_0_4px_rgba(167,209,43,0.35)]",
    circleDone: "border-cyan-300/80 bg-cyan-400/35 text-white",
  },
  run: {
    cardAccent: "border-sky-300/70 bg-sky-400/10",
    circleActive: "border-lime-100 bg-accent text-slate-950 shadow-[0_0_0_4px_rgba(167,209,43,0.35)]",
    circleDone: "border-sky-300/80 bg-sky-400/35 text-white",
  },
  results: {
    cardAccent: "border-lime-300/70 bg-lime-300/10",
    circleActive: "border-lime-100 bg-accent text-slate-950 shadow-[0_0_0_4px_rgba(167,209,43,0.35)]",
    circleDone: "border-lime-300/80 bg-lime-300/35 text-white",
  },
};

const ICONS: Record<StepId, typeof ClipboardList> = {
  setup: ClipboardList,
  run: LoaderCircle,
  results: Sparkles,
};

function getStepIndex(step: StepId): number {
  return STEPS.findIndex((s) => s.id === step);
}

export interface StepperProps {
  current: StepId;
}

export function Stepper({ current }: StepperProps) {
  const currentIndex = getStepIndex(current);

  return (
    <section className="animate-fade-up surface-card p-4 md:p-6">
      <div className="grid gap-3 md:grid-cols-3">
        {STEPS.map((step, index) => {
          const Icon = ICONS[step.id];
          const status = index < currentIndex ? "done" : index === currentIndex ? "active" : "pending";
          const colors = STEP_COLORS[step.id];

          return (
            <InsetPanel
              key={step.id}
              aria-current={status === "active" ? "step" : undefined}
              className={cn(
                "overflow-visible p-4 transition-all duration-300",
                status === "active" && colors.cardAccent,
                status === "done" && "border-white/35 bg-white/5",
                status === "pending" && "border-white/20 bg-white/5"
              )}
              style={{ animationDelay: `${index * 70}ms` }}
            >
              <div className="mb-2 flex items-center gap-2">
                <span
                  aria-label={`Step ${index + 1}`}
                  className={cn(
                    "relative z-10 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold transition-all",
                    status === "pending" && "border-white/35 bg-white/10 text-slate-100",
                    status === "active" && colors.circleActive,
                    status === "done" && colors.circleDone
                  )}
                >
                  {status === "done" ? <Check className="h-3.5 w-3.5" aria-hidden /> : index + 1}
                </span>
                <Icon className={cn("h-4 w-4 text-white", status === "active" ? "animate-spin" : "")} />
                <p className="text-sm font-semibold text-white md:text-base">{step.label}</p>
              </div>
              <p className="text-xs text-slate-100/80 md:text-sm">{step.description}</p>
            </InsetPanel>
          );
        })}
      </div>
    </section>
  );
}

