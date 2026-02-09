"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { useToast } from "@/components/ui/use-toast";
import { InstrumentSetupForm } from "@/components/InstrumentSetupForm";
import { EvidenceAuditPanel } from "@/components/EvidenceAuditPanel";
import { GeneratedItemsTable } from "@/components/GeneratedItemsTable";
import { DeveloperDrawer } from "@/components/DeveloperDrawer";
import { generateItems, formToRequest, GenerateError } from "@/lib/generate";
import type { InstrumentSetupFormValues } from "@/lib/schemas";
import type { FinalOutput } from "@/lib/types";

const LOADING_MESSAGES = [
  "Retrieving evidence…",
  "Drafting items…",
  "Reviewing…",
  "Revising…",
];

export default function HomePage() {
  const { toast } = useToast();
  const formRef = React.useRef<{ setErrorsFromApi: (detail: unknown) => void } | null>(null);
  const [threadIdInput, setThreadIdInput] = React.useState("");
  const [result, setResult] = React.useState<FinalOutput | null>(null);
  const [lastRequestJson, setLastRequestJson] = React.useState<string | null>(null);
  const [lastResponseJson, setLastResponseJson] = React.useState<string | null>(null);
  const [loadingMessageIndex, setLoadingMessageIndex] = React.useState(0);

  const mutation = useMutation({
    mutationFn: generateItems,
    onSuccess: (data) => {
      setResult(data);
      setLastResponseJson(JSON.stringify(data, null, 2));
      toast({ title: "Done", description: "Items generated successfully.", variant: "default" });
    },
    onError: (err: GenerateError) => {
      setLastResponseJson(err.rawText || null);
      if (err.status === 422 && err.detail) {
        formRef.current?.setErrorsFromApi(err.detail);
        toast({
          title: "Validation error",
          description: "Check the form for field-specific messages.",
          variant: "destructive",
        });
      } else {
        const message = err.status >= 500 ? "Server error. Try again later." : err.message;
        toast({ title: "Error", description: message, variant: "destructive" });
      }
    },
  });

  React.useEffect(() => {
    if (!mutation.isPending) return;
    const interval = setInterval(() => {
      setLoadingMessageIndex((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [mutation.isPending]);

  const handleSubmit = React.useCallback(
    (values: InstrumentSetupFormValues, threadId?: string) => {
      const body = formToRequest(values);
      setLastRequestJson(JSON.stringify(body, null, 2));
      setLastResponseJson(null);
      setResult(null);
      mutation.mutate({ body, threadId });
    },
    [mutation]
  );

  return (
    <main className="flex min-h-[calc(100vh-3.5rem)] flex-col">
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 p-4 lg:p-6 max-w-[1800px] mx-auto w-full">
        <section className="lg:col-span-1" aria-label="Instrument setup">
          <InstrumentSetupForm
            ref={formRef}
            onSubmit={handleSubmit}
            isPending={mutation.isPending}
            threadIdInput={threadIdInput}
            onThreadIdChange={setThreadIdInput}
          />
        </section>

        <section className="lg:col-span-1" aria-label="Evidence and audit">
          {mutation.isPending && (
            <div className="rounded-2xl border bg-card p-6 text-center text-muted-foreground">
              <p className="font-medium">{LOADING_MESSAGES[loadingMessageIndex]}</p>
            </div>
          )}
          {result && !mutation.isPending && (
            <EvidenceAuditPanel audit={result.audit} />
          )}
          {!result && !mutation.isPending && (
            <div className="rounded-2xl border bg-card p-6 text-center text-muted-foreground">
              <p>Run a generation to see evidence and audit.</p>
            </div>
          )}
        </section>

        <section className="lg:col-span-1" aria-label="Generated items">
          {mutation.isPending && (
            <div className="rounded-2xl border bg-card p-6 text-center text-muted-foreground">
              <p>Generating items…</p>
            </div>
          )}
          {result && !mutation.isPending && (
            <GeneratedItemsTable
              items={result.final_items}
              fullOutput={result}
            />
          )}
          {!result && !mutation.isPending && (
            <div className="rounded-2xl border bg-card p-6 text-center text-muted-foreground">
              <p>Generated items will appear here.</p>
            </div>
          )}
        </section>
      </div>

      <DeveloperDrawer requestJson={lastRequestJson} responseJson={lastResponseJson} />
    </main>
  );
}
