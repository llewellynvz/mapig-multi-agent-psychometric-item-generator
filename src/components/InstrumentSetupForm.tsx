"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { UseFormSetError } from "react-hook-form";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PrimaryButton, SecondaryButton } from "@/components/ui/action-buttons";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InsetPanel, SurfaceCard } from "@/components/ui/surface-card";
import { Textarea } from "@/components/ui/textarea";
import { TagInput } from "@/components/TagInput";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/components/ui/use-toast";
import {
  instrumentSetupSchema,
  type InstrumentSetupFormValues,
  defaultInstrumentSetup,
  RESPONSE_SCALE_PRESETS,
  LANGUAGE_PRESETS,
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
  console.log("[MAPIG] Validation error detail received:", detail);
  console.log("[MAPIG] Detail type:", typeof detail, "isArray:", Array.isArray(detail));

  // Handle single error object (not in array)
  if (!Array.isArray(detail) && typeof detail === "object" && detail !== null) {
    const errorObj = detail as { type?: string; msg?: string; loc?: unknown };
    console.log("[MAPIG] Single error object (not array):", errorObj);

    const loc = errorObj.loc;
    const msg = errorObj.msg ?? "Validation error";

    // Try to extract field name from loc
    if (Array.isArray(loc) && loc.length >= 2 && loc[0] === "body") {
      const field = loc[1] as keyof InstrumentSetupFormValues;
      console.log(`[MAPIG] Setting error on field "${field}":`, msg);
      setError(field, { type: "server", message: String(msg) });
      return;
    } else if (Array.isArray(loc) && loc.length >= 1) {
      const field = loc[0] as keyof InstrumentSetupFormValues;
      if (field in defaultInstrumentSetup) {
        console.log(`[MAPIG] Setting error on field "${field}" (fallback):`, msg);
        setError(field, { type: "server", message: String(msg) });
        return;
      }
    }

    // No field location found, set generic error
    console.warn("[MAPIG] No field location in single error object, setting generic error");
    setError("construct_name", {
      type: "server",
      message: String(msg)
    });
    return;
  }

  // Handle string errors
  if (typeof detail === "string") {
    console.log("[MAPIG] String error:", detail);
    setError("construct_name", {
      type: "server",
      message: detail
    });
    return;
  }

  // Handle array format (multiple errors)
  if (!Array.isArray(detail)) {
    console.error("[MAPIG] Unexpected validation error format:", detail);
    setError("construct_name", {
      type: "server",
      message: "Validation error occurred. Please check your inputs."
    });
    return;
  }

  // Parse array of validation errors
  let errorCount = 0;
  for (const item of detail) {
    console.log("[MAPIG] Processing error item:", item);
    const loc = item?.loc;
    const msg = item?.msg ?? "Validation error";

    // Handle errors with proper location
    if (Array.isArray(loc) && loc.length >= 2 && loc[0] === "body") {
      const field = loc[1] as keyof InstrumentSetupFormValues;
      console.log(`[MAPIG] Setting error on field "${field}":`, msg);
      setError(field, { type: "server", message: String(msg) });
      errorCount++;
    } else if (Array.isArray(loc) && loc.length >= 1) {
      // Fallback: try first element as field name
      const field = loc[0] as keyof InstrumentSetupFormValues;
      if (field in defaultInstrumentSetup) {
        console.log(`[MAPIG] Setting error on field "${field}" (fallback):`, msg);
        setError(field, { type: "server", message: String(msg) });
        errorCount++;
      } else {
        console.warn(`[MAPIG] Field "${field}" not found in schema, skipping`);
      }
    } else {
      console.warn("[MAPIG] Invalid loc format:", loc);
    }
  }

  console.log(`[MAPIG] Total errors set: ${errorCount}/${detail.length}`);

  // If no errors were set, log warning and set a fallback error
  if (errorCount === 0) {
    console.warn("[MAPIG] No field errors could be mapped from validation response:", detail);
    setError("construct_name", {
      type: "server",
      message: "Validation error occurred. Please check your inputs."
    });
  }
}

export const InstrumentSetupForm = React.forwardRef<InstrumentSetupFormRef, InstrumentSetupFormProps>(function InstrumentSetupForm({
  onSubmit,
  isPending = false,
  threadIdInput = "",
  onThreadIdChange,
}, ref) {
  const { toast } = useToast();
  const form = useForm<InstrumentSetupFormValues>({
    resolver: zodResolver(instrumentSetupSchema),
    defaultValues: defaultInstrumentSetup,
  });

  React.useEffect(() => {
    const saved = loadFromStorage();
    if (!saved) return;
    const savedItemCount = Number(saved.item_count ?? 10);

    form.reset({
      ...defaultInstrumentSetup,
      construct_name: saved.construct_name ?? "",
      construct_definition: saved.construct_definition ?? "",
      target_population: saved.target_population ?? "",
      response_scale: saved.response_scale ?? defaultInstrumentSetup.response_scale,
      item_count: Number.isFinite(savedItemCount) ? Math.max(2, savedItemCount) : 10,
      constraints: Array.isArray(saved.constraints) ? saved.constraints : [...DEFAULT_CONSTRAINTS],
      cultural_group: saved.cultural_group ?? "",
      construct_exclusions: saved.construct_exclusions ?? "",
      language: saved.language ?? "English",
      native_construct: saved.native_construct ?? "",
      example_item: saved.example_item ?? "",
      approved_domains: Array.isArray(saved.approved_domains) ? saved.approved_domains : [...DEFAULT_APPROVED_DOMAINS],
    });
  }, [form]);

  React.useImperativeHandle(ref, () => ({
    setErrorsFromApi(detail: unknown) {
      setErrorsFromDetail(form.setError, detail);
    },
  }));

  const handleGPT52Toggle = (checked: boolean) => {
    form.setValue("use_gpt52_analytics", checked);
    if (checked) {
      toast({
        title: "GPT-5.2 Analytics Enabled",
        description: "Reasoning models use 4-6x more tokens than standard models. Estimated additional cost: ~$1.50-$3.00 per run.",
        variant: "default",
        duration: 5000,
      });
    }
  };

  const submitValues = React.useCallback((values: InstrumentSetupFormValues) => {
    saveToStorage(values);
    const threadId = threadIdInput.trim() || undefined;
    onSubmit(values, threadId);
  }, [onSubmit, threadIdInput]);

  const handleSubmit = React.useCallback(
    (event?: React.BaseSyntheticEvent) => {
      if (event) {
        event.preventDefault();
      }
      void form.handleSubmit(submitValues)(event);
    },
    [form, submitValues]
  );

  const handleReset = () => {
    form.reset(defaultInstrumentSetup);
    onThreadIdChange?.("");
  };

  const responseScale = form.watch("response_scale");
  const isPresetResponseScale = RESPONSE_SCALE_PRESETS.includes(
    responseScale as (typeof RESPONSE_SCALE_PRESETS)[number]
  );

  return (
    <SurfaceCard className="border-cyan-300/70">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-base md:text-lg">Instrument Setup</CardTitle>
      </CardHeader>
      <CardContent className="pt-5">
        <InsetPanel className="space-y-6 rounded-2xl p-4">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="construct_name">Construct name (required)</Label>
              <Input
                id="construct_name"
                placeholder="e.g. Workplace belonging"
                {...form.register("construct_name")}
              />
              {form.formState.errors.construct_name && (
                <p className="text-sm font-medium text-accent">
                  {form.formState.errors.construct_name.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="construct_definition">
                Construct definition (required, min 10 chars)
              </Label>
              <Textarea
                id="construct_definition"
                placeholder="Operational definition of the construct..."
                rows={4}
                {...form.register("construct_definition")}
              />
              {form.formState.errors.construct_definition && (
                <p className="text-sm font-medium text-accent">
                  {form.formState.errors.construct_definition.message}
                </p>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="target_population">Target population (required)</Label>
                <Input
                  id="target_population"
                  placeholder="e.g. Full-time employees in hybrid work"
                  {...form.register("target_population")}
                />
                {form.formState.errors.target_population && (
                  <p className="text-sm font-medium text-accent">
                    {form.formState.errors.target_population.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="cultural_group">Cultural / Regional Group</Label>
                <Input
                  id="cultural_group"
                  placeholder="e.g. South African, Zulu, East Asian"
                  {...form.register("cultural_group")}
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="response_scale">Response scale</Label>
                <select
                  id="response_scale"
                  className="flex h-10 w-full items-center justify-between rounded-2xl border px-3 py-2 text-sm ring-offset-background focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  style={{
                    background: 'rgba(255, 255, 255, 0.08)',
                    borderColor: 'rgba(167, 209, 43, 0.32)',
                    color: 'var(--color-text)',
                  }}
                  value={isPresetResponseScale ? responseScale : "__custom__"}
                  onChange={(e) => form.setValue("response_scale", e.target.value === "__custom__" ? "" : e.target.value)}
                >
                  <option value="" disabled style={{ background: '#123f4a', color: '#f8fbfc' }}>
                    Select scale
                  </option>
                  {RESPONSE_SCALE_PRESETS.map((preset) => (
                    <option key={preset} value={preset} style={{ background: '#123f4a', color: '#f8fbfc' }}>
                      {preset}
                    </option>
                  ))}
                  <option value="__custom__" style={{ background: '#123f4a', color: '#f8fbfc' }}>Custom (enter below)</option>
                </select>
                {!isPresetResponseScale && (
                  <Input
                    placeholder="Enter custom response scale"
                    value={responseScale}
                    onChange={(e) => form.setValue("response_scale", e.target.value)}
                  />
                )}
                {form.formState.errors.response_scale && (
                  <p className="text-sm font-medium text-accent">
                    {form.formState.errors.response_scale.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <select
                  id="language"
                  className="flex h-10 w-full items-center justify-between rounded-2xl border px-3 py-2 text-sm ring-offset-background focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  style={{
                    background: 'rgba(255, 255, 255, 0.08)',
                    borderColor: 'rgba(167, 209, 43, 0.32)',
                    color: 'var(--color-text)',
                  }}
                  value={form.watch("language")}
                  onChange={(e) => form.setValue("language", e.target.value)}
                >
                  {LANGUAGE_PRESETS.map((lang) => (
                    <option key={lang} value={lang} style={{ background: '#123f4a', color: '#f8fbfc' }}>
                      {lang}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="item_count">Item count (2–50)</Label>
              <Input
                id="item_count"
                type="number"
                min={2}
                max={50}
                {...form.register("item_count", { valueAsNumber: true })}
              />
              {form.formState.errors.item_count && (
                <p className="text-sm font-medium text-accent">
                  {form.formState.errors.item_count.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4">
                <div className="space-y-1">
                  <Label htmlFor="is_unidimensional" className="cursor-pointer">Construct structure</Label>
                  <p className="text-xs text-muted-foreground mr-6">
                    {form.watch("is_unidimensional") ? (
                      <>
                        <span className="font-medium text-white">Unidimensional</span> — Items measure a single construct. Sub-constructs from literature flagged for separate runs.
                      </>
                    ) : (
                      <>
                        <span className="font-medium text-white">Multi-dimensional</span> — Items distributed across sub-constructs/facets identified in the literature.
                      </>
                    )}
                  </p>
                </div>
                <Switch
                  id="is_unidimensional"
                  checked={form.watch("is_unidimensional")}
                  onCheckedChange={(checked) => form.setValue("is_unidimensional", checked)}
                  className="data-[state=checked]:bg-[#008da1] data-[state=unchecked]:bg-[#b1dd0c]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4">
                <div className="space-y-1">
                  <Label htmlFor="include_qualitative" className="cursor-pointer">Qualitative questions</Label>
                  <p className="text-xs text-muted-foreground mr-6">
                    {form.watch("include_qualitative") ? (
                      <>
                        <span className="font-medium text-white">Included</span> — Also generates open-ended interview probes for construct pre-testing.
                      </>
                    ) : (
                      <>
                        <span className="font-medium text-white">Off</span> — Quantitative items only.
                      </>
                    )}
                  </p>
                </div>
                <Switch
                  id="include_qualitative"
                  checked={form.watch("include_qualitative")}
                  onCheckedChange={(checked) => form.setValue("include_qualitative", checked)}
                  className="data-[state=checked]:bg-[#008da1] data-[state=unchecked]:bg-[#b1dd0c]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4">
                <div className="space-y-1">
                  <Label htmlFor="use_chatgpt_critics" className="cursor-pointer">Critic Model</Label>
                  <p className="text-xs text-muted-foreground mr-6">
                    {form.watch("use_chatgpt_critics") ? (
                      <>
                        <span className="font-medium text-white">ChatGPT 5.2</span> — Critics, validators, and reviewers use OpenAI for cost savings. Item writer always uses Claude Sonnet.
                      </>
                    ) : (
                      <>
                        <span className="font-medium text-white">Claude</span> — All agents use Claude models (Opus/Sonnet). Item writer uses Claude Sonnet.
                      </>
                    )}
                  </p>
                </div>
                <Switch
                  id="use_chatgpt_critics"
                  checked={form.watch("use_chatgpt_critics")}
                  onCheckedChange={(checked) => form.setValue("use_chatgpt_critics", checked)}
                  className="data-[state=checked]:bg-[#008da1] data-[state=unchecked]:bg-[#b1dd0c]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4">
                <div className="space-y-1">
                  <Label htmlFor="use_gpt52_analytics" className="cursor-pointer">Analytics Model</Label>
                  <p className="text-xs text-muted-foreground mr-6">
                    {form.watch("use_gpt52_analytics") ? (
                      <>
                        <span className="font-medium text-white">GPT-5.2</span> — Reasoning models for higher accuracy analytics (4-6x cost)
                      </>
                    ) : (
                      <>
                        <span className="font-medium text-white">Standard</span> — Claude Sonnet for analytics (lower cost)
                      </>
                    )}
                  </p>
                </div>
                <Switch
                  id="use_gpt52_analytics"
                  checked={form.watch("use_gpt52_analytics")}
                  onCheckedChange={handleGPT52Toggle}
                  className="data-[state=checked]:bg-[#008da1] data-[state=unchecked]:bg-[#b1dd0c]"
                />
              </div>
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
              <Label htmlFor="construct_exclusions">Construct boundary / overlap exclusions (optional)</Label>
              <Textarea
                id="construct_exclusions"
                placeholder="Describe what this construct is NOT, and nearby constructs/items that should be avoided."
                rows={3}
                {...form.register("construct_exclusions")}
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
              <PrimaryButton type="button" disabled={isPending} onClick={() => handleSubmit()}>
                {isPending ? "Generating…" : "Generate items"}
              </PrimaryButton>
              <PrimaryButton
                type="button"
                onClick={handleReset}
                disabled={isPending}
              >
                Reset
              </PrimaryButton>
            </div>
          </form>
        </InsetPanel>
      </CardContent>
    </SurfaceCard>
  );
});
