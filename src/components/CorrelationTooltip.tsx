"use client";

import * as React from "react";
import type { CorrelationCell } from "@/lib/types";
import { truncateItemText } from "@/lib/export-correlation";

export interface CorrelationTooltipProps {
  visible: boolean;
  x: number;
  y: number;
  cell: CorrelationCell | null;
  itemTexts: string[];
}

export function CorrelationTooltip({
  visible,
  x,
  y,
  cell,
  itemTexts
}: CorrelationTooltipProps) {
  if (!visible || !cell) {
    return null;
  }

  const itemI = itemTexts[cell.item_i_index];
  const itemJ = itemTexts[cell.item_j_index];

  return (
    <div
      className="pointer-events-none fixed z-50 rounded-lg bg-slate-900 p-3 text-white shadow-lg"
      style={{
        left: x + 10,
        top: y + 10,
        maxWidth: '300px'
      }}
    >
      <div className="mb-2 text-xs font-semibold text-slate-400">
        Item {cell.item_i_index + 1} × Item {cell.item_j_index + 1}
      </div>
      <div className="mb-2">
        <span className="text-sm font-bold">cos = {cell.correlation.toFixed(3)}</span>
      </div>
      <div className="border-t border-slate-700 pt-2 text-xs text-slate-400">
        <div className="mb-1">
          <span className="font-semibold">Item {cell.item_i_index + 1}:</span>{' '}
          {truncateItemText(itemI, 30)}
        </div>
        <div>
          <span className="font-semibold">Item {cell.item_j_index + 1}:</span>{' '}
          {truncateItemText(itemJ, 30)}
        </div>
      </div>
    </div>
  );
}
