/**
 * Export functions for correlation matrix data
 * Supports CSV (square matrix + CI export) and JSON formats
 */

import type { CorrelationMatrix } from './types';

/**
 * Escape a field value for CSV according to RFC 4180
 * Fields with quotes, commas, or newlines are wrapped in quotes
 * Internal quotes are doubled
 */
function escapeCsvField(value: string): string {
  if (/[",\r\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

/**
 * Truncate item text with ellipsis for column headers
 */
export function truncateItemText(text: string, maxLength = 30): string {
  if (text.length <= maxLength) {
    return text;
  }
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Build a square correlation matrix from flat cells list
 * Returns 2D array where matrix[i][j] is correlation between item i and item j
 */
function buildSquareMatrix(cells: CorrelationMatrix['cells'], itemCount: number): number[][] {
  // Initialize with 1.0 on diagonal
  const matrix: number[][] = Array(itemCount).fill(null).map((_, i) =>
    Array(itemCount).fill(null).map((_, j) => i === j ? 1.0 : 0.0)
  );

  // Fill from cells list (symmetric)
  for (const cell of cells) {
    matrix[cell.item_i_index][cell.item_j_index] = cell.correlation;
    matrix[cell.item_j_index][cell.item_i_index] = cell.correlation; // Symmetric
  }

  return matrix;
}

/**
 * Export correlation matrix as square CSV with metadata header
 * @param matrix - CorrelationMatrix object with cells, omega, mean_r, etc.
 * @param itemTexts - Array of item text strings for row/column labels
 * @returns CSV string with UTF-8 BOM
 */
export function exportCorrelationMatrixToCsv(
  matrix: CorrelationMatrix,
  itemTexts: string[]
): string {
  // UTF-8 BOM for Excel compatibility
  let csv = '\uFEFF';

  // Metadata header rows
  csv += `CORRELATION MATRIX (LLM-ESTIMATED)\r\n`;
  csv += `McDonald's Omega,${matrix.mcdonalds_omega.toFixed(3)}\r\n`;
  csv += `Mean Inter-Item Correlation,${matrix.mean_inter_item_correlation.toFixed(3)}\r\n`;
  csv += `Internal Consistency,${matrix.internal_consistency_flag}\r\n`;
  csv += `\r\n`; // Empty line separator

  // Build square matrix
  const squareMatrix = buildSquareMatrix(matrix.cells, itemTexts.length);

  // Column headers: "" for first column, then "Item 1: [text]", "Item 2: [text]", etc.
  const headers = ['', ...itemTexts.map((text, i) =>
    `Item ${i + 1}: ${escapeCsvField(truncateItemText(text))}`
  )];
  csv += headers.join(',') + '\r\n';

  // Data rows: row label + correlation values
  for (let i = 0; i < itemTexts.length; i++) {
    const rowLabel = `Item ${i + 1}: ${escapeCsvField(truncateItemText(itemTexts[i]))}`;
    const values = squareMatrix[i].map(val => val.toFixed(3));
    csv += rowLabel + ',' + values.join(',') + '\r\n';
  }

  return csv;
}

/**
 * Export confidence intervals as separate CSV file
 * @param matrix - CorrelationMatrix object with cells containing CI data
 * @param itemTexts - Array of item text strings for labels
 * @returns CSV string with UTF-8 BOM
 */
export function exportConfidenceIntervalsToCsv(
  matrix: CorrelationMatrix,
  itemTexts: string[]
): string {
  // UTF-8 BOM for Excel compatibility
  let csv = '\uFEFF';

  // Header row
  csv += 'Item_i,Item_j,Correlation,CI_Low,CI_High\r\n';

  // One row per cell
  for (const cell of matrix.cells) {
    const itemI = `Item ${cell.item_i_index + 1}`;
    const itemJ = `Item ${cell.item_j_index + 1}`;
    const ciLow = cell.ci_low != null ? cell.ci_low.toFixed(3) : '';
    const ciHigh = cell.ci_high != null ? cell.ci_high.toFixed(3) : '';
    csv += `${itemI},${itemJ},${cell.correlation.toFixed(3)},${ciLow},${ciHigh}\r\n`;
  }

  return csv;
}

/**
 * Export full CorrelationMatrix as JSON with disclaimer
 * @param matrix - CorrelationMatrix object
 * @returns Pretty-printed JSON string
 */
export function exportCorrelationMatrixToJson(matrix: CorrelationMatrix): string {
  return JSON.stringify(matrix, null, 2);
}
