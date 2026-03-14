"use client";

import * as React from "react";
import { ChevronDown, ChevronRight, Download } from "lucide-react";
import * as Popover from "@radix-ui/react-popover";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SurfaceCard } from "@/components/ui/surface-card";
import { SecondaryButton } from "@/components/ui/action-buttons";
import { CorrelationHeatmap } from "./CorrelationHeatmap";
import { CorrelationSummaryCard } from "./CorrelationSummaryCard";
import { CorrelationTooltip } from "./CorrelationTooltip";
import type { CorrelationMatrix, CorrelationCell } from "@/lib/types";
import {
  exportCorrelationMatrixToCsv,
  exportConfidenceIntervalsToCsv,
  exportCorrelationMatrixToJson
} from "@/lib/export-correlation";
import { sanitizeFilename } from "@/lib/utils";

export interface CorrelationPanelProps {
  matrix: CorrelationMatrix;
  itemTexts: string[];
  constructName?: string;
}

export function CorrelationPanel({
  matrix,
  itemTexts,
  constructName = 'items'
}: CorrelationPanelProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [tooltipState, setTooltipState] = React.useState<{
    visible: boolean;
    x: number;
    y: number;
    cell: CorrelationCell | null;
  }>({
    visible: false,
    x: 0,
    y: 0,
    cell: null
  });
  const [popoverOpen, setPopoverOpen] = React.useState(false);
  const [selectedCell, setSelectedCell] = React.useState<CorrelationCell | null>(null);

  // Find cell by indices
  const findCell = (i: number, j: number): CorrelationCell | null => {
    if (i === j) {
      // Diagonal: perfect correlation
      return {
        item_i_index: i,
        item_j_index: j,
        correlation: 1.0,
        ci_low: 1.0,
        ci_high: 1.0
      };
    }

    // Find in cells list (handle both directions due to symmetry)
    const cell = matrix.cells.find(
      c => (c.item_i_index === i && c.item_j_index === j) ||
           (c.item_i_index === j && c.item_j_index === i)
    );

    return cell || null;
  };

  const handleCellHover = (i: number, j: number, event: React.MouseEvent) => {
    const cell = findCell(i, j);
    if (cell) {
      setTooltipState({
        visible: true,
        x: event.clientX,
        y: event.clientY,
        cell
      });
    }
  };

  const handleCellClick = (i: number, j: number) => {
    const cell = findCell(i, j);
    if (cell) {
      setSelectedCell(cell);
      setPopoverOpen(true);
    }
  };

  const handleMouseLeave = () => {
    setTooltipState({
      visible: false,
      x: 0,
      y: 0,
      cell: null
    });
  };

  const handleExportCsv = () => {
    const csv = exportCorrelationMatrixToCsv(matrix, itemTexts);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${sanitizeFilename(constructName)}_correlation_matrix.csv`;
    link.click();
    URL.revokeObjectURL(url);

    // Also export CI file
    const ciCsv = exportConfidenceIntervalsToCsv(matrix, itemTexts);
    const ciBlob = new Blob([ciCsv], { type: 'text/csv;charset=utf-8;' });
    const ciUrl = URL.createObjectURL(ciBlob);
    const ciLink = document.createElement('a');
    ciLink.href = ciUrl;
    ciLink.download = `${sanitizeFilename(constructName)}_confidence_intervals.csv`;
    ciLink.click();
    URL.revokeObjectURL(ciUrl);
  };

  const handleExportJson = () => {
    const json = exportCorrelationMatrixToJson(matrix);
    const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${sanitizeFilename(constructName)}_correlation_matrix.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div onMouseLeave={handleMouseLeave}>
      <SurfaceCard className="mt-4">
        {/* Collapsible header */}
        <CardHeader
          className="cursor-pointer border-b border-border/60 hover:bg-surface-2/50 transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <CardTitle className="flex items-center gap-2 text-base">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            Correlation Analysis
          </CardTitle>
        </CardHeader>

        {/* Expandable content */}
        {isExpanded && (
          <CardContent className="pt-5">
            {/* Heatmap */}
            <div className="mb-4">
              <CorrelationHeatmap
                matrix={matrix}
                itemTexts={itemTexts}
                onCellHover={handleCellHover}
                onCellClick={handleCellClick}
              />
            </div>

            {/* Quality summary card */}
            <CorrelationSummaryCard matrix={matrix} />

            {/* Export buttons */}
            <div className="mt-4 flex gap-2">
              <SecondaryButton onClick={handleExportCsv} size="sm">
                <Download className="mr-2 h-4 w-4" />
                Export CSV
              </SecondaryButton>
              <SecondaryButton onClick={handleExportJson} size="sm">
                <Download className="mr-2 h-4 w-4" />
                Export JSON
              </SecondaryButton>
            </div>
          </CardContent>
        )}
      </SurfaceCard>

      {/* Tooltip */}
      <CorrelationTooltip
        visible={tooltipState.visible}
        x={tooltipState.x}
        y={tooltipState.y}
        cell={tooltipState.cell}
        itemTexts={itemTexts}
      />

      {/* Click popover with full details */}
      <Popover.Root open={popoverOpen} onOpenChange={setPopoverOpen}>
        <Popover.Portal>
          <Popover.Content
            className="z-50 w-96 rounded-lg bg-slate-900 p-4 text-white shadow-2xl"
            sideOffset={5}
          >
            {selectedCell && (
              <div>
                <div className="mb-3 text-sm font-semibold text-slate-400">
                  Item {selectedCell.item_i_index + 1} × Item {selectedCell.item_j_index + 1}
                </div>

                <div className="mb-3">
                  <div className="text-lg font-bold">
                    r = {selectedCell.correlation.toFixed(3)}
                  </div>
                  {selectedCell.ci_low != null && selectedCell.ci_high != null && (
                    <div className="text-sm text-slate-300">
                      95% CI: [{selectedCell.ci_low.toFixed(3)}, {selectedCell.ci_high.toFixed(3)}]
                    </div>
                  )}
                </div>

                <div className="space-y-2 border-t border-slate-700 pt-3">
                  <div className="text-xs">
                    <div className="mb-1 font-semibold text-slate-400">
                      Item {selectedCell.item_i_index + 1}:
                    </div>
                    <div className="text-sm text-slate-100">
                      {itemTexts[selectedCell.item_i_index]}
                    </div>
                  </div>

                  <div className="text-xs">
                    <div className="mb-1 font-semibold text-slate-400">
                      Item {selectedCell.item_j_index + 1}:
                    </div>
                    <div className="text-sm text-slate-100">
                      {itemTexts[selectedCell.item_j_index]}
                    </div>
                  </div>
                </div>
              </div>
            )}
            <Popover.Arrow className="fill-slate-900" />
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    </div>
  );
}
