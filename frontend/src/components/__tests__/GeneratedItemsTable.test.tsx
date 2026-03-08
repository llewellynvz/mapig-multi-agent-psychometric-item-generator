import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { GeneratedItemsTable } from '../GeneratedItemsTable';
import type { FinalOutput } from '@/lib/types';

// Mock toast
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe('GeneratedItemsTable export UI', () => {
  const mockFinalOutput: FinalOutput = {
    final_items: [
      {
        item_text: 'I feel anxious',
        construct_name: 'Anxiety',
        rationale: 'Core symptom',
        evidence_citations: ['DSM-5'],
        validation_result: {
          item_index: 0,
          item_text: 'I feel anxious',
          dimension_scores: [
            { dimension: 'correspondence', reasoning: 'Good', score: 4.5 },
            { dimension: 'distinctiveness', reasoning: 'Unique', score: 4.0 },
            { dimension: 'clarity', reasoning: 'Clear', score: 5.0 },
            { dimension: 'specificity', reasoning: 'Specific', score: 4.2 },
          ],
          weighted_score: 4.4,
          accept: true,
          attempt: 1,
        },
      },
    ],
    audit: {
      thread_id: 'thread_123',
      run_id: 'run_456',
      timestamp_utc: '2026-03-08T22:00:00Z',
      iteration_count: 1,
      stop_reason: 'completed',
      model_info: {},
      approved_sources: ['DSM-5'],
      validation_attempts: 1,
      validation_failures: 0,
    },
    user_request: {
      construct_name: 'Anxiety',
      construct_definition: 'Worry and nervousness',
      target_population: 'Adults',
      response_scale: '5-point Likert',
    },
    linguistic_feedback: [],
    bias_feedback: [],
    content_feedback: [],
  };

  let mockCreateObjectURL: ReturnType<typeof vi.fn>;
  let mockRevokeObjectURL: ReturnType<typeof vi.fn>;
  let mockClick: ReturnType<typeof vi.fn>;
  let mockLocalStorage: Record<string, string>;

  beforeEach(() => {
    // Mock URL.createObjectURL and revokeObjectURL
    mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
    mockRevokeObjectURL = vi.fn();
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;

    // Mock createElement to track download clicks
    mockClick = vi.fn();
    const originalCreateElement = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      const element = originalCreateElement(tagName);
      if (tagName === 'a') {
        element.click = mockClick;
      }
      return element;
    });

    // Mock localStorage
    mockLocalStorage = {};
    global.localStorage = {
      getItem: vi.fn((key: string) => mockLocalStorage[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        mockLocalStorage[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete mockLocalStorage[key];
      }),
      clear: vi.fn(() => {
        mockLocalStorage = {};
      }),
      key: vi.fn(),
      length: 0,
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders format selector with 3 options (CSV, JSON, Markdown)', async () => {
    render(<GeneratedItemsTable items={mockFinalOutput.final_items} fullOutput={mockFinalOutput} />);

    // Look for Download button (should exist in footer)
    const downloadButton = screen.getByRole('button', { name: /download/i });
    expect(downloadButton).toBeDefined();

    // Look for select trigger - use a more flexible query
    const selectTriggers = screen.getAllByRole('combobox');
    expect(selectTriggers.length).toBeGreaterThan(0);

    // Click the last select trigger (format selector)
    const user = userEvent.setup();
    const formatSelector = selectTriggers[selectTriggers.length - 1];
    await user.click(formatSelector);

    // Wait for options to appear
    await waitFor(() => {
      expect(screen.getByText('CSV')).toBeDefined();
      expect(screen.getByText('JSON')).toBeDefined();
      expect(screen.getByText('Markdown')).toBeDefined();
    });
  });

  it('download button triggers download with selected format', async () => {
    render(<GeneratedItemsTable items={mockFinalOutput.final_items} fullOutput={mockFinalOutput} />);

    const user = userEvent.setup();

    // Get format selector and download button
    const selectTriggers = screen.getAllByRole('combobox');
    const formatSelector = selectTriggers[selectTriggers.length - 1];
    const downloadButton = screen.getByRole('button', { name: /download/i });

    // Select JSON format
    await user.click(formatSelector);
    await waitFor(() => screen.getByText('JSON'));
    await user.click(screen.getByText('JSON'));

    // Click download
    await user.click(downloadButton);

    // Verify blob was created and download triggered
    await waitFor(() => {
      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockClick).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalled();
    });
  });

  it('format selection persists to localStorage', async () => {
    render(<GeneratedItemsTable items={mockFinalOutput.final_items} fullOutput={mockFinalOutput} />);

    const user = userEvent.setup();

    // Get format selector
    const selectTriggers = screen.getAllByRole('combobox');
    const formatSelector = selectTriggers[selectTriggers.length - 1];

    // Select Markdown format
    await user.click(formatSelector);
    await waitFor(() => screen.getByText('Markdown'));
    await user.click(screen.getByText('Markdown'));

    // Verify localStorage was called
    await waitFor(() => {
      expect(global.localStorage.setItem).toHaveBeenCalledWith('mapig-export-format', 'markdown');
    });
  });

  it('format loads from localStorage on mount', () => {
    // Set localStorage before render
    mockLocalStorage['mapig-export-format'] = 'json';

    render(<GeneratedItemsTable items={mockFinalOutput.final_items} fullOutput={mockFinalOutput} />);

    // Verify getItem was called
    expect(global.localStorage.getItem).toHaveBeenCalledWith('mapig-export-format');
  });

  it('download button is disabled when fullOutput is null', () => {
    render(<GeneratedItemsTable items={mockFinalOutput.final_items} fullOutput={null} />);

    const downloadButton = screen.getByRole('button', { name: /download/i });
    expect(downloadButton).toHaveProperty('disabled', true);
  });

  it('item count summary displays correctly', () => {
    render(<GeneratedItemsTable items={mockFinalOutput.final_items} fullOutput={mockFinalOutput} />);

    // Look for "1 items generated" text
    expect(screen.getByText(/1 items generated/i)).toBeDefined();
  });
});
