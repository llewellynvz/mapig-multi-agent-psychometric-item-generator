"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { UseFormSetError } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { TagInput } from "@/components/TagInput";
import {
  instrumentSetupSchema,
  type InstrumentSetupFormValues,
  defaultInstrumentSetup,
  RESPONSE_SCALE_PRESETS,
  DEFAULT_CONSTRAINTS,
  DEFAULT_APPROVED_DOMAINS,
} from "@/lib/schemas";

const STORAGE_KEY = "mapig-instrument-setup";

function loadFromStorage(): Partial<InstrumentSetupFormValues> | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<InstrumentSetupFormValues>;
    return parsed;
  } catch {
    return null;
  }
}

function saveToStorage(values: InstrumentSetupFormValues) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(values));
  } catch {
    // ignore
  }
}

export interface InstrumentSetupFormRef {
  setErrorsFromApi: (detail: unknown) => void;
}

export interface InstrumentSetupFormProps {
  onSubmit: (values: InstrumentSetupFormValues, threadId?: string) => void;
  isPending?: boolean;
  threadIdInput?: string;
  onThreadIdChange?: (value: string) => void;
}

function setErrorsFromDetail(setError: UseFormSetError<InstrumentSetupFormValues>, detail: unknown) {
  if (!Array.isArray(detail)) return;
  for (const item of detail) {
    const loc = item?.loc;
    const msg = item?.msg ?? "Validation error";
    if (Array.isArray(loc) && loc.length >= 2 && loc[0] === "body") {
      const field = loc[1] as keyof InstrumentSetupFormValues;
      setError(field, { type: "server", message: String(msg) });
    }
  }
}

export const InstrumentSetupForm = React.forwardRef<InstrumentSetupFormRef, InstrumentSetupFormProps>(function InstrumentSetupForm({
  onSubmit,
  isPending = false,
  threadIdInput = "",
  onThreadIdChange,
}, ref) {
  const saved = loadFromStorage();
  const defaultValues: InstrumentSetupFormValues = {
    ...defaultInstrumentSetup,
    ...(saved && {
      construct_name: saved.construct_name ?? "",
      construct_definition: saved.construct_definition ?? "",
      target_population: saved.target_population ?? "",
      response_scale: saved.response_scale ?? defaultInstrumentSetup.response_scale,
      item_count: saved.item_count ?? 10,
      constraints: Array.isArray(saved.constraints) ? saved.constraints : DEFAULT_CONSTRAINTS,
      native_construct: saved.native_construct ?? "",
      example_item: saved.example_item ?? "",
      approved_domains: Array.isArray(saved.approved_domains) ? saved.approved_domains : DEFAULT_APPROVED_DOMAINS,
    }),
  };

  const form = useForm<InstrumentSetupFormValues>({
    resolver: zodResolver(instrumentSetupSchema),
    defaultValues,
  });

  React.useImperativeHandle(ref, () => ({
    setErrorsFromApi(detail: unknown) {
      setErrorsFromDetail(form.setError, detail);
    },
  }));

  const handleSubmit = form.handleSubmit((values) => {
    saveToStorage(values);
    const threadId = threadIdInput.trim() || undefined;
    onSubmit(values, threadId);
  });

  const handleReset = () => {
    form.reset(defaultInstrumentSetup);
    onThreadIdChange?.("");
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Instrument Setup</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="construct_name">Construct name (required)</Label>
            <Input
              id="construct_name"
              placeholder="e.g. Workplace belonging"
              {...form.register("construct_name")}
            />
            {form.formState.errors.construct_name && (
              <p className="text-sm text-destructive">
                {form.formState.errors.construct_name.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="construct_definition">
              Construct definition (required, min 30 chars)
            </Label>
            <Textarea
              id="construct_definition"
              placeholder="Operational definition of the construct..."
              rows={4}
              {...form.register("construct_definition")}
            />
            {form.formState.errors.construct_definition && (
              <p className="text-sm text-destructive">
                {form.formState.errors.construct_definition.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="target_population">Target population (required)</Label>
            <Input
              id="target_population"
              placeholder="e.g. Full-time employees in hybrid work"
              {...form.register("target_population")}
            />
            {form.formState.errors.target_population && (
              <p className="text-sm text-destructive">
                {form.formState.errors.target_population.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="response_scale">Response scale</Label>
            <select
              id="response_scale"
              className="flex h-10 w-full items-center justify-between rounded-2xl border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={RESPONSE_SCALE_PRESETS.includes(form.watch("response_scale") as (typeof RESPONSE_SCALE_PRESETS)[number]) ? form.watch("response_scale") : "__custom__"}
              onChange={(e) => form.setValue("response_scale", e.target.value === "__custom__" ? "" : e.target.value)}
            >
              <option value="" disabled>
                Select scale
              </option>
              {RESPONSE_SCALE_PRESETS.map((preset) => (
                <option key={preset} value={preset}>
                  {preset}
                </option>
              ))}
              <option value="__custom__">Custom (enter below)</option>
            </select>
            {!RESPONSE_SCALE_PRESETS.includes(form.watch("response_scale") as (typeof RESPONSE_SCALE_PRESETS)[number]) && (
              <Input
                placeholder="Enter custom response scale"
                value={form.watch("response_scale")}
                onChange={(e) => form.setValue("response_scale", e.target.value)}
              />
            )}
            {form.formState.errors.response_scale && (
              <p className="text-sm text-destructive">
                {form.formState.errors.response_scale.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="item_count">Item count (10–50)</Label>
            <Input
              id="item_count"
              type="number"
              min={10}
              max={50}
              {...form.register("item_count", { valueAsNumber: true })}
            />
            {form.formState.errors.item_count && (
              <p className="text-sm text-destructive">
                {form.formState.errors.item_count.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Constraints</Label>
            <TagInput
              value={form.watch("constraints")}
              onChange={(v) => form.setValue("constraints", v)}
              placeholder="Add constraint..."
              aria-label="Constraints"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="native_construct">Native construct (optional)</Label>
            <Input
              id="native_construct"
              placeholder="Optional native-language label"
              {...form.register("native_construct")}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="example_item">Example item (optional)</Label>
            <Input
              id="example_item"
              placeholder="e.g. I feel like I belong in my team."
              {...form.register("example_item")}
            />
          </div>

          <div className="space-y-2">
            <Label>Approved domains (optional)</Label>
            <p className="text-xs text-muted-foreground">
              Restrict Perplexity search to these domains. Add or remove as needed.
            </p>
            <TagInput
              value={form.watch("approved_domains")}
              onChange={(v) => form.setValue("approved_domains", v)}
              placeholder="e.g. doi.org"
              aria-label="Approved domains"
            />
          </div>

          {onThreadIdChange && (
            <div className="space-y-2">
              <Label htmlFor="thread_id">Resume thread (X-Thread-ID)</Label>
              <Input
                id="thread_id"
                placeholder="Paste thread ID to resume"
                value={threadIdInput}
                onChange={(e) => onThreadIdChange(e.target.value)}
                aria-label="Thread ID for resume"
              />
            </div>
          )}

          <div className="flex flex-wrap gap-3 pt-4">
            <Button type="submit" disabled={isPending}>
              {isPending ? "Generating…" : "Generate items"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleReset}
              disabled={isPending}
            >
              Reset
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
});
