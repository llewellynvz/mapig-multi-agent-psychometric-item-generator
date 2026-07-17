"use client";

import * as React from "react";
import { type FeedbackHistoryEntry } from "@/components/FeedbackHistoryPanel";
import type { InstrumentSetupFormValues } from "@/lib/schemas";
import type { FinalOutput } from "@/lib/types";

export type UiStep = "setup" | "run" | "results";
export type RunKind = "setup" | "refinement";

export interface ActiveRunState {
  threadId: string;
  runId?: string;
  status: "running" | "complete" | "error";
  kind: RunKind;
  feedback: string;
  updatedAt: string;
}

interface PersistedUiSession {
  threadIdInput: string;
  step: UiStep;
  submittedSetup: InstrumentSetupFormValues | null;
  result: FinalOutput | null;
  humanFeedback: string;
  feedbackHistory: FeedbackHistoryEntry[];
  lastRequestJson: string | null;
  lastResponseJson: string | null;
  activeRun: ActiveRunState | null;
}

const SESSION_STORAGE_KEY = "mapig-ui-session-v2";

export function useSessionPersistence() {
  const [hasRestored, setHasRestored] = React.useState(false);
  const [threadIdInput, setThreadIdInput] = React.useState("");
  const [step, setStep] = React.useState<UiStep>("setup");
  const [submittedSetup, setSubmittedSetup] = React.useState<InstrumentSetupFormValues | null>(null);
  const [result, setResult] = React.useState<FinalOutput | null>(null);
  const [humanFeedback, setHumanFeedback] = React.useState("");
  const [feedbackHistory, setFeedbackHistory] = React.useState<FeedbackHistoryEntry[]>([]);
  const [activeRun, setActiveRun] = React.useState<ActiveRunState | null>(null);
  const [lastRequestJson, setLastRequestJson] = React.useState<string | null>(null);
  const [lastResponseJson, setLastResponseJson] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = localStorage.getItem(SESSION_STORAGE_KEY);
      if (!raw) {
        setHasRestored(true);
        return;
      }
      const saved = JSON.parse(raw) as PersistedUiSession;
      setThreadIdInput(saved.threadIdInput ?? "");
      setSubmittedSetup(saved.submittedSetup ?? null);
      setResult(saved.result ?? null);
      setHumanFeedback(saved.humanFeedback ?? "");
      setFeedbackHistory(Array.isArray(saved.feedbackHistory) ? saved.feedbackHistory : []);
      setLastRequestJson(saved.lastRequestJson ?? null);
      setLastResponseJson(saved.lastResponseJson ?? null);
      setActiveRun(saved.activeRun ?? null);

      if (saved.activeRun?.status === "running" && saved.activeRun.threadId) {
        setStep("run");
      } else if (saved.result) {
        setStep("results");
      } else {
        setStep(saved.step ?? "setup");
      }
    } catch {
      // ignore corrupted session payload
    } finally {
      setHasRestored(true);
    }
  }, []);

  React.useEffect(() => {
    if (!hasRestored || typeof window === "undefined") return;
    const payload: PersistedUiSession = {
      threadIdInput,
      step,
      submittedSetup,
      result,
      humanFeedback,
      feedbackHistory,
      lastRequestJson,
      lastResponseJson,
      activeRun,
    };
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(payload));
  }, [
    activeRun,
    feedbackHistory,
    hasRestored,
    humanFeedback,
    lastRequestJson,
    lastResponseJson,
    result,
    step,
    submittedSetup,
    threadIdInput,
  ]);

  return {
    hasRestored,
    threadIdInput,
    setThreadIdInput,
    step,
    setStep,
    submittedSetup,
    setSubmittedSetup,
    result,
    setResult,
    humanFeedback,
    setHumanFeedback,
    feedbackHistory,
    setFeedbackHistory,
    activeRun,
    setActiveRun,
    lastRequestJson,
    setLastRequestJson,
    lastResponseJson,
    setLastResponseJson,
  };
}
