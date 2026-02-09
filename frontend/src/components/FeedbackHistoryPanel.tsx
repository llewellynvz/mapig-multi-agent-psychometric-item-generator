"use client";

import { History, RotateCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

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
    <Card className="glass-panel shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b border-border/60">
        <CardTitle className="flex items-center gap-2 text-base md:text-lg">
          <History className="h-5 w-5 text-primary" />
          Feedback History
        </CardTitle>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="bg-primary text-white hover:bg-accent hover:text-white"
          onClick={onClearHistory}
          disabled={entries.length === 0}
        >
          Clear history
        </Button>
      </CardHeader>
      <CardContent className="space-y-3 pt-5">
        {entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No history yet. Each successful run appears here with human feedback and run metadata.
          </p>
        ) : (
          entries
            .map((entry, index) => ({ entry, index }))
            .reverse()
            .map(({ entry, index }) => (
              <article
                key={entry.id}
                className="space-y-2 rounded-2xl border border-white/15 bg-white/10 p-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary">Round {index + 1}</Badge>
                  <Badge variant={entry.kind === "refinement" ? "default" : "outline"}>
                    {entry.kind === "refinement" ? "Feedback refinement" : "Initial setup run"}
                  </Badge>
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
                <div className="rounded-xl bg-white/10 p-2">
                  <p className="text-xs font-semibold text-muted-foreground">Human feedback</p>
                  <p className="mt-1 text-sm text-slate-100">
                    {entry.feedback || "No explicit human feedback was submitted for this round."}
                  </p>
                </div>
                {entry.feedback && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="bg-primary text-white hover:bg-accent hover:text-white"
                    onClick={() => onReuseFeedback(entry.feedback)}
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Reuse this feedback
                  </Button>
                )}
              </article>
            ))
        )}
      </CardContent>
    </Card>
  );
}
