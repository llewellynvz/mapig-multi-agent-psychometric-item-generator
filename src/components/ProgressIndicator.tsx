"use client";

import * as React from "react";
import { Check, Loader2 } from "lucide-react";
import { Pill } from "@/components/ui/pill";
import { SurfaceCard } from "@/components/ui/surface-card";
import type { ProgressEvent } from "@/lib/api";

export interface ProgressState {
  currentNode: string | null;
  displayName: string | null;
  iteration: number;
  status: "idle" | "running" | "complete" | "error";
  errorMessage?: string;
}

export interface CompletedNode {
  node: string;
  displayName: string;
  iteration: number;
  timestamp: number;
}

interface ProgressIndicatorProps {
  progress: ProgressState;
  logs?: ProgressEvent[];
  useChatGPT?: boolean;
  completedNodes?: CompletedNode[];
}

const NODE_DISPLAY_NAMES: Record<string, string> = {
  init_run: "Setting up pipeline",
  retrieve_node: "Searching academic sources",
  item_writer_node: "Drafting survey items",
  validation_node: "Validating item quality",
  regenerate_items_node: "Improving failed items",
  reviewers_fanout_node: "Running expert review panel",
  content_review_node: "Reviewing construct alignment",
  linguistic_review_node: "Reviewing language clarity",
  bias_review_node: "Reviewing bias and fairness",
  critic_node: "Evaluating review outcomes",
  meta_editor_node: "Applying reviewer feedback",
  finalize_node: "Finalizing results",
  correlation_node: "Estimating inter-item correlations",
  comparison_node: "Comparing with published instruments",
  cross_construct_node: "Analyzing cross-construct validity",
  analytics_dispatch_node: "Running analytics suite",
};

/* ── Stage-aware progress bar ── */
const FIRST_ITER_NODES = [
  "init_run", "retrieve_node", "item_writer_node",
  "content_review_node", "linguistic_review_node", "bias_review_node",
  "critic_node", "meta_editor_node",
];
const LATER_ITER_NODES = [
  "item_writer_node", "content_review_node", "linguistic_review_node",
  "bias_review_node", "critic_node", "meta_editor_node",
];
const POST_ITER_NODES = [
  "finalize_node", "correlation_node", "comparison_node", "cross_construct_node",
];

function computeStageProgress(currentNode: string | null, iteration: number): number {
  if (!currentNode) return 0;

  const postIdx = POST_ITER_NODES.indexOf(currentNode);
  if (postIdx >= 0) return (postIdx + 1) / POST_ITER_NODES.length;

  const nodes = iteration <= 1 ? FIRST_ITER_NODES : LATER_ITER_NODES;
  const idx = nodes.indexOf(currentNode);
  if (idx >= 0) return (idx + 1) / nodes.length;

  return 0.5;
}

function getPhaseLabel(currentNode: string | null, iteration: number): string {
  if (!currentNode) return "Starting";
  if (POST_ITER_NODES.includes(currentNode)) return "Finalizing";
  if (iteration > 1) return `Round ${iteration}`;
  return "Round 1";
}

export function ProgressIndicator({
  progress,
  logs = [],
  useChatGPT = false,
  completedNodes = [],
}: ProgressIndicatorProps) {
  const displayName =
    progress.displayName ||
    (progress.currentNode
      ? NODE_DISPLAY_NAMES[progress.currentNode] || progress.currentNode
      : "Starting...");

  const logContainerRef = React.useRef<HTMLDivElement>(null);
  const timelineEndRef = React.useRef<HTMLDivElement>(null);

  const stageProgress = progress.status === "running"
    ? computeStageProgress(progress.currentNode, progress.iteration)
    : progress.status === "complete" ? 1 : 0;

  const phaseLabel = progress.status === "running"
    ? getPhaseLabel(progress.currentNode, progress.iteration)
    : "";

  React.useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  React.useEffect(() => {
    timelineEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [completedNodes.length, progress.currentNode]);

  return (
    <SurfaceCard className="border-sky-300/70 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 px-6 pt-6 pb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold tracking-tight">Generation Progress</h3>
          {useChatGPT ? (
            <Pill className="border-accent/60 bg-accent/30 text-accent text-[10px]">GPT 5.2</Pill>
          ) : (
            <Pill className="border-sky-400/60 bg-sky-400/20 text-sky-300 text-[10px]">Claude</Pill>
          )}
        </div>
        {progress.status === "running" && phaseLabel && (
          <Pill className="border-accent/40 bg-accent/15 text-accent text-[10px]">
            {phaseLabel}
          </Pill>
        )}
        {progress.status === "complete" && (
          <Pill className="border-emerald-500/40 bg-emerald-500/15 text-emerald-400 text-[10px]">
            Complete
          </Pill>
        )}
        {progress.status === "error" && (
          <Pill className="border-red-500/40 bg-red-500/15 text-red-400 text-[10px]">Error</Pill>
        )}
      </div>

      {/* Progress bar */}
      {progress.status === "running" && (
        <div className="px-6 pb-4">
          <div className="h-1 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-gradient-to-r from-sky-500 to-accent transition-all duration-700 ease-out"
              style={{ width: `${Math.round(stageProgress * 100)}%` }}
            />
          </div>
        </div>
      )}
      {progress.status === "complete" && (
        <div className="px-6 pb-4">
          <div className="h-1 overflow-hidden rounded-full bg-white/10">
            <div className="h-full w-full rounded-full bg-emerald-500/80" />
          </div>
        </div>
      )}

      {/* Timeline */}
      {(completedNodes.length > 0 || (progress.status === "running" && progress.currentNode)) && (
        <div className="border-t border-white/5 px-6 py-4">
          <div className="max-h-52 overflow-y-auto pr-1">
            <div className="relative pl-10">
              {/* Vertical connecting line */}
              <div className="absolute left-[7px] top-1 bottom-1 w-px bg-white/10" />

              {completedNodes.map((node, idx) => (
                <div
                  key={`${node.node}-${idx}`}
                  className="relative flex items-center pb-3 last:pb-0"
                >
                  <div className="absolute left-[-33px] flex h-4 w-4 items-center justify-center rounded-full bg-accent/20">
                    <Check className="h-2.5 w-2.5 text-accent" />
                  </div>
                  <span className="text-sm text-muted-foreground">{node.displayName}</span>
                </div>
              ))}

              {progress.status === "running" && progress.currentNode && (
                <div className="relative flex items-center pb-0">
                  <div className="absolute left-[-33px] flex h-4 w-4 items-center justify-center rounded-full bg-sky-500/20">
                    <Loader2 className="h-2.5 w-2.5 animate-spin text-sky-400" />
                  </div>
                  <span className="text-sm font-medium text-foreground">{displayName}</span>
                </div>
              )}
              <div ref={timelineEndRef} />
            </div>
          </div>
        </div>
      )}

      {/* Status messages */}
      {progress.status === "complete" && completedNodes.length === 0 && (
        <div className="px-6 pb-5">
          <p className="text-sm text-muted-foreground">Generation completed successfully.</p>
        </div>
      )}

      {progress.status === "error" && progress.errorMessage && (
        <div className="px-6 pb-5">
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3">
            <p className="text-sm text-red-300">{progress.errorMessage}</p>
          </div>
        </div>
      )}

      {progress.status === "idle" && (
        <div className="px-6 pb-5">
          <p className="text-sm text-muted-foreground">Ready to generate items.</p>
        </div>
      )}

      {/* Live Logs */}
      {progress.status === "running" && logs.length > 0 && (
        <div className="border-t border-white/5 px-6 py-4">
          <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Live Logs
          </h4>
          <div
            ref={logContainerRef}
            className="max-h-48 overflow-y-auto space-y-0.5 rounded-lg bg-black/20 p-3"
          >
            {logs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs font-mono leading-relaxed">
                <span
                  className={`shrink-0 ${
                    log.level === "error"
                      ? "text-red-400"
                      : log.level === "warning"
                        ? "text-yellow-400"
                        : "text-slate-500"
                  }`}
                >
                  {log.timestamp?.split("T")[1]?.slice(0, 8) ?? ""}
                </span>
                <span className="shrink-0 text-sky-400/70">{log.source}</span>
                <span className="text-slate-400">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </SurfaceCard>
  );
}
