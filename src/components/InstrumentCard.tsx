"use client";

import * as React from "react";
import { Pill } from "@/components/ui/pill";
import type { ComparisonInstrument } from "@/lib/types";

export interface InstrumentCardProps {
  instrument: ComparisonInstrument;
  label: string;
  score?: number;
  scoreLabel?: string;
  showWarning?: boolean;
  warningText?: string;
}

/**
 * Get status pill for validity score
 */
function getScoreStatus(score: number): { label: string; className: string } {
  if (score >= 0.70) {
    return { label: 'Pass', className: 'bg-green-500/20 text-green-400 border-green-500/40' };
  }
  if (score >= 0.50) {
    return { label: 'Acceptable', className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40' };
  }
  return { label: 'Warning', className: 'bg-amber-500/20 text-amber-400 border-amber-500/40' };
}

/**
 * Extract author and year from citation
 * Attempts to parse common formats like "Author (Year)" or "Author, Year"
 * Falls back to showing full citation if parsing fails
 */
function parseAuthorYear(citation: string): string {
  // Try pattern: "Author (Year)"
  const match1 = citation.match(/^([^(]+)\((\d{4})\)/);
  if (match1) {
    return `${match1[1].trim()}, ${match1[2]}`;
  }

  // Try pattern: "Author, Year"
  const match2 = citation.match(/^([^,]+),\s*(\d{4})/);
  if (match2) {
    return `${match2[1].trim()}, ${match2[2]}`;
  }

  // Try pattern: "Author et al. (Year)"
  const match3 = citation.match(/^([^(]+et al\.)\s*\((\d{4})\)/);
  if (match3) {
    return `${match3[1].trim()}, ${match3[2]}`;
  }

  // Fallback: show full citation
  return citation;
}

export function InstrumentCard({
  instrument,
  label,
  score,
  scoreLabel,
  showWarning = false,
  warningText
}: InstrumentCardProps) {
  const authorYear = parseAuthorYear(instrument.source_citation);
  const scoreStatus = score !== undefined ? getScoreStatus(score) : null;

  return (
    <div className="rounded-xl border border-border/60 bg-slate-900/30 p-4 space-y-3">
      {/* Label */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
        {score !== undefined && scoreStatus && (
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-foreground">
              {scoreLabel || 'Score'}: {score.toFixed(2)}
            </span>
            <Pill className={scoreStatus.className}>{scoreStatus.label}</Pill>
          </div>
        )}
      </div>

      {/* Instrument name */}
      <div>
        <h4 className="text-base font-bold text-foreground">{instrument.name}</h4>
        <p className="text-sm text-muted-foreground mt-1">{authorYear}</p>
      </div>

      {/* Construct */}
      <div>
        <p className="text-sm text-muted-foreground">
          <span className="font-medium">Construct:</span> {instrument.construct}
        </p>
      </div>

      {/* Similarity rationale */}
      {instrument.similarity_rationale && (
        <div>
          <p className="text-sm italic text-slate-300">
            {instrument.similarity_rationale}
          </p>
        </div>
      )}

      {/* Full APA citation */}
      <div>
        <p className="text-xs text-muted-foreground">
          {instrument.source_citation}
        </p>
      </div>

      {/* Warning badge */}
      {showWarning && warningText && (
        <div className="pt-2 border-t border-border/40">
          <Pill className="bg-amber-500/20 text-amber-400 border-amber-500/40">
            {warningText}
          </Pill>
        </div>
      )}
    </div>
  );
}
