"use client";

import * as React from "react";
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

interface ProgressIndicatorProps {
  progress: ProgressState;
  logs?: ProgressEvent[];
  useChatGPT?: boolean;
}

const NODE_DISPLAY_NAMES: Record<string, string> = {
  init_run: "Initializing",
  retrieve_node: "Retrieving Evidence",
  item_writer_node: "Writing Items",
  content_review_node: "Reviewing Content",
  linguistic_review_node: "Reviewing Linguistics",
  bias_review_node: "Reviewing Bias",
  critic_node: "Evaluating Quality",
  meta_editor_node: "Revising Items",
  finalize_node: "Finalizing",
};

export function ProgressIndicator({ progress, logs = [], useChatGPT = false }: ProgressIndicatorProps) {
  const displayName =
    progress.displayName ||
    (progress.currentNode ? NODE_DISPLAY_NAMES[progress.currentNode] || progress.currentNode : "Starting...");

  const logContainerRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  React.useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <SurfaceCard className="border-sky-300/70 p-6">
      <div className="space-y-5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold">Generation Progress</h3>
            {useChatGPT ? (
              <Pill className="border-accent/60 bg-accent/30 text-accent">GPT 5.2</Pill>
            ) : (
              <Pill className="border-sky-400/60 bg-sky-400/20 text-sky-300">Claude</Pill>
            )}
          </div>
          {progress.status === "running" && (
            <div className="h-2 w-2 animate-pulse rounded-full bg-accent" />
          )}
          {progress.status === "complete" && (
            <Pill className="border-accent/60 bg-accent/30">Complete</Pill>
          )}
          {progress.status === "error" && (
            <Pill className="border-accent/60 bg-accent/30">Error</Pill>
          )}
        </div>

        {progress.status === "running" && (
          <div className="space-y-3">
            <div className="h-2 overflow-hidden rounded-full bg-white/15">
              <div className="h-full w-1/3 animate-pulse rounded-full bg-accent" />
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-accent" />
              <p className="text-sm font-medium">{displayName}</p>
            </div>
            {progress.iteration > 0 && (
              <p className="text-xs text-muted-foreground">
                Iteration {progress.iteration} of up to 3
              </p>
            )}
          </div>
        )}

        {progress.status === "complete" && (
          <p className="text-sm text-muted-foreground">Generation completed successfully!</p>
        )}

        {progress.status === "error" && progress.errorMessage && (
          <div className="rounded-md bg-accent/20 p-3">
            <p className="text-sm font-medium text-slate-100">{progress.errorMessage}</p>
          </div>
        )}

        {progress.status === "idle" && (
          <p className="text-sm text-muted-foreground">Ready to generate items...</p>
        )}

        {/* Live Logs */}
        {progress.status === "running" && logs.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-300">Live Logs</h4>
            <div
              ref={logContainerRef}
              className="max-h-60 overflow-y-auto space-y-1 rounded-md bg-white/5 p-3"
            >
              {logs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs font-mono">
                  <span
                    className={`shrink-0 ${
                      log.level === "error"
                        ? "text-red-400"
                        : log.level === "warning"
                          ? "text-yellow-400"
                          : "text-slate-400"
                    }`}
                  >
                    [{log.timestamp?.split("T")[1]?.slice(0, 8) ?? ""}]
                  </span>
                  <span className="text-sky-300 shrink-0">{log.source}:</span>
                  <span className="text-slate-300">{log.message}</span>
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <span className="text-slate-500 text-[10px]">
                      {JSON.stringify(log.metadata)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </SurfaceCard>
  );
}
