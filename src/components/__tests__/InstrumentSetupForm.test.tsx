import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { InstrumentSetupForm } from '../InstrumentSetupForm';

// Mock localStorage
const mockLocalStorage: Record<string, string> = {};

beforeEach(() => {
  // Reset localStorage mock
  Object.keys(mockLocalStorage).forEach(key => delete mockLocalStorage[key]);

  global.localStorage = {
    getItem: vi.fn((key: string) => mockLocalStorage[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      mockLocalStorage[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete mockLocalStorage[key];
    }),
    clear: vi.fn(() => {
      Object.keys(mockLocalStorage).forEach(key => delete mockLocalStorage[key]);
    }),
    key: vi.fn(),
    length: 0,
  };
});

describe('InstrumentSetupForm - Model Provider Selector (API-06)', () => {
  it('renders model provider selector as first field', () => {
    const mockOnSubmit = vi.fn();
    render(<InstrumentSetupForm onSubmit={mockOnSubmit} />);

    // Find LLM Provider label
    const providerLabel = screen.getByText('LLM Provider');
    expect(providerLabel).toBeDefined();

    // Find the select trigger (combobox)
    const selectTriggers = screen.getAllByRole('combobox');
    expect(selectTriggers.length).toBeGreaterThan(0);

    // Verify help text is displayed
    const helpText = screen.getByText(/Choose Claude for smart model allocation/i);
    expect(helpText).toBeDefined();
  });

  it('model provider selector has claude and openai options', async () => {
    const mockOnSubmit = vi.fn();
    render(<InstrumentSetupForm onSubmit={mockOnSubmit} />);

    const user = userEvent.setup();

    // Get all comboboxes - first one should be model_provider
    const selectTriggers = screen.getAllByRole('combobox');
    const modelProviderSelect = selectTriggers[0];

    // Click to open dropdown
    await user.click(modelProviderSelect);

    // Wait for options to appear
    await waitFor(() => {
      // Look for both options in the dropdown
      const claudeOptions = screen.getAllByText(/Claude.*Default/i);
      const openaiOptions = screen.getAllByText('OpenAI');

      expect(claudeOptions.length).toBeGreaterThan(0);
      expect(openaiOptions.length).toBeGreaterThan(0);
    });
  });

  it('model provider defaults to claude', async () => {
    const mockOnSubmit = vi.fn();
    render(<InstrumentSetupForm onSubmit={mockOnSubmit} />);

    // Get all comboboxes - first one should be model_provider
    const selectTriggers = screen.getAllByRole('combobox');
    const modelProviderSelect = selectTriggers[0];

    // Check the displayed value (should show Claude Default)
    await waitFor(() => {
      const displayedValue = modelProviderSelect.textContent;
      expect(displayedValue).toContain('Claude');
    });
  });

  it('model provider selection updates form state', async () => {
    const mockOnSubmit = vi.fn();
    render(<InstrumentSetupForm onSubmit={mockOnSubmit} />);

    const user = userEvent.setup();

    // Get model provider selector
    const selectTriggers = screen.getAllByRole('combobox');
    const modelProviderSelect = selectTriggers[0];

    // Open dropdown
    await user.click(modelProviderSelect);

    // Wait for options and select OpenAI - use getAllByText to handle multiple instances
    await waitFor(() => {
      const openaiOptions = screen.getAllByText('OpenAI');
      expect(openaiOptions.length).toBeGreaterThan(0);
    });

    // Click on the last OpenAI option (the one in the dropdown menu)
    const openaiOptions = screen.getAllByText('OpenAI');
    await user.click(openaiOptions[openaiOptions.length - 1]);

    // Verify selection changed
    await waitFor(() => {
      const displayedValue = modelProviderSelect.textContent;
      expect(displayedValue).toContain('OpenAI');
    });
  });

  it('model provider selection persists to localStorage on form submission', async () => {
    const mockOnSubmit = vi.fn();
    render(<InstrumentSetupForm onSubmit={mockOnSubmit} isPending={false} />);

    const user = userEvent.setup();

    // Fill required fields
    const constructNameInput = screen.getByLabelText(/Construct name/i);
    const constructDefInput = screen.getByLabelText(/Construct definition/i);
    const targetPopInput = screen.getByLabelText(/Target population/i);

    await user.type(constructNameInput, 'Test Construct');
    await user.type(constructDefInput, 'Definition here for testing');
    await user.type(targetPopInput, 'Adults');

    // Select OpenAI provider
    const selectTriggers = screen.getAllByRole('combobox');
    const modelProviderSelect = selectTriggers[0];
    await user.click(modelProviderSelect);
    await waitFor(() => {
      const openaiOptions = screen.getAllByText('OpenAI');
      expect(openaiOptions.length).toBeGreaterThan(0);
    });
    const openaiOptions = screen.getAllByText('OpenAI');
    await user.click(openaiOptions[openaiOptions.length - 1]);

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Generate items/i });
    await user.click(submitButton);

    // Verify localStorage was called with model_provider
    await waitFor(() => {
      expect(global.localStorage.setItem).toHaveBeenCalled();
      const setItemCalls = (global.localStorage.setItem as any).mock.calls;
      const savedData = setItemCalls.find((call: any[]) => call[0] === 'mapig-instrument-setup');
      expect(savedData).toBeDefined();

      if (savedData) {
        const parsedData = JSON.parse(savedData[1]);
        expect(parsedData.model_provider).toBe('openai');
      }
    });
  });
});
