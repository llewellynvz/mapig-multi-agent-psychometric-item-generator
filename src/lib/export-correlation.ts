/**
 * Export functions for correlation matrix data
 * Supports CSV (square matrix + CI export) and JSON formats
 */

import type { CorrelationMatrix, SyntheticPilotResult } from './types';

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
  csv += `SEMANTIC SIMILARITY MATRIX (EMBEDDING-BASED PRE-DATA ESTIMATE)\r\n`;
  csv += `Pseudo-alpha (semantic),${matrix.pseudo_alpha != null ? matrix.pseudo_alpha.toFixed(3) : 'not estimable'}\r\n`;
  csv += `Mean Semantic Similarity,${matrix.mean_inter_item_correlation.toFixed(3)}\r\n`;
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
 * Export full CorrelationMatrix as JSON with disclaimer
 * @param matrix - CorrelationMatrix object
 * @returns Pretty-printed JSON string
 */
export function exportCorrelationMatrixToJson(matrix: CorrelationMatrix): string {
  return JSON.stringify(matrix, null, 2);
}

/**
 * Export the synthetic-respondent pilot as CSV. Every column carries the
 * synthetic_ prefix so simulated statistics can never be mistaken for
 * human data downstream.
 */
export function exportSyntheticPilotToCsv(
  pilot: SyntheticPilotResult,
  itemTexts: string[]
): string {
  const num = (value: number | null, digits = 4) =>
    value != null ? value.toFixed(digits) : 'not estimable';

  let csv = '﻿';
  csv += `SYNTHETIC PILOT (SIMULATED LLM RESPONDENTS)\r\n`;
  csv += `${escapeCsvField(pilot.disclaimer)}\r\n`;
  csv += `synthetic_n_respondents,${pilot.n_respondents}\r\n`;
  csv += `synthetic_n_items,${pilot.n_items}\r\n`;
  csv += `synthetic_scale_points,${pilot.scale_points}\r\n`;
  csv += `synthetic_model,${escapeCsvField(pilot.model_name)}\r\n`;
  csv += `synthetic_failed_respondents,${pilot.failed_respondents}\r\n`;
  csv += `synthetic_cronbach_alpha,${num(pilot.cronbach_alpha)}\r\n`;
  csv += `synthetic_omega_total,${num(pilot.omega_total)}\r\n`;
  csv += `synthetic_kmo,${num(pilot.kmo)}\r\n`;
  csv += `synthetic_bartlett_chi2,${num(pilot.bartlett_chi2, 2)}\r\n`;
  csv += `synthetic_bartlett_p,${pilot.bartlett_p != null ? pilot.bartlett_p.toExponential(3) : 'not estimable'}\r\n`;
  csv += `synthetic_parallel_analysis_n_factors,${pilot.parallel_analysis_n_factors ?? 'not estimable'}\r\n`;
  csv += `\r\n`;

  csv += `synthetic_component,synthetic_observed_eigenvalue,synthetic_random_threshold\r\n`;
  pilot.observed_eigenvalues.forEach((eig, i) => {
    const threshold = pilot.threshold_eigenvalues[i];
    csv += `${i + 1},${eig.toFixed(4)},${threshold != null ? threshold.toFixed(4) : ''}\r\n`;
  });
  csv += `\r\n`;

  csv += `synthetic_item_i,synthetic_item_j,synthetic_pearson_r,synthetic_ci_low,synthetic_ci_high\r\n`;
  for (const cell of pilot.cells) {
    const labelI = escapeCsvField(truncateItemText(itemTexts[cell.item_i_index] ?? `Item ${cell.item_i_index + 1}`));
    const labelJ = escapeCsvField(truncateItemText(itemTexts[cell.item_j_index] ?? `Item ${cell.item_j_index + 1}`));
    csv += `${labelI},${labelJ},${cell.correlation.toFixed(4)},${cell.ci_low != null ? cell.ci_low.toFixed(4) : ''},${cell.ci_high != null ? cell.ci_high.toFixed(4) : ''}\r\n`;
  }

  return csv;
}
