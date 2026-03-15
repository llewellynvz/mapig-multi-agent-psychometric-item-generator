"use client";

import * as React from "react";
import { AlertTriangle, ExternalLink } from "lucide-react";
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

/**
 * Extract a paper URL (DOI or direct link) from a citation string
 */
function extractPaperUrl(citation: string): string | null {
  // Try DOI URL pattern
  const doiUrlMatch = citation.match(/(?:https?:\/\/)?(?:dx\.)?doi\.org\/([^\s,)]+)/i);
  if (doiUrlMatch) return `https://doi.org/${doiUrlMatch[1]}`;

  // Try raw DOI reference (10.xxxx/...)
  const rawDoi = citation.match(/\b(10\.\d{4,}\/[^\s,)]+)/);
  if (rawDoi) return `https://doi.org/${rawDoi[1]}`;

  // Try any URL
  const urlMatch = citation.match(/(https?:\/\/[^\s,)]+)/);
  if (urlMatch) return urlMatch[1];

  return null;
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
  const paperUrl = extractPaperUrl(instrument.source_citation);

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

      {/* Main content row: info left, score badge right */}
      <div className="mt-3 flex items-start justify-between gap-4">
        {/* Left: Instrument info */}
        <div className="min-w-0 flex-1 space-y-2">
          <div>
            <h4 className="text-base font-semibold text-slate-50 leading-tight">
              {instrument.name}
            </h4>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              <span className="text-sm text-muted-foreground">{authorYear}</span>
              {paperUrl && (
                <a
                  href={paperUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
                >
                  Read paper
                  <ExternalLink className="h-3 w-3" />
                </a>
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

        {/* Right: Square score badge */}
        {hasScore && (
          <div className="flex shrink-0 flex-col items-center justify-center rounded-xl border border-border/40 bg-slate-900/30 w-24 h-24">
            <span className={`text-2xl font-bold tabular-nums leading-none ${getScoreColor(score)}`}>
              {score.toFixed(2)}
            </span>
            <span className="mt-1 text-[9px] font-medium text-muted-foreground">
              r = {score.toFixed(2)}
            </span>
            <span className={`mt-0.5 text-[9px] font-medium uppercase tracking-wider ${getScoreColor(score)}`}>
              {getScoreLabel(score)}
            </span>
          </div>
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
