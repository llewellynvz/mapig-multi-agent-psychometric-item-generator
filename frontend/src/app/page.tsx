"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertCircle, ArrowLeft, Rocket } from "lucide-react";
import { AppDescription } from "@/components/AppDescription";
import { DeveloperDrawer } from "@/components/DeveloperDrawer";
import { EvidenceAuditPanel } from "@/components/EvidenceAuditPanel";
import { FeedbackHistoryPanel, type FeedbackHistoryEntry } from "@/components/FeedbackHistoryPanel";
import { FlowStepper } from "@/components/FlowStepper";
import { GeneratedItemsTable } from "@/components/GeneratedItemsTable";
import { HumanFeedbackPanel } from "@/components/HumanFeedbackPanel";
import { InstrumentSetupForm } from "@/components/InstrumentSetupForm";
import { ProgressIndicator, type ProgressState } from "@/components/ProgressIndicator";
import { SetupSnapshotCard } from "@/components/SetupSnapshotCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { type ProgressEvent } from "@/lib/api";
import { fetchRunStatus, formToRequest, generateItemsStream, GenerateError } from "@/lib/generate";
import type { InstrumentSetupFormValues } from "@/lib/schemas";
import type { FinalOutput, UserRequest } from "@/lib/types";

type UiStep = "setup" | "run" | "results";
type RunKind = "setup" | "refinement";

interface ActiveRunState {
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

function isFinalOutput(value: unknown): value is FinalOutput {
  if (!value || typeof value !== "object") return false;
  const obj = value as Record<string, unknown>;
  return Array.isArray(obj.final_items) && typeof obj.audit === "object" && obj.audit !== null;
}

function deriveRunKind(request: UserRequest): RunKind {
  return (request.previous_items?.length ?? 0) > 0 ? "refinement" : "setup";
}

export default function HomePage() {
  const { toast } = useToast();
  const formRef = React.useRef<{ setErrorsFromApi: (detail: unknown) => void } | null>(null);
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
  const [progress, setProgress] = React.useState<ProgressState>({
    currentNode: null,
    displayName: null,
    iteration: 0,
    status: "idle",
  });

  const appendHistoryEntry = React.useCallback(
    (data: FinalOutput, kind: RunKind, feedback: string) => {
      setFeedbackHistory((prev) => {
        if (prev.some((entry) => entry.runId === data.audit.run_id)) {
          return prev;
        }
        return [
          ...prev,
          {
            id: data.audit.run_id,
            kind,
            feedback: feedback.trim(),
            timestampUtc: data.audit.timestamp_utc,
            runId: data.audit.run_id,
            threadId: data.audit.thread_id,
            itemCount: data.final_items.length,
            iterationCount: data.audit.iteration_count,
            stopReason: data.audit.stop_reason,
          },
        ];
      });
    },
    []
  );

  const mutation = useMutation({
    mutationFn: async ({ request, threadId }: { request: UserRequest; threadId?: string }) =>
      generateItemsStream({
        body: request,
        threadId,
        onProgress: (event: ProgressEvent) => {
          if (event.type === "start") {
            if (event.thread_id) {
              setThreadIdInput(event.thread_id);
            }
            setActiveRun((prev) => ({
              threadId: event.thread_id || prev?.threadId || "",
              runId: event.run_id || prev?.runId,
              status: "running",
              kind: prev?.kind ?? "setup",
              feedback: prev?.feedback ?? "",
              updatedAt: new Date().toISOString(),
            }));
            setProgress({
              currentNode: null,
              displayName: null,
              iteration: 0,
              status: "running",
            });
          } else if (event.type === "node_start") {
            setProgress((prev) => ({
              ...prev,
              currentNode: event.node || null,
              displayName: event.display_name || null,
              iteration: event.iteration || prev.iteration,
              status: "running",
            }));
          } else if (event.type === "iteration") {
            setProgress((prev) => ({
              ...prev,
              iteration: event.iteration || prev.iteration,
            }));
          } else if (event.type === "complete") {
            setProgress((prev) => ({
              ...prev,
              status: "complete",
            }));
          } else if (event.type === "error") {
            setProgress((prev) => ({
              ...prev,
              status: "error",
              errorMessage: event.message || "Unknown error",
            }));
          }
        },
      }),
    onSuccess: (data, variables) => {
      const kind = deriveRunKind(variables.request);
      const feedbackText = variables.request.human_feedback ?? "";

      setResult(data);
      setThreadIdInput(data.audit.thread_id);
      setActiveRun({
        threadId: data.audit.thread_id,
        runId: data.audit.run_id,
        status: "complete",
        kind,
        feedback: feedbackText,
        updatedAt: new Date().toISOString(),
      });
      appendHistoryEntry(data, kind, feedbackText);
      setHumanFeedback("");
      setLastResponseJson(JSON.stringify(data, null, 2));
      setStep("results");
      toast({ title: "Done", description: "Items generated successfully.", variant: "default" });
    },
    onError: (err: GenerateError) => {
      setProgress((prev) => ({
        ...prev,
        status: "error",
        errorMessage: err.message,
      }));
      setActiveRun((prev) =>
        prev
          ? {
              ...prev,
              status: "error",
              updatedAt: new Date().toISOString(),
            }
          : prev
      );
      setLastResponseJson(err.rawText || null);
      if (err.status === 422 && err.detail) {
        setStep("setup");
        formRef.current?.setErrorsFromApi(err.detail);
        toast({
          title: "Validation error",
          description: "Check the form for field-specific messages.",
          variant: "default",
        });
      } else {
        toast({
          title: "Error",
          description: err.status >= 500 ? "Server error. Try again later." : err.message,
          variant: "default",
        });
      }
    },
  });

  const resetProgress = React.useCallback(() => {
    setProgress({
      currentNode: null,
      displayName: null,
      iteration: 0,
      status: "idle",
    });
  }, []);

  const runGeneration = React.useCallback(
    (request: UserRequest, threadId?: string) => {
      const kind = deriveRunKind(request);
      const feedbackText = request.human_feedback ?? "";
      const effectiveThreadId =
        threadId?.trim() ||
        (typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random().toString(16).slice(2)}`);

      setStep("run");
      setResult(null);
      setLastResponseJson(null);
      setLastRequestJson(JSON.stringify(request, null, 2));
      setThreadIdInput(effectiveThreadId);
      setActiveRun({
        threadId: effectiveThreadId,
        status: "running",
        kind,
        feedback: feedbackText,
        updatedAt: new Date().toISOString(),
      });
      resetProgress();
      mutation.mutate({ request, threadId: effectiveThreadId });
    },
    [mutation, resetProgress]
  );

  const handleSetupSubmit = React.useCallback(
    (values: InstrumentSetupFormValues, threadId?: string) => {
      setSubmittedSetup(values);
      setHumanFeedback("");
      setFeedbackHistory([]);
      runGeneration(formToRequest(values), threadId);
    },
    [runGeneration]
  );

  const handleRefineRun = React.useCallback(() => {
    if (!submittedSetup || !result) return;
    const request = formToRequest({
      ...submittedSetup,
      human_feedback: humanFeedback,
      previous_items: result.final_items.map((item) => item.item_text),
    });
    const threadId = threadIdInput.trim() || result.audit.thread_id;
    runGeneration(request, threadId);
  }, [humanFeedback, result, runGeneration, submittedSetup, threadIdInput]);

  const handleStartNew = React.useCallback(() => {
    setStep("setup");
    setResult(null);
    setHumanFeedback("");
    setFeedbackHistory([]);
    setActiveRun(null);
    setLastResponseJson(null);
    resetProgress();
  }, [resetProgress]);

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

  React.useEffect(() => {
    if (!hasRestored) return;
    if (!activeRun?.threadId || activeRun.status !== "running") return;
    if (mutation.isPending) return;

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
          setActiveRun((prev) =>
            prev
              ? {
                  ...prev,
                  threadId: status.thread_id,
                  runId: status.run_id,
                  status: "running",
                  updatedAt: status.updated_at ?? new Date().toISOString(),
                }
              : prev
          );
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
        if (err.status !== 404) {
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
  }, [activeRun, appendHistoryEntry, hasRestored, mutation.isPending, toast]);

  const jumpToResults = React.useCallback(() => {
    if (result) {
      setStep("results");
      return;
    }
    if (activeRun?.status === "running") {
      setStep("run");
      return;
    }
    setStep("setup");
  }, [activeRun, result]);

  return (
    <main className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-[#0B2A34] via-[#0F3743] to-[#1A4A53]">
      <div className="mx-auto w-full max-w-[1680px] space-y-7 p-4 pb-8 lg:p-6">
        <AppDescription
          onPrimaryCta={() => setStep("setup")}
          onSecondaryCta={jumpToResults}
        />
        <FlowStepper current={step} />

        {step === "setup" && (
          <section className="animate-fade-up grid gap-6 xl:grid-cols-[2fr_1fr]">
            <InstrumentSetupForm
              ref={formRef}
              onSubmit={handleSetupSubmit}
              isPending={mutation.isPending}
              threadIdInput={threadIdInput}
              onThreadIdChange={setThreadIdInput}
            />
            <Card className="glass-panel shadow-sm">
              <CardHeader className="border-b border-border/60">
                <CardTitle className="text-base md:text-lg">Run Guidance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-5 text-sm text-muted-foreground">
                <p>
                  Start with precise construct boundaries and constraints. This improves reviewer convergence and
                  reduces revision cycles.
                </p>
                <p>
                  When results are ready, submit human feedback to run a refinement loop with explicit context from
                  the current item set.
                </p>
                {activeRun?.status === "running" && activeRun.threadId && (
                  <div className="rounded-xl border border-accent/35 bg-white/10 p-3 text-xs text-slate-100">
                    <p className="mb-1 flex items-center gap-1 font-semibold">
                      <AlertCircle className="h-3.5 w-3.5 text-accent" />
                      Running session detected
                    </p>
                    <p>Thread ID: {activeRun.threadId}</p>
                    <Button
                      type="button"
                      size="sm"
                      className="mt-2"
                      onClick={() => setStep("run")}
                    >
                      Resume running session
                    </Button>
                  </div>
                )}
                <Button
                  type="button"
                  className="w-full"
                  onClick={() => {
                    if (!submittedSetup) return;
                    handleSetupSubmit(submittedSetup, threadIdInput.trim() || undefined);
                  }}
                  disabled={!submittedSetup || mutation.isPending}
                >
                  <Rocket className="mr-2 h-4 w-4" />
                  Rerun last setup
                </Button>
              </CardContent>
            </Card>
          </section>
        )}

        {step === "run" && (
          <section className="animate-fade-up grid gap-6 lg:grid-cols-[1.2fr_1fr]">
            <div className="space-y-4">
              <ProgressIndicator progress={progress} />
              <Card className="glass-panel shadow-sm">
                <CardHeader className="border-b border-border/60">
                  <CardTitle className="text-base md:text-lg">Running Agent Workflow</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 pt-5 text-sm text-muted-foreground">
                  <p>
                    The system is executing retrieval, drafting, multi-review, and revision stages. This view updates
                    in real time.
                  </p>
                  {activeRun?.threadId && (
                    <p>
                      Active thread: <span className="font-medium text-white">{activeRun.threadId}</span>
                    </p>
                  )}
                  {activeRun?.runId && (
                    <p>
                      Active run: <span className="font-medium text-white">{activeRun.runId}</span>
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
            <div className="space-y-4">
              <SetupSnapshotCard values={submittedSetup} />
              <Button
                type="button"
                variant="secondary"
                className="bg-primary text-white hover:bg-accent hover:text-white"
                onClick={() => setStep("setup")}
                disabled={mutation.isPending}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to setup
              </Button>
            </div>
          </section>
        )}

        {step === "results" && (
          <section className="animate-fade-up grid gap-6 xl:grid-cols-3">
            <div className="space-y-4">
              <SetupSnapshotCard values={submittedSetup} />
              <Button
                type="button"
                variant="secondary"
                className="w-full bg-primary text-white hover:bg-accent hover:text-white"
                onClick={handleStartNew}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Edit setup
              </Button>
            </div>
            <div className="space-y-4">
              <HumanFeedbackPanel
                value={humanFeedback}
                onChange={setHumanFeedback}
                onRefine={handleRefineRun}
                isPending={mutation.isPending}
              />
              <FeedbackHistoryPanel
                entries={feedbackHistory}
                onReuseFeedback={setHumanFeedback}
                onClearHistory={() => setFeedbackHistory([])}
              />
              {result ? (
                <EvidenceAuditPanel audit={result.audit} />
              ) : (
                <Card className="glass-panel shadow-sm">
                  <CardHeader className="border-b border-border/60">
                    <CardTitle className="text-base md:text-lg">Evidence and Audit</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-5">
                    <p className="text-sm text-muted-foreground">Run generation to load evidence and audit details.</p>
                  </CardContent>
                </Card>
              )}
            </div>
            <div className="space-y-4">
              {result ? (
                <GeneratedItemsTable items={result.final_items} fullOutput={result} />
              ) : (
                <Card className="glass-panel shadow-sm">
                  <CardHeader className="border-b border-border/60">
                    <CardTitle className="text-base md:text-lg">Generated Items</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-5">
                    <p className="text-sm text-muted-foreground">No generated items yet.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </section>
        )}

        <DeveloperDrawer requestJson={lastRequestJson} responseJson={lastResponseJson} />
      </div>
    </main>
  );
}
