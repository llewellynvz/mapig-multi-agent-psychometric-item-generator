"use client";

import { History, RotateCcw } from "lucide-react";
import { PrimaryButton, SecondaryButton } from "@/components/ui/action-buttons";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";
import { InsetPanel, SurfaceCard } from "@/components/ui/surface-card";

export interface FeedbackHistoryEntry {
  id: string;
  kind: "setup" | "refinement";
  feedback: string;
  timestampUtc: string;
  runId: string;
  threadId: string;
  itemCount: number;
  iterationCount: number;
  stopReason: string;
}

export interface FeedbackHistoryPanelProps {
  entries: FeedbackHistoryEntry[];
  onReuseFeedback: (feedback: string) => void;
  onClearHistory: () => void;
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function FeedbackHistoryPanel({
  entries,
  onReuseFeedback,
  onClearHistory,
}: FeedbackHistoryPanelProps) {
  return (
    <SurfaceCard className="border-lime-300/70">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b border-border/60">
        <CardTitle className="flex items-center gap-2 text-base md:text-lg">
          <History className="h-5 w-5 text-white" />
          Feedback History
        </CardTitle>
        <SecondaryButton
          type="button"
          size="sm"
          onClick={onClearHistory}
          disabled={entries.length === 0}
        >
          Clear history
        </SecondaryButton>
      </CardHeader>
      <CardContent className="pt-5">
        {entries.length === 0 ? (
          <InsetPanel className="rounded-2xl p-3">
            <p className="text-sm text-muted-foreground">
              No history yet. Each successful run appears here with human feedback and run metadata.
            </p>
          </InsetPanel>
        ) : (
          <div className="space-y-3">
            {entries
              .map((entry, index) => ({ entry, index }))
              .reverse()
              .map(({ entry, index }) => (
                <article
                  key={entry.id}
                  className="inset-panel space-y-2 rounded-2xl p-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Pill>Round {index + 1}</Pill>
                    <Pill className={entry.kind === "refinement" ? "border-accent/60 bg-accent/25" : ""}>
                      {entry.kind === "refinement" ? "Feedback refinement" : "Initial setup run"}
                    </Pill>
                  </div>
                  <p className="text-xs text-muted-foreground">{formatTimestamp(entry.timestampUtc)}</p>
                  <p className="text-xs text-muted-foreground">
                    Run: <span className="font-medium text-white">{entry.runId}</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Thread: <span className="font-medium text-white">{entry.threadId}</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Items: <span className="font-medium text-white">{entry.itemCount}</span> | Iterations:{" "}
                    <span className="font-medium text-white">{entry.iterationCount}</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Stop reason: <span className="font-medium text-white">{entry.stopReason || "N/A"}</span>
                  </p>
                  <InsetPanel className="rounded-xl p-2">
                    <p className="text-xs font-semibold text-muted-foreground">Human feedback</p>
                    <p className="mt-1 text-sm text-slate-100">
                      {entry.feedback || "No explicit human feedback was submitted for this round."}
                    </p>
                  </InsetPanel>
                  {entry.feedback && (
                    <PrimaryButton
                      type="button"
                      size="sm"
                      onClick={() => onReuseFeedback(entry.feedback)}
                    >
                      <RotateCcw className="mr-2 h-4 w-4" />
                      Reuse this feedback
                    </PrimaryButton>
                  )}
                </article>
              ))}
          </div>
        )}
      </CardContent>
    </SurfaceCard>
  );
}
