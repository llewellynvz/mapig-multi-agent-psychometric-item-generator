"use client";

import * as React from "react";
import { ChevronDown, ChevronRight, Download, Pencil } from "lucide-react";
import { PrimaryButton } from "@/components/ui/action-buttons";
import { CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pill } from "@/components/ui/pill";
import { InsetPanel, SurfaceCard } from "@/components/ui/surface-card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import type { FinalItem, FinalOutput, ItemValidation } from "@/lib/types";
import { exportToCsv, exportToJson, exportToMarkdown, generateFilename } from "@/lib/export";
import { QualityChecksPanel } from "./QualityChecksPanel";

function ValidationScoreDisplay({ validation }: { validation: ItemValidation }) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <div className="validation-score mt-2">
      <div className="flex items-center gap-2">
        <span className={`font-semibold ${validation.accept ? 'text-green-600' : 'text-red-600'}`}>
          Score: {validation.weighted_score.toFixed(2)}/10
        </span>
        <span className={`px-2 py-1 rounded text-sm ${validation.accept ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {validation.accept ? 'Accepted' : 'Rejected'}
        </span>
        {validation.attempt > 1 && (
          <span className="text-sm text-gray-600">
            (Attempt {validation.attempt})
          </span>
        )}
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-sm text-blue-600 hover:underline"
        >
          {expanded ? 'Hide details' : 'Show reasoning'}
        </button>
      </div>

      {expanded && (
        <div className="mt-2 space-y-2 text-sm">
          {validation.dimension_scores.map((dim, idx) => (
            <div key={idx} className="border-l-2 border-gray-300 pl-3">
              <div className="font-medium">
                {dim.dimension.charAt(0).toUpperCase() + dim.dimension.slice(1)}: {dim.score}/10
              </div>
              <div className="text-gray-700 italic">
                {dim.reasoning}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export interface GeneratedItemsTableProps {
  items: FinalItem[];
  fullOutput?: FinalOutput | null;
  onItemsChange?: (items: FinalItem[]) => void;
}

export function GeneratedItemsTable({ items, fullOutput, onItemsChange }: GeneratedItemsTableProps) {
  const { toast } = useToast();
  const [editedItems, setEditedItems] = React.useState<FinalItem[]>(items);
  const [editingIndex, setEditingIndex] = React.useState<number | null>(null);
  const [expandedRationale, setExpandedRationale] = React.useState<Set<number>>(new Set());
  const [selectedFormat, setSelectedFormat] = React.useState<'csv' | 'json' | 'markdown'>('csv');

  React.useEffect(() => {
    setEditedItems(items);
  }, [items]);

  // Load format preference from localStorage on mount
  React.useEffect(() => {
    if (typeof window === 'undefined') return; // SSR guard
    try {
      const saved = localStorage.getItem('mapig-export-format');
      if (saved && ['csv', 'json', 'markdown'].includes(saved)) {
        setSelectedFormat(saved as 'csv' | 'json' | 'markdown');
      }
    } catch {
      // Ignore localStorage errors (private browsing, quota exceeded)
    }
  }, []);

  const handleEdit = (index: number, newText: string) => {
    const next = [...editedItems];
    next[index] = { ...next[index], item_text: newText };
    setEditedItems(next);
    onItemsChange?.(next);
    setEditingIndex(null);
  };

  const displayItems = onItemsChange ? editedItems : items;

  const copyItemsOnly = () => {
    const text = displayItems.map((i) => i.item_text).join("\n");
    navigator.clipboard.writeText(text).then(
      () => toast({ title: "Copied", description: "Items copied to clipboard." }),
      () => toast({ title: "Copy failed", description: "Could not copy." })
    );
  };

  const payload = fullOutput ?? { final_items: displayItems, audit: {} };

  const copyFullOutput = () => {
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2)).then(
      () => toast({ title: "Copied", description: "Full output copied." }),
      () => toast({ title: "Copy failed", description: "Could not copy." })
    );
  };

  const handleFormatChange = (format: 'csv' | 'json' | 'markdown') => {
    setSelectedFormat(format);
    try {
      localStorage.setItem('mapig-export-format', format);
    } catch {
      // Ignore errors
    }
  };

  const handleDownload = () => {
    if (!fullOutput) return;

    const content = selectedFormat === 'csv'
      ? exportToCsv(fullOutput)
      : selectedFormat === 'json'
      ? exportToJson(fullOutput)
      : exportToMarkdown(fullOutput);

    const mimeTypes = {
      csv: 'text/csv;charset=utf-8',
      json: 'application/json;charset=utf-8',
      markdown: 'text/markdown;charset=utf-8'
    };

    const extension = selectedFormat === 'markdown' ? 'md' : selectedFormat;
    const filename = generateFilename(
      fullOutput.final_items[0]?.construct_name ?? 'items',
      extension
    );

    const blob = new Blob([content], { type: mimeTypes[selectedFormat] });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url); // Clean up memory
  };

  const toggleRationale = (index: number) => {
    setExpandedRationale((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  return (
    <SurfaceCard className="border-lime-300/70">
      <CardHeader className="flex flex-col items-center gap-3 border-b border-border/60 md:flex-row md:items-center md:justify-between">
        <CardTitle className="text-base md:text-lg">Generated Items</CardTitle>
        <div className="flex flex-wrap justify-center gap-2 md:justify-end">
          <PrimaryButton
            size="sm"
            onClick={copyItemsOnly}
            className="h-9 min-w-[148px]"
          >
            Copy items only
          </PrimaryButton>
          <PrimaryButton
            size="sm"
            onClick={copyFullOutput}
            className="h-9 min-w-[148px]"
          >
            Copy full output
          </PrimaryButton>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-5">
        <div className="space-y-4">
          {displayItems.map((item, index) => (
            <InsetPanel
              key={index}
              className="rounded-2xl p-4 transition-colors hover:bg-white/15"
            >
              <div className="flex items-start gap-2">
                <span className="text-sm font-medium text-muted-foreground shrink-0">
                  {index + 1}.
                </span>
                {editingIndex === index && onItemsChange ? (
                  <div className="flex-1 flex gap-2">
                    <Input
                      defaultValue={item.item_text}
                      onBlur={(e) => handleEdit(index, e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleEdit(index, (e.target as HTMLInputElement).value);
                      }}
                      autoFocus
                      className="flex-1"
                    />
                  </div>
                ) : (
                  <div className="flex-1">
                    <p className="text-sm text-slate-100">{item.item_text}</p>
                    {onItemsChange && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="mt-1 h-8 w-8"
                        onClick={() => setEditingIndex(index)}
                        aria-label="Edit item"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                )}
              </div>
              {item.validation_result && (
                <ValidationScoreDisplay validation={item.validation_result} />
              )}
              <div>
                <button
                  type="button"
                  onClick={() => toggleRationale(index)}
                  className="flex items-center gap-1 rounded text-sm font-medium text-accent hover:underline focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  {expandedRationale.has(index) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  Rationale
                </button>
                {expandedRationale.has(index) && (
                  <InsetPanel className="mt-4 rounded-xl border border-white/20 bg-slate-900/45 p-3 pl-4 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-200/80">Rationale</p>
                    <p className="mt-1 text-sm text-slate-100">{item.rationale}</p>
                  </InsetPanel>
                )}
              </div>
            </InsetPanel>
          ))}
        </div>
        <QualityChecksPanel items={displayItems} />
        {fullOutput?.audit?.validation_attempts && fullOutput.audit.validation_attempts > 0 && (
          <div className="mt-4 p-4 bg-blue-50 rounded">
            <h3 className="font-semibold text-slate-900">Validation Summary</h3>
            <p className="text-sm text-slate-700">Total validation attempts: {fullOutput.audit.validation_attempts}</p>
            <p className="text-sm text-slate-700">Items regenerated: {fullOutput.audit.validation_failures || 0}</p>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex flex-col gap-3 border-t border-border/60 pt-5 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">
          {displayItems.length} items generated
          {fullOutput?.audit?.validation_failures
            ? ` (${fullOutput.audit.validation_failures} rejected, ${
                (fullOutput.audit.validation_attempts ?? 0) - (fullOutput.audit.validation_failures ?? 0)
              } from regeneration)`
            : ''
          }
        </p>
        <div className="flex items-center gap-2">
          <Select value={selectedFormat} onValueChange={handleFormatChange}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Format" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="csv">CSV</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
              <SelectItem value="markdown">Markdown</SelectItem>
            </SelectContent>
          </Select>
          <PrimaryButton onClick={handleDownload} size="sm" disabled={!fullOutput}>
            <Download className="mr-2 h-4 w-4" />
            Download
          </PrimaryButton>
        </div>
      </CardFooter>
    </SurfaceCard>
  );
}
