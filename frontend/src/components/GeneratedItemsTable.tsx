"use client";

import * as React from "react";
import { ChevronDown, ChevronRight, Pencil } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import type { FinalItem, FinalOutput } from "@/lib/types";
import { QualityChecksPanel } from "./QualityChecksPanel";

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

  React.useEffect(() => {
    setEditedItems(items);
  }, [items]);

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

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "mapig-output.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadCsv = () => {
    const headers = ["index", "item_text", "rationale", "citations"];
    const rows = displayItems.map((item, i) => [
      i + 1,
      `"${item.item_text.replace(/"/g, '""')}"`,
      `"${item.rationale.replace(/"/g, '""')}"`,
      item.evidence_citations.join("; "),
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "mapig-items.csv";
    a.click();
    URL.revokeObjectURL(url);
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
    <Card className="glass-panel shadow-sm">
      <CardHeader className="flex flex-col items-center gap-3 border-b border-border/60 md:flex-row md:items-center md:justify-between">
        <CardTitle className="text-base md:text-lg">Generated Items</CardTitle>
        <div className="flex flex-wrap justify-center gap-2 md:justify-end">
          <Button
            size="sm"
            onClick={copyItemsOnly}
            className="h-9 min-w-[148px] bg-primary text-white hover:bg-accent hover:text-white"
          >
            Copy items only
          </Button>
          <Button
            size="sm"
            onClick={copyFullOutput}
            className="h-9 min-w-[148px] bg-primary text-white hover:bg-accent hover:text-white"
          >
            Copy full output
          </Button>
          <Button
            size="sm"
            onClick={downloadCsv}
            className="h-9 min-w-[148px] bg-primary text-white hover:bg-accent hover:text-white"
          >
            Download CSV
          </Button>
          <Button
            size="sm"
            onClick={downloadJson}
            className="h-9 min-w-[148px] bg-primary text-white hover:bg-accent hover:text-white"
          >
            Download JSON
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-5">
        <div className="space-y-4">
          {displayItems.map((item, index) => (
            <div
              key={index}
              className="rounded-2xl border border-white/15 bg-white/10 p-4 shadow-sm transition-colors hover:bg-white/15"
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
              <div>
                <button
                  type="button"
                  onClick={() => toggleRationale(index)}
                  className="flex items-center gap-1 rounded text-sm font-medium text-accent-light hover:underline focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  {expandedRationale.has(index) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  Rationale
                </button>
                {expandedRationale.has(index) && (
                  <p className="mt-1 pl-5 text-sm text-slate-200/90">{item.rationale}</p>
                )}
              </div>
              {item.evidence_citations.length > 0 && (
                <div className="flex flex-wrap gap-1 pl-5">
                  {item.evidence_citations.map((cit, j) => (
                    <Badge key={j} variant="outline" className="text-xs font-normal">
                      {cit}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        <QualityChecksPanel items={displayItems} />
      </CardContent>
    </Card>
  );
}
