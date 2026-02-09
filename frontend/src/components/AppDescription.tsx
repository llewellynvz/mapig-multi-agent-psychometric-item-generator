"use client";

import Image from "next/image";
import { ArrowRight, BarChart3, CheckCircle2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface AppDescriptionProps {
  onPrimaryCta?: () => void;
  onSecondaryCta?: () => void;
}

export function AppDescription({ onPrimaryCta, onSecondaryCta }: AppDescriptionProps) {
  return (
    <section className="animate-fade-up relative overflow-hidden rounded-[2rem] border border-border/60 bg-gradient-to-br from-[#0B2A34] via-[#0F3743] to-[#1A4A53] p-6 text-white shadow-xl md:p-10">
      <div className="absolute -left-20 -top-20 h-56 w-56 rounded-full bg-cyan-300/10 blur-3xl" aria-hidden />
      <div className="absolute -bottom-20 right-0 h-64 w-64 rounded-full bg-lime-200/10 blur-3xl" aria-hidden />
      <div className="relative grid items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium">
            <Sparkles className="h-3.5 w-3.5" />
            MAPIG Workspace
          </div>
          <div className="space-y-4">
            <h1 className="max-w-2xl text-3xl font-semibold leading-tight tracking-tight md:text-5xl">
              Build auditable psychometric items with a startup-grade workflow.
            </h1>
            <p className="max-w-2xl text-sm leading-relaxed text-slate-100/90 md:text-base">
              Define construct boundaries, run the multi-agent pipeline, review evidence, and refine output with human
              feedback loops in a single guided interface.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="button"
              onClick={onPrimaryCta}
              className="h-11 rounded-xl bg-accent px-5 font-semibold text-muted-dark hover:bg-accent/90"
            >
              Start New Run
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onSecondaryCta}
              className="h-11 rounded-xl border-white/40 bg-white/10 px-5 text-white hover:bg-white/20"
            >
              Jump to Results
            </Button>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/15 bg-white/10 p-3 shadow-sm">
              <p className="text-2xl font-semibold">3</p>
              <p className="text-xs text-slate-100/80">Guided stages</p>
            </div>
            <div className="rounded-2xl border border-white/15 bg-white/10 p-3 shadow-sm">
              <p className="text-2xl font-semibold">100%</p>
              <p className="text-xs text-slate-100/80">Evidence traceable</p>
            </div>
            <div className="rounded-2xl border border-white/15 bg-white/10 p-3 shadow-sm">
              <p className="text-2xl font-semibold">1-click</p>
              <p className="text-xs text-slate-100/80">Rerun refinement</p>
            </div>
          </div>
        </div>

        <div className="space-y-3 rounded-3xl border border-white/15 bg-white/10 p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold">Pipeline Preview</p>
            <BarChart3 className="h-4 w-4 text-accent-light" />
          </div>
          <div className="overflow-hidden rounded-2xl border border-white/15 bg-white">
            <Image
              src="/mapig_arc.png"
              alt="MAPIG architecture"
              width={1000}
              height={620}
              className="h-auto w-full object-cover"
              priority
            />
          </div>
          <ul className="space-y-1 text-xs text-slate-100/90">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-accent" />
              Setup, run, and review without context switching.
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-accent" />
              Resume sessions using thread IDs and status recovery.
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-accent" />
              Keep human feedback history per refinement round.
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
