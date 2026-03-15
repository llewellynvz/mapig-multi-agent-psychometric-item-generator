"use client";

import * as React from "react";
import { AlertTriangle } from "lucide-react";
import type { ComparisonInstrument } from "@/lib/types";

export interface InstrumentCardProps {
  instrument: ComparisonInstrument;
  label: string;
  score?: number;
  scoreLabel?: string;
  showWarning?: boolean;
  warningText?: string;
}

function getScoreColor(score: number): string {
  if (score >= 0.70) return "text-[#a7d12b]";
  if (score >= 0.50) return "text-[#a7d12b]/70";
  return "text-[#a7d12b]/50";
}

function getScoreTopStripeColor(score: number): string {
  if (score >= 0.70) return "border-t-[#a7d12b]/60";
  if (score >= 0.50) return "border-t-[#a7d12b]/40";
  return "border-t-[#a7d12b]/30";
}

function getScoreLabel(score: number): string {
  if (score >= 0.70) return "Strong";
  if (score >= 0.50) return "Moderate";
  return "Weak";
}

/**
 * Extract author and year from citation
 */
function parseAuthorYear(citation: string): string {
  const match1 = citation.match(/^([^(]+)\((\d{4})\)/);
  if (match1) return `${match1[1].trim()}, ${match1[2]}`;

  const match2 = citation.match(/^([^,]+),\s*(\d{4})/);
  if (match2) return `${match2[1].trim()}, ${match2[2]}`;

  const match3 = citation.match(/^([^(]+et al\.)\s*\((\d{4})\)/);
  if (match3) return `${match3[1].trim()}, ${match3[2]}`;

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
  const hasScore = score !== undefined;

  return (
    <div
      className={`rounded-xl border border-border/50 bg-slate-900/40 p-5 ${
        hasScore ? `border-t-2 ${getScoreTopStripeColor(score)}` : ""
      }`}
    >
      {/* Header: label */}
      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </span>

      {/* Instrument info */}
      <div className="mt-3 space-y-2">
        <div>
          <h4 className="text-base font-semibold text-slate-50 leading-tight">
            {instrument.name}
          </h4>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-sm text-muted-foreground">{authorYear}</span>
            {hasScore && (
              <div className="mt-2 rounded-lg border border-border/40 bg-slate-900/30 px-3 py-2 inline-flex items-center gap-2">
                <span className={`text-xl font-bold tabular-nums ${getScoreColor(score)}`}>
                  {score.toFixed(2)}
                </span>
                <span className={`text-[10px] font-medium uppercase tracking-wider ${getScoreColor(score)}`}>
                  {scoreLabel ?? "r"} · {getScoreLabel(score)}
                </span>
              </div>
            )}
          </div>
        </div>

        <p className="text-sm text-muted-foreground">
          <span className="text-slate-50/70">Construct:</span> {instrument.construct}
        </p>

        {instrument.similarity_rationale && (
          <p className="text-sm italic text-slate-400 leading-relaxed">
            {instrument.similarity_rationale}
          </p>
        )}
      </div>

      {/* Citation */}
      <div className="mt-3 pt-3 border-t border-border/30">
        <p className="text-[11px] leading-relaxed text-muted-foreground/70">
          {instrument.source_citation}
        </p>
      </div>

      {/* Warning */}
      {showWarning && warningText && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-accent/10 border border-accent/20 px-3 py-2">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-accent" />
          <span className="text-xs font-medium text-accent">{warningText}</span>
        </div>
      )}
    </div>
  );
}
