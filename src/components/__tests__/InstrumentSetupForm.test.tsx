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

describe('InstrumentSetupForm - Basic Form Functionality', () => {
  it('renders required form fields', () => {
    const mockOnSubmit = vi.fn();
    render(<InstrumentSetupForm onSubmit={mockOnSubmit} />);

    // Verify core required fields are present
    expect(screen.getByLabelText(/Construct name/i)).toBeDefined();
    expect(screen.getByLabelText(/Construct definition/i)).toBeDefined();
    expect(screen.getByLabelText(/Target population/i)).toBeDefined();
    expect(screen.getByLabelText(/Response scale/i)).toBeDefined();
    expect(screen.getByLabelText(/Item count/i)).toBeDefined();
  });

  it('form validates required fields on submission', async () => {
    const mockOnSubmit = vi.fn();
    render(<InstrumentSetupForm onSubmit={mockOnSubmit} />);

    const user = userEvent.setup();

    // Try to submit without filling required fields
    const submitButton = screen.getByRole('button', { name: /Generate items/i });
    await user.click(submitButton);

    // Form should not call onSubmit with invalid data
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('form submits with valid data', async () => {
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

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Generate items/i });
    await user.click(submitButton);

    // Verify form submission
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
      const submitData = mockOnSubmit.mock.calls[0][0];
      expect(submitData.construct_name).toBe('Test Construct');
      expect(submitData.construct_definition).toBe('Definition here for testing');
      expect(submitData.target_population).toBe('Adults');
      // Model provider should default to claude
      expect(submitData.model_provider).toBe('claude');
    });
  });

  it('form data persists to localStorage on submission', async () => {
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

    // Submit form
    const submitButton = screen.getByRole('button', { name: /Generate items/i });
    await user.click(submitButton);

    // Verify localStorage was updated
    await waitFor(() => {
      expect(global.localStorage.setItem).toHaveBeenCalled();
      const setItemCalls = (global.localStorage.setItem as any).mock.calls;
      const savedData = setItemCalls.find((call: any[]) => call[0] === 'mapig-instrument-setup');
      expect(savedData).toBeDefined();

      if (savedData) {
        const parsedData = JSON.parse(savedData[1]);
        expect(parsedData.construct_name).toBe('Test Construct');
        expect(parsedData.model_provider).toBe('claude');
      }
    });
  });
});
