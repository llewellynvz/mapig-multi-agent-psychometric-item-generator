"use client";

import * as React from "react";
import { Pill } from "@/components/ui/pill";

export interface PlagiarismBadgeProps {
  warning: string;
}

/**
 * Warning pill for items flagged by plagiarism detection.
 * Displays informational warning message - no auto-removal or revision suggestions.
 */
export function PlagiarismBadge({ warning }: PlagiarismBadgeProps) {
  return (
    <Pill className="bg-red-500/20 text-red-400 border-red-500/40 text-xs">
      {warning}
    </Pill>
  );
}
