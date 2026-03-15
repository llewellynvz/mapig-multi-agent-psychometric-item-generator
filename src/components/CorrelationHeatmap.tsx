"use client";

import * as React from "react";
import { HeatmapRect } from "@visx/heatmap";
import { scaleLinear } from "@visx/scale";
import { Group } from "@visx/group";
import type { CorrelationMatrix } from "@/lib/types";

export interface CorrelationHeatmapProps {
  matrix: CorrelationMatrix;
  itemTexts: string[];
  onCellHover?: (i: number, j: number, event: React.MouseEvent) => void;
  onCellClick?: (i: number, j: number) => void;
}

interface HeatmapBin {
  bin: number;
  bins: { bin: number; count: number }[];
}

/**
 * Build 2D heatmap data from flat cells list
 * Returns data structure expected by visx HeatmapRect
 */
function buildHeatmapData(
  cells: CorrelationMatrix['cells'],
  itemCount: number
): HeatmapBin[] {
  // Initialize 2D array with 1.0 on diagonal
  const data: number[][] = Array(itemCount).fill(null).map((_, i) =>
    Array(itemCount).fill(null).map((_, j) => i === j ? 1.0 : 0.0)
  );

  // Fill from cells list (symmetric)
  for (const cell of cells) {
    data[cell.item_i_index][cell.item_j_index] = cell.correlation;
    data[cell.item_j_index][cell.item_i_index] = cell.correlation; // Symmetric
  }

  // Convert to visx format: array of rows, each row has bins
  // Use |correlation| for color mapping (magnitude scale)
  return data.map((row, i) => ({
    bin: i,
    bins: row.map((value, j) => ({
      bin: j,
      count: Math.abs(value) // Use |correlation| for teal magnitude color scale
    }))
  }));
}

export function CorrelationHeatmap({
  matrix,
  itemTexts,
  onCellHover,
  onCellClick
}: CorrelationHeatmapProps) {
  const itemCount = itemTexts.length;

  // Responsive sizing: scale down for large item sets
  const containerWidth = 900; // Max width
  const cellSize = Math.max(44, Math.min(64, containerWidth / itemCount));
  const margin = { top: 80, right: 20, bottom: 20, left: 80 };
  const width = cellSize * itemCount + margin.left + margin.right;
  const height = cellSize * itemCount + margin.top + margin.bottom;

  // Color scale: teal magnitude (light = weak, dark = strong)
  // Uses |correlation| so both positive and negative map to same intensity
  const colorScale = scaleLinear<string>({
    domain: [0, 0.5, 1],
    range: ['#e8f5f7', '#4db8c9', '#006d7c']
  });

  const heatmapData = buildHeatmapData(matrix.cells, itemCount);

  return (
    <div className="correlation-heatmap-container">
      <div className="flex justify-center">
      <svg width={width} height={height}>
        <Group left={margin.left} top={margin.top}>
          {/* Heatmap cells */}
          <HeatmapRect
            data={heatmapData}
            xScale={(d) => d * cellSize}
            yScale={(d) => d * cellSize}
            colorScale={colorScale}
            binWidth={cellSize}
            binHeight={cellSize}
            gap={1}
          >
            {(heatmap) =>
              heatmap.map((bins) =>
                bins.map((bin) => (
                  <rect
                    key={`heatmap-rect-${bin.row}-${bin.column}`}
                    className="cursor-pointer transition-opacity hover:opacity-80"
                    x={bin.x}
                    y={bin.y}
                    width={bin.width}
                    height={bin.height}
                    fill={bin.color}
                    stroke="var(--border)"
                    strokeWidth={0.5}
                    onMouseEnter={(e) => onCellHover?.(bin.row, bin.column, e)}
                    onClick={() => onCellClick?.(bin.row, bin.column)}
                  />
                ))
              )
            }
          </HeatmapRect>

          {/* Y-axis labels (left) */}
          {itemTexts.map((_, i) => (
            <text
              key={`y-label-${i}`}
              x={-8}
              y={i * cellSize + cellSize / 2}
              fontSize={10}
              textAnchor="end"
              dominantBaseline="middle"
              className="fill-foreground"
            >
              Item {i + 1}
            </text>
          ))}

          {/* X-axis labels (top, rotated) */}
          {itemTexts.map((_, i) => (
            <text
              key={`x-label-${i}`}
              x={i * cellSize + cellSize / 2}
              y={-10}
              fontSize={10}
              textAnchor="start"
              dominantBaseline="middle"
              transform={`rotate(-45, ${i * cellSize + cellSize / 2}, -10)`}
              className="fill-foreground"
            >
              Item {i + 1}
            </text>
          ))}
        </Group>
      </svg>
      </div>

      {/* Color legend */}
      <div className="mt-4 flex items-center justify-center gap-3">
        <span className="text-xs font-medium text-muted-foreground">0.0</span>
        <div className="flex h-3 w-56 rounded-full overflow-hidden" style={{
          background: 'linear-gradient(to right, #e8f5f7, #4db8c9, #006d7c)'
        }} />
        <span className="text-xs font-medium text-[#006d7c]">1.0</span>
      </div>
      <p className="mt-1.5 text-center text-[11px] text-muted-foreground">
        Light = weak correlation, Dark = strong correlation
      </p>
    </div>
  );
}
