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

  // Section 6: Pseudo-Factor Analysis (Phase 14)
  if (fullOutput.pfa_result && fullOutput.pfa_result.loadings.length > 0) {
    const pfa = fullOutput.pfa_result;
    md += `## Pseudo-Factor Analysis\n\n`;
    md += `Embedding-based pre-calibration factor structure (Varrasi et al., 2026). `;
    md += `Embedding model: \`${pfa.embedding_model}\`.\n\n`;
    md += `**Fit verdict:** ${pfa.fit_verdict.toUpperCase()}\n\n`;
    if (pfa.model_identifiability) {
      md += `**Model identifiability:** ${pfa.model_identifiability}`;
      if (pfa.model_identifiability === 'saturated') {
        md += ` (RMSR / CAF are uninformative — model is exactly identified)`;
      }
      md += `\n\n`;
    }
    md += `**Summary statistics:**\n\n`;
    md += `| Metric | Value |\n|---|---|\n`;
    md += `| Items | ${pfa.n_items} |\n`;
    md += `| Factors | ${pfa.n_factors} |\n`;
    md += `| Factor recovery rate | ${(pfa.factor_recovery_rate * 100).toFixed(0)}% |\n`;
    md += `| RMSR | ${pfa.rmsr.toFixed(4)} |\n`;
    md += `| CAF | ${pfa.caf.toFixed(4)} |\n`;
    if (pfa.tuckers_congruence.length > 0) {
      const meanCong = pfa.tuckers_congruence.reduce((a, b) => a + b, 0) / pfa.tuckers_congruence.length;
      md += `| Mean Tucker's congruence | ${meanCong.toFixed(3)} |\n`;
    }
    if (pfa.items_dropped.length > 0) {
      md += `| Items dropped (PFA pruning) | ${pfa.items_dropped.length} |\n`;
    }
    md += '\n';

    if (pfa.factor_labels.length > 0) {
      md += `**Factor labels (DAAL):**\n\n`;
      pfa.factor_labels.forEach((label, idx) => {
        const cong = pfa.tuckers_congruence[idx];
        md += `- **F${idx + 1}: ${label}**`;
        if (cong !== undefined) md += ` — Tucker's congruence ${cong.toFixed(3)}`;
        md += `\n`;
      });
      md += '\n';
    }

    md += `**Item × Factor loadings:**\n\n`;
    md += `| Item | Facet | ${pfa.factor_labels.map((_, i) => `F${i + 1}`).join(' | ')} | Retention |\n`;
    md += `|---|---|${pfa.factor_labels.map(() => '---').join('|')}|---|\n`;
    pfa.loadings.forEach(fl => {
      const loadStr = fl.loadings.map(l => l.toFixed(2)).join(' | ');
      const retention = fl.is_well_loaded ? 'OK' : `flag (${fl.retention_rule_violations.join(', ')})`;
      md += `| ${fl.item_index + 1} | ${fl.facet_name ?? '—'} | ${loadStr} | ${retention} |\n`;
    });
    md += '\n';

    if (pfa.eigenvalues.length > 0) {
      md += `**Eigenvalues:** ${pfa.eigenvalues.map(e => e.toFixed(2)).join(', ')}\n\n`;
    }

    md += `*${pfa.disclaimer}*\n\n`;
  }

  // Section 7: Expert Panel (Phase 15)
  if (fullOutput.expert_consensus && fullOutput.expert_consensus.evaluations.length > 0) {
    const ec = fullOutput.expert_consensus;
    md += `## Expert Panel — Face/Content Validity\n\n`;
    if (ec.irr_alpha != null) {
      md += `**Inter-rater reliability (Krippendorff's α):** ${ec.irr_alpha.toFixed(3)}\n\n`;
    }
    if (ec.irr_warning) {
      md += `> ⚠ ${ec.irr_warning}\n\n`;
    }

    if (Object.keys(ec.irr_pairwise).length > 0) {
      md += `**Pairwise Cohen's κ:**\n\n`;
      Object.entries(ec.irr_pairwise).forEach(([pair, kappa]) => {
        md += `- ${pair.replace('|', ' ↔ ')}: ${kappa.toFixed(3)}\n`;
      });
      md += '\n';
    }

    const finalEvals = ec.debate_revisions.length > 0 ? ec.debate_revisions : ec.evaluations;
    md += `**Per-expert evaluations:**\n\n`;
    md += `| Expert | Verdict | Mean score | Item-level concerns |\n|---|---|---|---|\n`;
    finalEvals.forEach(ev => {
      const scores = Object.values(ev.item_scores);
      const mean = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
      const concernCount = Object.values(ev.item_comments).filter(c => c && c.length > 0).length;
      md += `| ${ev.expert_label} | ${ev.overall_verdict} | ${mean.toFixed(2)} / 5 | ${concernCount} flagged |\n`;
    });
    md += '\n';

    finalEvals.forEach(ev => {
      const concerns = Object.entries(ev.item_comments).filter(([_, c]) => c && c.length > 0);
      if (concerns.length > 0) {
        md += `**${ev.expert_label} — flagged items:**\n\n`;
        concerns.forEach(([idx, comment]) => {
          md += `- Item ${parseInt(idx, 10) + 1} (score ${ev.item_scores[parseInt(idx, 10)]}): ${comment}\n`;
        });
        md += '\n';
      }
      if (ev.overall_summary) {
        md += `*${ev.expert_label}:* ${ev.overall_summary}\n\n`;
      }
    });

    if (ec.dissent_flags.length > 0) {
      md += `**Items with inter-expert disagreement (SD ≥ 1.0):** ${ec.dissent_flags.map(i => i + 1).join(', ')}\n\n`;
    }

    if (ec.consensus_revisions.edits.length > 0) {
      md += `**Consensus revisions applied:**\n\n`;
      ec.consensus_revisions.edits.forEach(edit => {
        md += `- Item ${edit.item_index + 1}: ${edit.reason}\n`;
      });
      md += '\n';
    } else {
      md += `*${ec.consensus_revisions.summary}*\n\n`;
    }
  }

  // Section 8: Persona Validation (Phase 16)
  if (fullOutput.persona_validation && fullOutput.persona_validation.ratings.length > 0) {
    const pv = fullOutput.persona_validation;
    md += `## Persona-Based Conceptual Alignment (Step 13)\n\n`;
    md += `${pv.summary}\n\n`;
    md += `**Interpretive variance** (mean cross-persona SD): ${pv.interpretive_variance.toFixed(2)}\n\n`;

    if (pv.personas.length > 0) {
      md += `**Personas used:**\n\n`;
      pv.personas.forEach((p, idx) => {
        md += `${idx + 1}. ${p}\n`;
      });
      md += '\n';
    }

    // Group ratings by item for a readable table
    const byItem = new Map<number, Array<{ persona: string; rating: number; interpretation: string }>>();
    pv.ratings.forEach(r => {
      const arr = byItem.get(r.item_index) ?? [];
      arr.push({ persona: r.persona_label, rating: r.rating, interpretation: r.interpretation });
      byItem.set(r.item_index, arr);
    });

    md += `**Per-item persona ratings + reasoning:**\n\n`;
    Array.from(byItem.entries()).sort((a, b) => a[0] - b[0]).forEach(([itemIdx, ratings]) => {
      md += `**Item ${itemIdx + 1}**\n\n`;
      ratings.forEach(r => {
        md += `- *${r.persona}* — rated ${r.rating}/5: "${r.interpretation}"\n`;
      });
      md += '\n';
    });

    if (pv.flagged_items.length > 0) {
      md += `**Items flagged for ambiguity** (SD ≥ 2 across personas): ${pv.flagged_items.map(i => i + 1).join(', ')}\n\n`;
    }
  }

  // Section 9: Audit Trail
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
  if (fullOutput.audit.force_accepted_below_threshold) {
    md += `- **Force-accept fallback:** YES`;
    if (fullOutput.audit.forced_scores && fullOutput.audit.forced_scores.length > 0) {
      md += ` (scores: ${fullOutput.audit.forced_scores.map(s => s.toFixed(2)).join(', ')})`;
    }
    md += `\n`;
  }
  if (fullOutput.audit.warnings && fullOutput.audit.warnings.length > 0) {
    md += `\n**Setup warnings:**\n`;
    fullOutput.audit.warnings.forEach(w => {
      md += `- ${w}\n`;
    });
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
