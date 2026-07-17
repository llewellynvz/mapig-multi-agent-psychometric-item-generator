"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type MethodBadgeVariant = "semantic" | "predata" | "llm" | "synthetic";

export interface MethodBadgeProps {
  variant: MethodBadgeVariant;
  className?: string;
}

const VARIANT_CONFIG: Record<
  MethodBadgeVariant,
  { label: string; title: string; className: string }
> = {
  semantic: {
    label: "SEMANTIC SIMILARITY",
    title:
      "Computed from sentence-embedding cosine similarity between item texts — a language-based estimate, not respondent data.",
    className: "border-[#4db8c9]/40 bg-[#4db8c9]/10 text-[#4db8c9]",
  },
  predata: {
    label: "PRE-DATA ESTIMATE",
    title:
      "Estimated before any human responses exist. Treat as a triage signal, not evidence of psychometric properties.",
    className: "border-[#a7d12b]/40 bg-[#a7d12b]/10 text-[#a7d12b]",
  },
  llm: {
    label: "LLM-JUDGED",
    title:
      "A language model's structured judgment — theoretical estimate, not a computed statistic.",
    className: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  },
  synthetic: {
    label: "SYNTHETIC PILOT",
    title: "Computed from simulated LLM respondents, not human data.",
    className: "border-slate-400/40 bg-slate-400/10 text-slate-300",
  },
};

export function MethodBadge({ variant, className }: MethodBadgeProps) {
  const config = VARIANT_CONFIG[variant];
  return (
    <span
      title={config.title}
      className={cn(
        "inline-flex shrink-0 items-center whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}
