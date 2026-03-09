"use client";

import React, { useState } from "react";
import { SurfaceCard, InsetPanel } from "@/components/ui/surface-card";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PrimaryButton } from "@/components/ui/action-buttons";

interface EvaluationMetrics {
  item_quality_score: number;
  agent_performance_score: number;
  workflow_efficiency_score: number;
  construct_validity_score: number;
  overall_score: number;
  total_comparisons: number;
}

interface EvaluationResults {
  current: EvaluationMetrics;
  baseline: EvaluationMetrics;
  improvement: {
    overall_improvement: number;
    item_quality_improvement: number;
    agent_performance_improvement: number;
    workflow_efficiency_improvement: number;
    construct_validity_improvement: number;
  };
  success_criteria: {
    meets_improvement_threshold: boolean;
    all_dimensions_passing: boolean;
    success: boolean;
  };
}

export default function EvaluationDashboard() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<EvaluationResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runEvaluation = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/v1/run-evaluation?model_provider=claude", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`Evaluation failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

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
              results.success_criteria.success
                ? "border-green-500/70"
                : "border-yellow-500/70"
            }
          >
            <CardHeader className="border-b border-border/60">
              <CardTitle className="text-base md:text-lg">
                {results.success_criteria.success ? "✓" : "✗"} Success Criteria
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-5">
              <InsetPanel className="rounded-2xl border border-accent/35 bg-accent/15 p-3">
                <p className="text-sm font-semibold">Overall Improvement</p>
                <p className="text-2xl font-bold text-accent mt-1">
                  {results.success_criteria.meets_improvement_threshold
                    ? "✓"
                    : "✗"}{" "}
                  {results.improvement.overall_improvement.toFixed(1)}%
                </p>
                <p className="text-xs text-slate-100/90 mt-1">
                  {results.success_criteria.meets_improvement_threshold
                    ? "Exceeds 15% improvement threshold"
                    : "Below 15% improvement threshold"}
                </p>
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
              <InsetPanel className="space-y-2 rounded-2xl p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Item Quality
                </p>
                <p className="text-2xl font-bold">
                  {results.current.item_quality_score.toFixed(1)}/10
                </p>
                <p className="text-xs text-slate-400">
                  +{results.improvement.item_quality_improvement.toFixed(1)}% vs
                  baseline
                </p>
              </InsetPanel>

              <InsetPanel className="space-y-2 rounded-2xl p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Agent Performance
                </p>
                <p className="text-2xl font-bold">
                  {results.current.agent_performance_score.toFixed(1)}/10
                </p>
                <p className="text-xs text-slate-400">
                  +{results.improvement.agent_performance_improvement.toFixed(1)}%
                  vs baseline
                </p>
              </InsetPanel>

              <InsetPanel className="space-y-2 rounded-2xl p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Workflow Efficiency
                </p>
                <p className="text-2xl font-bold">
                  {results.current.workflow_efficiency_score.toFixed(1)}/10
                </p>
                <p className="text-xs text-slate-400">
                  +
                  {results.improvement.workflow_efficiency_improvement.toFixed(1)}%
                  vs baseline
                </p>
              </InsetPanel>

              <InsetPanel className="space-y-2 rounded-2xl p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Construct Validity
                </p>
                <p className="text-2xl font-bold">
                  {results.current.construct_validity_score.toFixed(1)}/10
                </p>
                <p className="text-xs text-slate-400">
                  +
                  {results.improvement.construct_validity_improvement.toFixed(1)}%
                  vs baseline
                </p>
              </InsetPanel>

              <div className="pt-3 border-t border-border/40">
                <p className="text-sm text-slate-400">
                  Based on {results.current.total_comparisons} comparisons to
                  published scales
                </p>
              </div>
            </CardContent>
          </SurfaceCard>
        </>
      )}
    </div>
  );
}
