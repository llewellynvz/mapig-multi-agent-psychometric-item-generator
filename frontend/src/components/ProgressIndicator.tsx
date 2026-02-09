"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export interface ProgressState {
  currentNode: string | null;
  displayName: string | null;
  iteration: number;
  status: "idle" | "running" | "complete" | "error";
  errorMessage?: string;
}

interface ProgressIndicatorProps {
  progress: ProgressState;
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

export function ProgressIndicator({ progress }: ProgressIndicatorProps) {
  const displayName =
    progress.displayName ||
    (progress.currentNode ? NODE_DISPLAY_NAMES[progress.currentNode] || progress.currentNode : "Starting...");

  return (
    <Card className="border-primary/20 bg-gradient-to-br from-background to-primary/5 p-6 shadow-sm">
      <div className="space-y-5">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold">Generation Progress</h3>
          {progress.status === "running" && (
            <div className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
          )}
          {progress.status === "complete" && (
            <Badge variant="default" className="bg-green-500">
              Complete
            </Badge>
          )}
          {progress.status === "error" && (
            <Badge className="bg-red-500 text-white">Error</Badge>
          )}
        </div>

        {progress.status === "running" && (
          <div className="space-y-3">
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div className="h-full w-1/3 animate-pulse rounded-full bg-primary" />
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
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
          <div className="rounded-md bg-destructive/10 p-3">
            <p className="text-sm text-destructive">{progress.errorMessage}</p>
          </div>
        )}

        {progress.status === "idle" && (
          <p className="text-sm text-muted-foreground">Ready to generate items...</p>
        )}
      </div>
    </Card>
  );
}
