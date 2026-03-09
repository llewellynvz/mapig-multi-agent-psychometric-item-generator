/**
 * Export formatting functions for MAPIG-generated items
 * Supports CSV (RFC 4180), JSON, and Markdown formats
 * Includes full metadata: validation scores, review feedback, audit trail
 */

import type { FinalOutput } from './types';
import { sanitizeFilename } from './utils';

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
 * Export FinalOutput to CSV format with UTF-8 BOM for Excel compatibility
 * Includes metadata rows, validation scores, and review feedback
 */
export function exportToCsv(fullOutput: FinalOutput): string {
  // UTF-8 BOM for Excel compatibility
  let csv = '\uFEFF';

  // Metadata rows from user_request
  const constructName = fullOutput.user_request?.construct_name ?? fullOutput.final_items[0]?.construct_name ?? 'items';
  const definition = fullOutput.user_request?.construct_definition ?? '';
  const population = fullOutput.user_request?.target_population ?? '';
  const constraints = fullOutput.user_request?.constraints?.join('; ') ?? '';

  csv += `CONSTRUCT,${escapeCsvField(constructName)}\r\n`;
  csv += `DEFINITION,${escapeCsvField(definition)}\r\n`;
  csv += `TARGET_POPULATION,${escapeCsvField(population)}\r\n`;
  csv += `CONSTRAINTS,${escapeCsvField(constraints)}\r\n`;
  csv += '\r\n'; // Blank separator

  // Header row
  const headers = [
    'item_number',
    'item_text',
    'rationale',
    'validation_score',
    'validation_accept',
    'attempt_count',
    'dimension_scores',
    'evidence_citations',
    'review_feedback',
  ];
  csv += headers.join(',') + '\r\n';

  // Collect all feedback arrays (may be undefined in older data)
  const linguisticFeedback = fullOutput.linguistic_feedback ?? [];
  const biasFeedback = fullOutput.bias_feedback ?? [];
  const contentFeedback = fullOutput.content_feedback ?? [];

  // Data rows
  fullOutput.final_items.forEach((item, index) => {
    const itemNumber = (index + 1).toString();
    const itemText = escapeCsvField(item.item_text);
    const rationale = escapeCsvField(item.rationale);

    const validationScore = item.validation_result?.weighted_score?.toString() ?? '';
    const validationAccept = item.validation_result?.accept ? 'TRUE' : 'FALSE';
    const attemptCount = item.validation_result?.attempt?.toString() ?? '';

    // Dimension scores as JSON string
    const dimensionScores = item.validation_result?.dimension_scores
      ? escapeCsvField(JSON.stringify(item.validation_result.dimension_scores))
      : '';

    // Evidence citations as semicolon-separated
    const evidenceCitations = escapeCsvField(item.evidence_citations.join('; '));

    // Review feedback: filter all three arrays by item_index
    const itemFeedback = [
      ...linguisticFeedback.filter(f => f.item_index === index),
      ...biasFeedback.filter(f => f.item_index === index),
      ...contentFeedback.filter(f => f.item_index === index),
    ];
    const reviewFeedback = itemFeedback.length > 0
      ? escapeCsvField(JSON.stringify(itemFeedback))
      : '';

    const row = [
      itemNumber,
      itemText,
      rationale,
      validationScore,
      validationAccept,
      attemptCount,
      dimensionScores,
      evidenceCitations,
      reviewFeedback,
    ];

    csv += row.join(',') + '\r\n';
  });

  return csv;
}

/**
 * Export FinalOutput to JSON format (formatted with 2-space indent)
 * Returns the full FinalOutput structure including Phase 3.1 fields
 */
export function exportToJson(fullOutput: FinalOutput): string {
  return JSON.stringify(fullOutput, null, 2);
}

/**
 * Export FinalOutput to Markdown format
 * Includes construct definition, items, validation scores table, review feedback, and audit trail
 */
export function exportToMarkdown(fullOutput: FinalOutput): string {
  let md = '';

  // Section 1: Title and timestamp
  const constructName = fullOutput.user_request?.construct_name ?? fullOutput.final_items[0]?.construct_name ?? 'Generated Items';
  const timestamp = fullOutput.audit.timestamp_utc;
  md += `# ${constructName}\n\n`;
  md += `**Generated:** ${timestamp}\n\n`;

  // Section 2: Construct Definition
  md += `## Construct Definition\n\n`;
  if (fullOutput.user_request) {
    md += `**Construct:** ${fullOutput.user_request.construct_name}\n\n`;
    md += `**Definition:** ${fullOutput.user_request.construct_definition}\n\n`;
    md += `**Target Population:** ${fullOutput.user_request.target_population}\n\n`;
    if (fullOutput.user_request.constraints && fullOutput.user_request.constraints.length > 0) {
      md += `**Constraints:**\n`;
      fullOutput.user_request.constraints.forEach(constraint => {
        md += `- ${constraint}\n`;
      });
      md += '\n';
    }
  }

  // Section 3: Generated Items
  md += `## Generated Items\n\n`;
  fullOutput.final_items.forEach((item, index) => {
    md += `### Item ${index + 1}\n\n`;
    md += `**Text:** ${item.item_text}\n\n`;
    md += `**Rationale:** ${item.rationale}\n\n`;
    md += `**Evidence Citations:** ${item.evidence_citations.join(', ')}\n\n`;
  });

  // Section 4: Validation Scores
  md += `## Validation Scores\n\n`;
  md += `| Item | Score | Accept | Correspondence | Distinctiveness | Clarity | Specificity |\n`;
  md += `|------|-------|--------|----------------|-----------------|---------|-------------|\n`;

  fullOutput.final_items.forEach((item, index) => {
    if (item.validation_result) {
      const v = item.validation_result;
      const scores = v.dimension_scores.reduce((acc, ds) => {
        acc[ds.dimension] = ds.score;
        return acc;
      }, {} as Record<string, number>);

      md += `| ${index + 1} | ${v.weighted_score.toFixed(2)} | ${v.accept ? 'Yes' : 'No'} | `;
      md += `${scores.correspondence?.toFixed(1) ?? 'N/A'} | `;
      md += `${scores.distinctiveness?.toFixed(1) ?? 'N/A'} | `;
      md += `${scores.clarity?.toFixed(1) ?? 'N/A'} | `;
      md += `${scores.specificity?.toFixed(1) ?? 'N/A'} |\n`;
    }
  });
  md += '\n';

  // Section 5: Review Feedback
  md += `## Review Feedback\n\n`;

  const linguisticFeedback = fullOutput.linguistic_feedback ?? [];
  const biasFeedback = fullOutput.bias_feedback ?? [];
  const contentFeedback = fullOutput.content_feedback ?? [];

  md += `### Linguistic Reviewer\n\n`;
  if (linguisticFeedback.length > 0) {
    linguisticFeedback.forEach(comment => {
      const itemRef = comment.item_index !== undefined ? `Item ${comment.item_index + 1}` : 'General';
      md += `- **${itemRef}:** ${comment.issue} (severity ${comment.severity})\n`;
      if (comment.suggested_edit) {
        md += `  - Suggested: ${comment.suggested_edit}\n`;
      }
    });
  } else {
    md += `No linguistic feedback provided.\n`;
  }
  md += '\n';

  md += `### Bias Reviewer\n\n`;
  if (biasFeedback.length > 0) {
    biasFeedback.forEach(comment => {
      const itemRef = comment.item_index !== undefined ? `Item ${comment.item_index + 1}` : 'General';
      md += `- **${itemRef}:** ${comment.issue} (severity ${comment.severity})\n`;
      if (comment.suggested_edit) {
        md += `  - Suggested: ${comment.suggested_edit}\n`;
      }
    });
  } else {
    md += `No bias feedback provided.\n`;
  }
  md += '\n';

  md += `### Content Reviewer\n\n`;
  if (contentFeedback.length > 0) {
    contentFeedback.forEach(comment => {
      const itemRef = comment.item_index !== undefined ? `Item ${comment.item_index + 1}` : 'General';
      md += `- **${itemRef}:** ${comment.issue} (severity ${comment.severity})\n`;
      if (comment.suggested_edit) {
        md += `  - Suggested: ${comment.suggested_edit}\n`;
      }
    });
  } else {
    md += `No content feedback provided.\n`;
  }
  md += '\n';

  // Section 6: Audit Trail
  md += `## Audit Trail\n\n`;
  md += `- **Thread ID:** ${fullOutput.audit.thread_id}\n`;
  md += `- **Run ID:** ${fullOutput.audit.run_id}\n`;
  md += `- **Iterations:** ${fullOutput.audit.iteration_count}\n`;
  if (fullOutput.audit.validation_attempts !== undefined) {
    md += `- **Validation Attempts:** ${fullOutput.audit.validation_attempts}\n`;
  }
  if (fullOutput.audit.validation_failures !== undefined) {
    md += `- **Validation Failures:** ${fullOutput.audit.validation_failures}\n`;
  }

  return md;
}

/**
 * Generate a filename for export with sanitized construct name and timestamp
 * Format: {construct-name}_{YYYYMMDD-HHMMSS}.{extension}
 */
export function generateFilename(constructName: string, extension: string): string {
  const sanitized = sanitizeFilename(constructName);

  // Generate timestamp in YYYYMMDD-HHMMSS format
  const now = new Date();
  const year = now.getUTCFullYear().toString();
  const month = (now.getUTCMonth() + 1).toString().padStart(2, '0');
  const day = now.getUTCDate().toString().padStart(2, '0');
  const hours = now.getUTCHours().toString().padStart(2, '0');
  const minutes = now.getUTCMinutes().toString().padStart(2, '0');
  const seconds = now.getUTCSeconds().toString().padStart(2, '0');

  const timestamp = `${year}${month}${day}-${hours}${minutes}${seconds}`;

  return `${sanitized}_${timestamp}.${extension}`;
}
