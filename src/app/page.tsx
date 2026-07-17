"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertCircle, ArrowLeft, Rocket } from "lucide-react";
import { AppDescription } from "@/components/AppDescription";
import { DeveloperDrawer } from "@/components/DeveloperDrawer";
import { EmptyPanel } from "@/components/EmptyPanel";
import { EvidenceAuditPanel } from "@/components/EvidenceAuditPanel";
import { FeedbackHistoryPanel } from "@/components/FeedbackHistoryPanel";
import { GeneratedItemsTable } from "@/components/GeneratedItemsTable";
import { HumanFeedbackPanel } from "@/components/HumanFeedbackPanel";
import { PFAPanel } from "@/components/PFAPanel";
import { SyntheticPilotPanel } from "@/components/SyntheticPilotPanel";
import { QualitativeQuestionsPanel } from "@/components/QualitativeQuestionsPanel";
import { ExpertPanelCard } from "@/components/ExpertPanelCard";
import { PersonaValidationCard } from "@/components/PersonaValidationCard";
import { InstrumentSetupForm } from "@/components/InstrumentSetupForm";
import { ProgressIndicator, type CompletedNode, type ProgressState } from "@/components/ProgressIndicator";
import { SetupSnapshotCard } from "@/components/SetupSnapshotCard";
import { CorrelationPanel } from "@/components/CorrelationPanel";
import { ComparisonPanel } from "@/components/ComparisonPanel";
import { Stepper } from "@/components/Stepper";
import { PrimaryButton } from "@/components/ui/action-buttons";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InsetPanel, SurfaceCard } from "@/components/ui/surface-card";
import { useToast } from "@/components/ui/use-toast";
import { type ProgressEvent } from "@/lib/api";
import { formToRequest, generateItemsStream, GenerateError } from "@/lib/generate";
import type { InstrumentSetupFormValues } from "@/lib/schemas";
import type { FinalOutput, UserRequest } from "@/lib/types";
import { useRunRecovery } from "@/hooks/useRunRecovery";
import { useSessionPersistence, type RunKind } from "@/hooks/useSessionPersistence";

function deriveRunKind(request: UserRequest): RunKind {
  return (request.previous_items?.length ?? 0) > 0 ? "refinement" : "setup";
}

export default function HomePage() {
  const { toast } = useToast();
  const formRef = React.useRef<{ setErrorsFromApi: (detail: unknown) => void } | null>(null);
  const {
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
  } = useSessionPersistence();
  const [progress, setProgress] = React.useState<ProgressState>({
    currentNode: null,
    displayName: null,
    iteration: 0,
    status: "idle",
  });
  const [completedNodes, setCompletedNodes] = React.useState<CompletedNode[]>([]);
  const [logs, setLogs] = React.useState<ProgressEvent[]>([]);
  const [useChatGPT, setUseChatGPT] = React.useState(false);

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
          if (event.type === "log") {
            // Handle log events
            setLogs((prev) => [...prev, event]);
            return;
          }

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
            setCompletedNodes([]);
            setLogs([]); // Clear logs on new run
          } else if (event.type === "node_start") {
            // Push the previous current node into completed list
            setProgress((prev) => {
              if (prev.currentNode) {
                const completedEntry = {
                  node: prev.currentNode,
                  displayName: prev.displayName || prev.currentNode,
                  iteration: prev.iteration,
                  timestamp: Date.now(),
                };
                setCompletedNodes((nodes) => {
                  // Dedup: check ALL entries, not just last
                  if (nodes.some(n => n.node === completedEntry.node && n.iteration === completedEntry.iteration)) {
                    return nodes;
                  }
                  return [...nodes, completedEntry];
                });
              }
              return {
                ...prev,
                currentNode: event.node || null,
                displayName: event.display_name || null,
                iteration: event.iteration || prev.iteration,
                status: "running",
              };
            });
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
      toast({ title: "Done", description: "Items generated successfully.", variant: "success" });
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
    setCompletedNodes([]);
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
      setUseChatGPT(values.use_chatgpt_critics);
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

  const handleClearResults = React.useCallback(() => {
    setResult(null);
    setHumanFeedback("");
    setFeedbackHistory([]);
    setActiveRun(null);
    setLastResponseJson(null);
    setLastRequestJson(null);
    resetProgress();
    setStep("setup");
  }, [resetProgress]);

  useRunRecovery({
    hasRestored,
    activeRun,
    isMutationPending: mutation.isPending,
    appendHistoryEntry,
    toast,
    setStep,
    setProgress,
    setActiveRun,
    setResult,
    setThreadIdInput,
    setLastResponseJson,
  });

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
    <main className="min-h-[calc(100vh-4rem)] bg-app-gradient">
      <div className="mx-auto w-full max-w-[1680px] space-y-7 p-4 pb-8 lg:p-6">
        <AppDescription
          onPrimaryCta={() => setStep("setup")}
          onSecondaryCta={jumpToResults}
          onClearResults={handleClearResults}
          showClearButton={result !== null}
        />
        <Stepper current={step} />

        {step === "setup" && (
          <section className="animate-fade-up grid gap-6 xl:grid-cols-[2fr_1fr]">
            <InstrumentSetupForm
              ref={formRef}
              onSubmit={handleSetupSubmit}
              isPending={mutation.isPending}
              threadIdInput={threadIdInput}
              onThreadIdChange={setThreadIdInput}
            />
            <SurfaceCard className="border-cyan-300/70">
              <CardHeader className="border-b border-border/60">
                <CardTitle className="text-base md:text-lg">Run Guidance</CardTitle>
              </CardHeader>
              <CardContent className="pt-5 text-sm text-muted-foreground">
                <InsetPanel className="space-y-4 rounded-2xl p-4">
                  <p>
                    Start with precise construct boundaries and constraints. This improves reviewer convergence and
                    reduces revision cycles.
                  </p>
                  <p>
                    When results are ready, submit human feedback to run a refinement loop with explicit context from
                    the current item set.
                  </p>
                  {activeRun?.status === "running" && activeRun.threadId && (
                    <InsetPanel className="rounded-xl p-3 text-xs text-slate-100">
                      <p className="mb-1 flex items-center gap-1 font-semibold">
                        <AlertCircle className="h-3.5 w-3.5 text-accent" />
                        Running session detected
                      </p>
                      <p>Thread ID: {activeRun.threadId}</p>
                      <PrimaryButton
                        type="button"
                        size="sm"
                        className="mt-2"
                        onClick={() => setStep("run")}
                      >
                        Resume running session
                      </PrimaryButton>
                    </InsetPanel>
                  )}
                  <PrimaryButton
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
                  </PrimaryButton>
                </InsetPanel>
              </CardContent>
            </SurfaceCard>
          </section>
        )}

        {step === "run" && (
          <section className="animate-fade-up grid gap-6 lg:grid-cols-[1.2fr_1fr]">
            <div className="space-y-4">
              <ProgressIndicator progress={progress} logs={logs} useChatGPT={useChatGPT} completedNodes={completedNodes} />
            </div>
            <div className="space-y-4">
              <SetupSnapshotCard values={submittedSetup} />
              <PrimaryButton
                type="button"
                onClick={() => setStep("setup")}
                disabled={mutation.isPending}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to setup
              </PrimaryButton>
            </div>
          </section>
        )}

        {step === "results" && (
          <section className="animate-fade-up space-y-6">
            {/* Full-width setup snapshot bar (Edit button inside card) */}
            <SetupSnapshotCard values={submittedSetup} horizontal onEditSetup={handleStartNew} />

            {/* Persona-based ambiguity detection (collapsed by default) */}
            {result && result.persona_validation && (
              <PersonaValidationCard validation={result.persona_validation} />
            )}

            {/* 2-column main content: 60/40 split */}
            <div className="grid gap-6 xl:grid-cols-[3fr_2fr]">
              {/* Left (60%): Generated items + Correlation */}
              <div className="space-y-4">
                {result ? (
                  <GeneratedItemsTable items={result.final_items} fullOutput={result} />
                ) : (
                  <EmptyPanel title="Generated Items">No generated items yet.</EmptyPanel>
                )}

                {/* Qualitative interview probes (opt-in) */}
                {result && result.qualitative_questions && result.qualitative_questions.length > 0 && (
                  <QualitativeQuestionsPanel questions={result.qualitative_questions} />
                )}

                {/* Correlation Analysis — directly under items */}
                {result && result.correlation_matrix ? (
                  <CorrelationPanel
                    matrix={result.correlation_matrix}
                    itemTexts={result.final_items.map(item => item.item_text)}
                    constructName={result.final_items[0]?.construct_name}
                    defaultExpanded
                  />
                ) : (
                  <EmptyPanel title="Correlation Analysis" className="border-lime-300/70">
                    {result && result.final_items.length >= 3
                      ? "Correlation analytics did not complete for this run."
                      : "Requires 3+ items for correlation analysis."}
                  </EmptyPanel>
                )}
              </div>

              {/* Right (40%): Feedback + Comparison + Evidence + History */}
              <div className="space-y-4">
                <HumanFeedbackPanel
                  value={humanFeedback}
                  onChange={setHumanFeedback}
                  onRefine={handleRefineRun}
                  isPending={mutation.isPending}
                />

                {/* Expert face/content validity panel */}
                {result && result.expert_consensus && (
                  <ExpertPanelCard consensus={result.expert_consensus} />
                )}

                {/* Instrument Comparison (moved from bottom analytics row) */}
                {result && result.comparison_instruments && result.comparison_instruments.length >= 2 ? (
                  <ComparisonPanel
                    convergentInstrument={result.comparison_instruments[0]}
                    discriminantInstrument={result.comparison_instruments[1]}
                    convergentScore={result.convergent_validity_score ?? null}
                    crossConstruct={result.cross_construct_analysis}
                    defaultExpanded
                  />
                ) : (
                  <EmptyPanel title="Instrument Comparison" className="border-lime-300/70">
                    {result && result.final_items.length >= 3
                      ? "Instrument comparison did not complete for this run."
                      : "Requires 3+ items for instrument comparison analytics."}
                  </EmptyPanel>
                )}

                {result ? (
                  <EvidenceAuditPanel audit={result.audit} />
                ) : (
                  <EmptyPanel title="Evidence and Audit">Run generation to load evidence and audit details.</EmptyPanel>
                )}

                <FeedbackHistoryPanel
                  entries={feedbackHistory}
                  onReuseFeedback={setHumanFeedback}
                  onClearHistory={() => setFeedbackHistory([])}
                />
              </div>
            </div>

            {/* Pseudo-Factor Analysis full-width row (centerpiece structural result) */}
            {result && result.pfa_result && result.pfa_result.loadings.length > 0 && (
              <PFAPanel
                pfa={result.pfa_result}
                egaSemantic={result.ega_semantic}
                egaSynthetic={result.ega_synthetic}
                itemTexts={result.final_items.map(item => item.item_text)}
              />
            )}

            {/* Synthetic-respondent pilot full-width row (flag-gated, simulated data) */}
            {result && result.synthetic_pilot && (
              <SyntheticPilotPanel
                pilot={result.synthetic_pilot}
                itemTexts={result.final_items.map(item => item.item_text)}
              />
            )}

          </section>
        )}

        {process.env.NODE_ENV === "development" && (
          <DeveloperDrawer requestJson={lastRequestJson} responseJson={lastResponseJson} />
        )}
      </div>
    </main>
  );
}
