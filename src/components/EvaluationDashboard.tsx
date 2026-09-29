"use client";

import React, { useState } from "react";
import { SurfaceCard, InsetPanel } from "@/components/ui/surface-card";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PrimaryButton } from "@/components/ui/action-buttons";
import { API_BASE_URL } from "@/lib/api";

// Scores are the mean LLM-judge score (1-10) for the dimension of the same name.
interface EvaluationMetrics {
  quality_parity_score: number;
  construct_fidelity_score: number;
  stylistic_similarity_score: number;
  psychometric_properties_score: number;
  overall_score: number;
  total_comparisons: number;
}

type DimensionKey =
  | "quality_parity"
  | "construct_fidelity"
  | "stylistic_similarity"
  | "psychometric_properties";

interface FailedScale {
  name: string;
  domain: string;
  error: string;
}

interface EvaluationResults {
  baseline_source?: "synthetic" | "measured";
  improvement_basis?: "synthetic_reference" | "measured_baseline";
  mode?: string;
  model_provider?: string;
  pairing_method?: string | null;
  evaluated_scales?: string[];
  failed_scales?: FailedScale[];
  current: EvaluationMetrics;
  baseline: EvaluationMetrics;
  improvement: {
    overall_improvement: number;
  } & Record<`${DimensionKey}_improvement`, number>;
  success_criteria: {
    meets_improvement_threshold: boolean;
    all_dimensions_passing: boolean;
    // null = undetermined (e.g. baseline is a synthetic reference)
    success: boolean | null;
    success_reason?: string | null;
  };
}

const DIMENSIONS: { key: DimensionKey; label: string; description: string }[] = [
  {
    key: "quality_parity",
    label: "Quality Parity",
    description: "Clarity and precision relative to the published item",
  },
  {
    key: "construct_fidelity",
    label: "Construct Fidelity",
    description: "Alignment with the target construct",
  },
  {
    key: "stylistic_similarity",
    label: "Stylistic Similarity",
    description: "Tone and format similarity to the published item",
  },
  {
    key: "psychometric_properties",
    label: "Psychometric Properties",
    description: "Judged difficulty, discrimination and bias",
  },
];

const formatPct = (value: number) => `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;

export default function EvaluationDashboard() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<EvaluationResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runEvaluation = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/v1/run-evaluation?model_provider=claude`, {
        method: "POST",
      });

      if (!response.ok) {
        // statusText is empty over HTTP/2; prefer the backend's JSON `detail`.
        let detail: string = response.statusText || String(response.status);
        try {
          const body = (await response.json()) as { detail?: unknown };
          if (typeof body.detail === "string" && body.detail) detail = body.detail;
        } catch {
          // non-JSON error body
        }
        throw new Error(`Evaluation failed: ${detail}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const isSynthetic = results?.baseline_source === "synthetic";

  return (
    <div className="space-y-6">
      {/* Run Button */}
      <div className="flex items-center gap-4">
        <PrimaryButton onClick={runEvaluation} disabled={loading}>
          {loading ? "Running evaluation suite..." : "Run Evaluation"}
        </PrimaryButton>
        {loading && (
          <p className="text-sm text-slate-400">
            Generating items and comparing to 25 benchmark items...
          </p>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <SurfaceCard className="border-red-500/70">
          <CardContent className="pt-5">
            <p className="text-red-400 font-medium">Error: {error}</p>
          </CardContent>
        </SurfaceCard>
      )}

      {/* Results Display */}
      {results && (
        <>
          {/* Success Criteria Summary */}
          <SurfaceCard
            className={
              results.success_criteria.success === true
                ? "border-green-500/70"
                : results.success_criteria.success === false
                  ? "border-red-500/70"
                  : "border-yellow-500/70"
            }
          >
            <CardHeader className="border-b border-border/60">
              <CardTitle className="text-base md:text-lg">
                {results.success_criteria.success === true
                  ? "✓ Success Criteria Met"
                  : results.success_criteria.success === false
                    ? "✗ Success Criteria Not Met"
                    : "Success Criteria Undetermined"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-5">
              {results.success_criteria.success_reason && (
                <p className="text-sm text-yellow-300/90">
                  {results.success_criteria.success_reason}
                </p>
              )}

              {results.failed_scales && results.failed_scales.length > 0 && (
                <InsetPanel className="rounded-2xl border border-red-500/50 bg-red-500/10 p-3">
                  <p className="text-sm font-semibold">
                    {results.failed_scales.length} scale
                    {results.failed_scales.length === 1 ? "" : "s"} failed (excluded from scores)
                  </p>
                  <ul className="mt-1 space-y-1 text-xs text-slate-100/90">
                    {results.failed_scales.map((scale) => (
                      <li key={scale.name}>
                        <span className="font-medium">{scale.name}</span> ({scale.domain}):{" "}
                        {scale.error}
                      </li>
                    ))}
                  </ul>
                </InsetPanel>
              )}

              <InsetPanel className="rounded-2xl border border-accent/35 bg-accent/15 p-3">
                <p className="text-sm font-semibold">
                  {isSynthetic ? "Overall Change vs Synthetic Reference" : "Overall Improvement"}
                </p>
                <p className="text-2xl font-bold text-accent mt-1">
                  {results.success_criteria.meets_improvement_threshold
                    ? "✓"
                    : "✗"}{" "}
                  {formatPct(results.improvement.overall_improvement)}
                </p>
                <p className="text-xs text-slate-100/90 mt-1">
                  {results.success_criteria.meets_improvement_threshold
                    ? "Exceeds 15% improvement threshold"
                    : "Below 15% improvement threshold"}
                  {isSynthetic ? " (relative to a synthetic reference)" : ""}
                </p>
                {isSynthetic && (
                  <p className="text-xs text-yellow-300/90 mt-1">
                    Baseline is a fixed synthetic reference, not a measured run — improvement
                    figures are illustrative and cannot establish success.
                  </p>
                )}
                {results.mode === "mock" && (
                  <p className="text-xs text-yellow-300/90 mt-1">
                    Running in mock mode — scores are mock values.
                  </p>
                )}
              </InsetPanel>

              <InsetPanel className="rounded-2xl border border-accent/35 bg-accent/15 p-3">
                <p className="text-sm font-semibold">Dimension Quality</p>
                <p className="text-2xl font-bold text-accent mt-1">
                  {results.success_criteria.all_dimensions_passing ? "✓" : "✗"}{" "}
                  {results.success_criteria.all_dimensions_passing
                    ? "All ≥7.0"
                    : "Some <7.0"}
                </p>
                <p className="text-xs text-slate-100/90 mt-1">
                  {results.success_criteria.all_dimensions_passing
                    ? "All dimensions meet quality threshold"
                    : "One or more dimensions below 7.0 threshold"}
                </p>
              </InsetPanel>
            </CardContent>
          </SurfaceCard>

          {/* Dimension Scores */}
          <SurfaceCard className="border-lime-300/70">
            <CardHeader className="border-b border-border/60">
              <CardTitle className="text-base md:text-lg">
                Evaluation Dimensions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5 pt-5">
              {DIMENSIONS.map(({ key, label, description }) => (
                <InsetPanel key={key} className="space-y-2 rounded-2xl p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    {label}
                  </p>
                  <p className="text-2xl font-bold">
                    {results.current[`${key}_score`].toFixed(1)}/10
                  </p>
                  <p className="text-xs text-slate-400">{description}</p>
                  <p className="text-xs text-slate-400">
                    {formatPct(results.improvement[`${key}_improvement`])} vs{" "}
                    {isSynthetic ? "synthetic reference" : "baseline"}
                  </p>
                </InsetPanel>
              ))}

              <div className="pt-3 border-t border-border/40">
                <p className="text-sm text-slate-400">
                  Based on {results.current.total_comparisons} comparisons to
                  published scale items
                  {results.pairing_method === "embedding_nearest_neighbor"
                    ? " (each generated item paired with its most similar published item by embedding similarity)"
                    : results.pairing_method
                      ? " (each generated item paired with its most similar published item by word overlap)"
                      : ""}
                </p>
              </div>
            </CardContent>
          </SurfaceCard>
        </>
      )}
    </div>
  );
}
