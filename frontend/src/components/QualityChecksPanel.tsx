"use client";

import { AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { FinalItem } from "@/lib/types";

export interface QualityChecksPanelProps {
  items: FinalItem[];
}

function wordCount(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function getWarnings(item: FinalItem, index: number): { type: string; message: string }[] {
  const warnings: { type: string; message: string }[] = [];
  const lower = item.item_text.toLowerCase();

  if (lower.includes("and/or")) {
    warnings.push({ type: "and_or", message: "Contains 'and/or'" });
  }
  if (/\b(not|never|no)\b/.test(lower)) {
    warnings.push({ type: "negation", message: "Contains negation (not, never, no)" });
  }
  if (wordCount(item.item_text) > 25) {
    warnings.push({ type: "length", message: `Over 25 words (${wordCount(item.item_text)})` });
  }
  return warnings;
}

export function QualityChecksPanel({ items }: QualityChecksPanelProps) {
  const allWarnings = items.flatMap((item, i) =>
    getWarnings(item, i).map((w) => ({ itemIndex: i + 1, ...w }))
  );

  if (allWarnings.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="h-4 w-4 text-accent" />
          Quality checks
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-2">
          Non-blocking client-side heuristics.
        </p>
        <ul className="space-y-1">
          {allWarnings.map((w, i) => (
            <li key={i} className="flex items-center gap-2 text-sm">
              <Badge variant="outline" className="font-normal">
                Item {w.itemIndex}
              </Badge>
              <span>{w.message}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
