import { describe, it, expect } from 'vitest';
import { exportToCsv, exportToJson, exportToMarkdown, generateFilename } from '../export';
import { sanitizeFilename } from '../utils';
import type { FinalOutput } from '../types';

describe('export functions', () => {
  // Test fixture: minimal FinalOutput with Phase 3.1 fields
  const mockFinalOutput: FinalOutput = {
    final_items: [
      {
        item_text: 'I feel anxious in social situations',
        construct_name: 'Social Anxiety',
        rationale: 'Captures core social anxiety symptom',
        evidence_citations: ['DSM-5', 'Liebowitz Social Anxiety Scale'],
        validation_result: {
          item_index: 0,
          item_text: 'I feel anxious in social situations',
          dimension_scores: [
            { dimension: 'correspondence', reasoning: 'Aligns with construct', score: 4.5 },
            { dimension: 'distinctiveness', reasoning: 'Unique phrasing', score: 4.0 },
            { dimension: 'clarity', reasoning: 'Clear wording', score: 5.0 },
            { dimension: 'specificity', reasoning: 'Appropriately specific', score: 4.2 },
          ],
          weighted_score: 4.4,
          accept: true,
          attempt: 1,
        },
      },
      {
        item_text: 'I worry "too much" about others\' opinions',
        construct_name: 'Social Anxiety',
        rationale: 'Reflects worry component',
        evidence_citations: ['Social Phobia Inventory'],
        validation_result: {
          item_index: 1,
          item_text: 'I worry "too much" about others\' opinions',
          dimension_scores: [
            { dimension: 'correspondence', reasoning: 'Core symptom', score: 4.8 },
            { dimension: 'distinctiveness', reasoning: 'Distinct from item 1', score: 4.5 },
            { dimension: 'clarity', reasoning: 'Generally clear', score: 4.3 },
            { dimension: 'specificity', reasoning: 'Well-scoped', score: 4.0 },
          ],
          weighted_score: 4.6,
          accept: true,
          attempt: 2,
        },
      },
    ],
    audit: {
      thread_id: 'thread_abc123',
      run_id: 'run_xyz789',
      timestamp_utc: '2026-03-08T22:00:00Z',
      iteration_count: 3,
      stop_reason: 'completed',
      model_info: { model: 'claude-opus-4-6' },
      approved_sources: ['DSM-5', 'Academic journals'],
      validation_attempts: 3,
      validation_failures: 1,
    },
    user_request: {
      construct_name: 'Social Anxiety',
      construct_definition: 'Persistent fear and avoidance of social situations due to negative evaluation concerns',
      target_population: 'Adults aged 18-65',
      response_scale: '5-point Likert (Strongly Disagree to Strongly Agree)',
      item_count: 2,
      constraints: ['Avoid clinical jargon', 'Use first person'],
    },
    linguistic_feedback: [
      {
        type: 'linguistic',
        item_index: 1,
        issue: 'Quotation marks around "too much" may confuse respondents',
        severity: 3,
        suggested_edit: 'I worry excessively about others\' opinions',
      },
    ],
    bias_feedback: [
      {
        type: 'bias',
        item_index: 0,
        issue: 'May assume social situation access',
        severity: 2,
        suggested_edit: 'Consider adding context qualifier',
      },
    ],
    content_feedback: [],
  };

  describe('exportToCsv', () => {
    it('starts with UTF-8 BOM for Excel compatibility', () => {
      const csv = exportToCsv(mockFinalOutput);
      expect(csv.charCodeAt(0)).toBe(0xfeff);
    });

    it('includes user_request metadata rows at top', () => {
      const csv = exportToCsv(mockFinalOutput);
      const lines = csv.split('\r\n');

      expect(lines[0]).toContain('CONSTRUCT');
      expect(lines[0]).toContain('Social Anxiety');
      expect(lines[1]).toContain('DEFINITION');
      expect(lines[1]).toContain('Persistent fear and avoidance');
      expect(lines[2]).toContain('TARGET_POPULATION');
      expect(lines[2]).toContain('Adults aged 18-65');
      expect(lines[3]).toContain('CONSTRAINTS');
      expect(lines[3]).toContain('Avoid clinical jargon');
    });

    it('escapes fields with quotes using RFC 4180 (double quotes)', () => {
      const csv = exportToCsv(mockFinalOutput);

      // Item 2 has quotes in text: 'I worry "too much" about others\' opinions'
      // Should be escaped as: "I worry ""too much"" about others' opinions"
      expect(csv).toContain('I worry ""too much"" about others\' opinions');
    });

    it('wraps fields with commas in quotes', () => {
      const testData: FinalOutput = {
        ...mockFinalOutput,
        final_items: [
          {
            ...mockFinalOutput.final_items[0],
            rationale: 'Captures anxiety, worry, and avoidance',
          },
        ],
      };

      const csv = exportToCsv(testData);
      // Field with commas should be wrapped in quotes
      expect(csv).toContain('"Captures anxiety, worry, and avoidance"');
    });

    it('includes review_feedback column with filtered comments', () => {
      const csv = exportToCsv(mockFinalOutput);
      const lines = csv.split('\r\n');

      // Find header row (after metadata rows and blank line)
      const headerLine = lines.find(line => line.includes('review_feedback'));
      expect(headerLine).toBeDefined();

      // Item 2 (index 1) should have linguistic feedback
      const item2Line = lines.find(line => line.includes('I worry ""too much""'));
      expect(item2Line).toContain('Quotation marks');
    });
  });

  describe('exportToJson', () => {
    it('matches FinalOutput structure with Phase 3.1 fields', () => {
      const json = exportToJson(mockFinalOutput);
      const parsed = JSON.parse(json);

      expect(parsed).toHaveProperty('final_items');
      expect(parsed).toHaveProperty('audit');
      expect(parsed).toHaveProperty('user_request');
      expect(parsed).toHaveProperty('linguistic_feedback');
      expect(parsed).toHaveProperty('bias_feedback');
      expect(parsed).toHaveProperty('content_feedback');

      expect(parsed.user_request.construct_name).toBe('Social Anxiety');
      expect(parsed.linguistic_feedback).toHaveLength(1);
    });

    it('uses 2-space indentation for readability', () => {
      const json = exportToJson(mockFinalOutput);

      // Check for 2-space indent (should have lines starting with "  ")
      expect(json).toContain('\n  "final_items"');
    });
  });

  describe('exportToMarkdown', () => {
    it('includes all required sections', () => {
      const md = exportToMarkdown(mockFinalOutput);

      expect(md).toContain('# Social Anxiety');
      expect(md).toContain('## Construct Definition');
      expect(md).toContain('## Generated Items');
      expect(md).toContain('## Validation Scores');
      expect(md).toContain('## Review Feedback');
      expect(md).toContain('## Audit Trail');
    });

    it('includes all 4 validation dimensions in table', () => {
      const md = exportToMarkdown(mockFinalOutput);

      expect(md).toContain('Correspondence');
      expect(md).toContain('Distinctiveness');
      expect(md).toContain('Clarity');
      expect(md).toContain('Specificity');

      // Check scores are present
      expect(md).toContain('4.5');
      expect(md).toContain('4.0');
      expect(md).toContain('5.0');
      expect(md).toContain('4.2');
    });

    it('includes review feedback with three subsections', () => {
      const md = exportToMarkdown(mockFinalOutput);

      expect(md).toContain('### Linguistic Reviewer');
      expect(md).toContain('### Bias Reviewer');
      expect(md).toContain('### Content Reviewer');

      // Check feedback content
      expect(md).toContain('Quotation marks around "too much"');
      expect(md).toContain('May assume social situation access');
    });

    it('includes user_request data in Construct Definition section', () => {
      const md = exportToMarkdown(mockFinalOutput);

      expect(md).toContain('Persistent fear and avoidance of social situations');
      expect(md).toContain('Adults aged 18-65');
      expect(md).toContain('Avoid clinical jargon');
      expect(md).toContain('Use first person');
    });
  });

  describe('generateFilename', () => {
    it('sanitizes construct name and adds timestamp', () => {
      const filename = generateFilename('Social Anxiety: Clinical', 'csv');

      expect(filename).toMatch(/^social-anxiety-clinical_\d{8}-\d{6}\.csv$/);
    });

    it('produces timestamp in YYYYMMDD-HHMMSS format', () => {
      const filename = generateFilename('Test Construct', 'json');

      // Extract timestamp part (between underscore and extension)
      const match = filename.match(/_(\d{8}-\d{6})\./);
      expect(match).toBeTruthy();

      const timestamp = match![1];
      expect(timestamp).toMatch(/^\d{8}-\d{6}$/);
    });
  });

  describe('sanitizeFilename', () => {
    it('converts to lowercase and replaces special chars with hyphens', () => {
      expect(sanitizeFilename('Social Anxiety: Clinical')).toBe('social-anxiety-clinical');
    });

    it('handles edge case of empty result by returning "untitled"', () => {
      expect(sanitizeFilename('!!!')).toBe('untitled');
      expect(sanitizeFilename('')).toBe('untitled');
    });

    it('removes leading and trailing hyphens', () => {
      expect(sanitizeFilename('  Test  ')).toBe('test');
    });

    it('limits to 50 characters', () => {
      const longName = 'a'.repeat(100);
      const result = sanitizeFilename(longName);
      expect(result.length).toBeLessThanOrEqual(50);
    });
  });
});
