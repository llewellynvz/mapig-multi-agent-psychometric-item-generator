"use client";

import { useState } from "react";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronUp, MessageCircleQuestion } from "lucide-react";
import { MethodBadge } from "./MethodBadge";
import type { QualitativeQuestion } from "@/lib/types";

export interface QualitativeQuestionsPanelProps {
  questions: QualitativeQuestion[];
}

const PROBE_LABELS: Record<QualitativeQuestion["probe_type"], string> = {
  comprehension: "Comprehension",
  elaboration: "Elaboration",
  example: "Example",
  contrast: "Contrast",
  process: "Process",
};

export function QualitativeQuestionsPanel({ questions }: QualitativeQuestionsPanelProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <SurfaceCard className="border-lime-300/70">
      <CardHeader className="border-b border-border/60">
        <button
          type="button"
          onClick={() => setExpanded((s) => !s)}
          className="w-full flex items-center justify-between text-left"
        >
          <CardTitle className="text-base md:text-lg flex items-center gap-2">
            <MessageCircleQuestion className="h-4 w-4 text-[#a7d12b]" />
            Qualitative Interview Questions
            <MethodBadge variant="llm" />
          </CardTitle>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-[#a7d12b]/30 text-[#a7d12b]">
              {questions.length} question{questions.length === 1 ? "" : "s"}
            </Badge>
            {expanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </button>
      </CardHeader>
      {expanded && (
        <CardContent className="pt-5">
          <p className="text-xs text-muted-foreground/80 mb-4">
            Open-ended probes for construct pre-testing interviews and focus
            groups, grounded in the facet mapping and evidence. Use them to
            explore how the target population understands the construct before
            fielding the quantitative items.
          </p>
          <ol className="space-y-3">
            {questions.map((question, index) => (
              <li
                key={index}
                className="rounded-lg border border-border/40 bg-slate-900/30 p-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm text-slate-50">
                    {index + 1}. {question.question_text}
                  </p>
                  <Badge
                    variant="outline"
                    className="border-[#4db8c9]/30 text-[#4db8c9] shrink-0 text-[10px]"
                  >
                    {PROBE_LABELS[question.probe_type] ?? question.probe_type}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground/70 mt-1.5">
                  {question.facet} — {question.rationale}
                </p>
              </li>
            ))}
          </ol>
        </CardContent>
      )}
    </SurfaceCard>
  );
}
