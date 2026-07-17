"use client";

import * as React from "react";
import { type ProgressState } from "@/components/ProgressIndicator";
import { useToast } from "@/components/ui/use-toast";
import { fetchRunStatus, GenerateError } from "@/lib/generate";
import type { FinalOutput } from "@/lib/types";
import type { ActiveRunState, RunKind, UiStep } from "@/hooks/useSessionPersistence";

function isFinalOutput(value: unknown): value is FinalOutput {
  if (!value || typeof value !== "object") return false;
  const obj = value as Record<string, unknown>;
  return Array.isArray(obj.final_items) && typeof obj.audit === "object" && obj.audit !== null;
}

interface UseRunRecoveryOptions {
  hasRestored: boolean;
  activeRun: ActiveRunState | null;
  isMutationPending: boolean;
  appendHistoryEntry: (data: FinalOutput, kind: RunKind, feedback: string) => void;
  toast: ReturnType<typeof useToast>["toast"];
  setStep: React.Dispatch<React.SetStateAction<UiStep>>;
  setProgress: React.Dispatch<React.SetStateAction<ProgressState>>;
  setActiveRun: React.Dispatch<React.SetStateAction<ActiveRunState | null>>;
  setResult: React.Dispatch<React.SetStateAction<FinalOutput | null>>;
  setThreadIdInput: React.Dispatch<React.SetStateAction<string>>;
  setLastResponseJson: React.Dispatch<React.SetStateAction<string | null>>;
}

export function useRunRecovery({
  hasRestored,
  activeRun,
  isMutationPending,
  appendHistoryEntry,
  toast,
  setStep,
  setProgress,
  setActiveRun,
  setResult,
  setThreadIdInput,
  setLastResponseJson,
}: UseRunRecoveryOptions) {
  React.useEffect(() => {
    if (!hasRestored) return;
    if (!activeRun?.threadId || activeRun.status !== "running") return;
    if (isMutationPending) return;

    let cancelled = false;
    const poll = async () => {
      try {
        const status = await fetchRunStatus(activeRun.threadId);
        if (cancelled) return;

        if (status.status === "running") {
          setStep("run");
          setProgress({
            currentNode: status.current_node ?? null,
            displayName: status.display_name ?? null,
            iteration: status.iteration ?? 0,
            status: "running",
          });
          // No setActiveRun here: a new object each poll would re-trigger this
          // effect (activeRun is a dep) and collapse the 2.5s interval into a
          // tight polling loop. Transitions below still update it.
          return;
        }

        if (status.status === "complete" && isFinalOutput(status.final_output)) {
          setResult(status.final_output);
          setStep("results");
          setThreadIdInput(status.thread_id);
          setProgress({
            currentNode: "finalize_node",
            displayName: "Finalizing",
            iteration: status.final_output.audit.iteration_count,
            status: "complete",
          });
          setActiveRun((prev) =>
            prev
              ? {
                ...prev,
                threadId: status.thread_id,
                runId: status.run_id,
                status: "complete",
                updatedAt: status.updated_at ?? new Date().toISOString(),
              }
              : prev
          );
          appendHistoryEntry(status.final_output, activeRun.kind, activeRun.feedback);
          setLastResponseJson(JSON.stringify(status.final_output, null, 2));
          toast({ title: "Session recovered", description: "Recovered a completed run.", variant: "default" });
          return;
        }

        if (status.status === "error") {
          setProgress((prev) => ({
            ...prev,
            status: "error",
            errorMessage: status.error || "Run failed while session was disconnected.",
          }));
          setActiveRun((prev) =>
            prev
              ? {
                ...prev,
                runId: status.run_id,
                status: "error",
                updatedAt: status.updated_at ?? new Date().toISOString(),
              }
              : prev
          );
          toast({
            title: "Recovered session state",
            description: status.error || "The previous run ended with an error.",
            variant: "default",
          });
        }
      } catch (error) {
        const err = error as GenerateError;
        if (err.status === 404) {
          // Server restarted — in-memory registry lost this thread.
          // Clear stale running state so user returns to setup.
          setActiveRun((prev) =>
            prev ? { ...prev, status: "error", updatedAt: new Date().toISOString() } : prev
          );
          setStep("setup");
          setProgress((prev) => ({
            ...prev,
            status: "idle",
          }));
        } else {
          setProgress((prev) => ({
            ...prev,
            status: "error",
            errorMessage: "Could not fetch run status.",
          }));
        }
      }
    };

    void poll();
    const timer = window.setInterval(() => {
      void poll();
    }, 2500);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeRun, appendHistoryEntry, hasRestored, isMutationPending, toast]);
}
