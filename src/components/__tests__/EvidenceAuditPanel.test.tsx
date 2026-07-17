import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EvidenceAuditPanel } from '../EvidenceAuditPanel';
import type { AuditMetadata } from '@/lib/types';

function renderExpanded(audit: AuditMetadata) {
  const view = render(<EvidenceAuditPanel audit={audit} />);
  fireEvent.click(screen.getByRole('button', { name: /show details/i }));
  return view;
}

// Mock toast
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe('EvidenceAuditPanel - Cost Tracking Display (API-07)', () => {
  const baseAudit: AuditMetadata = {
    thread_id: 'thread_123',
    run_id: 'run_456',
    timestamp_utc: '2026-03-09T00:00:00Z',
    iteration_count: 2,
    stop_reason: 'completed',
    model_info: { mode: 'claude' },
    approved_sources: ['https://example.com/source1'],
    validation_attempts: 1,
    validation_failures: 0,
  };

  it('displays cost breakdown when cost fields are defined', () => {
    const auditWithCosts: AuditMetadata = {
      ...baseAudit,
      opus_cost: 1.25,
      sonnet_cost: 0.45,
      openai_cost: 0,
      total_cost: 1.70,
    };

    renderExpanded(auditWithCosts);

    // Find cost section heading
    const costHeading = screen.getByText(/API Cost Breakdown/i);
    expect(costHeading).toBeDefined();

    // Verify Opus cost is displayed
    const opusCost = screen.getByText(/Claude Opus.*Validation/i);
    expect(opusCost).toBeDefined();
    expect(screen.getByText('$1.25')).toBeDefined();

    // Verify Sonnet cost is displayed
    const sonnetCost = screen.getByText(/Claude Sonnet.*Other Agents/i);
    expect(sonnetCost).toBeDefined();
    expect(screen.getByText('$0.45')).toBeDefined();

    // Verify total cost is displayed
    const totalText = screen.getByText('Total:');
    expect(totalText).toBeDefined();
    expect(screen.getByText('$1.70')).toBeDefined();
  });

  it('hides cost section when cost fields are undefined', () => {
    const auditWithoutCosts: AuditMetadata = {
      ...baseAudit,
      // No cost fields
    };

    renderExpanded(auditWithoutCosts);

    // Cost section should not be present
    const costHeading = screen.queryByText(/API Cost Breakdown/i);
    expect(costHeading).toBeNull();
  });

  it('only shows non-zero cost lines', () => {
    const auditWithPartialCosts: AuditMetadata = {
      ...baseAudit,
      opus_cost: 2.50,
      sonnet_cost: 0, // Zero cost
      openai_cost: 0, // Zero cost
      total_cost: 2.50,
    };

    renderExpanded(auditWithPartialCosts);

    // Opus should be displayed (non-zero)
    expect(screen.getByText(/Claude Opus.*Validation/i)).toBeDefined();
    const costElements = screen.getAllByText('$2.50');
    expect(costElements.length).toBeGreaterThan(0); // At least one (could be in Opus line and Total line)

    // Sonnet should NOT be displayed (zero cost)
    expect(screen.queryByText(/Claude Sonnet.*Other Agents/i)).toBeNull();

    // OpenAI should NOT be displayed (zero cost)
    expect(screen.queryByText(/OpenAI:/i)).toBeNull();

    // Total should still be displayed
    expect(screen.getByText('Total:')).toBeDefined();
  });

  it('formats costs as USD with 2 decimal places', () => {
    const auditWithCosts: AuditMetadata = {
      ...baseAudit,
      opus_cost: 3.456, // Should round to $3.46
      sonnet_cost: 0.123, // Should round to $0.12
      total_cost: 3.579, // Should round to $3.58
    };

    renderExpanded(auditWithCosts);

    // Check formatting (toFixed(2) should be applied)
    // The component uses .toFixed(2) so we should see exactly 2 decimal places
    const allCosts = screen.getAllByText(/\$\d+\.\d{2}/);
    expect(allCosts.length).toBeGreaterThan(0);

    // Verify specific values
    expect(screen.getByText('$3.46')).toBeDefined();
    expect(screen.getByText('$0.12')).toBeDefined();
    expect(screen.getByText('$3.58')).toBeDefined();
  });

  it('displays all three provider costs when all are non-zero', () => {
    const auditWithAllCosts: AuditMetadata = {
      ...baseAudit,
      opus_cost: 1.00,
      sonnet_cost: 0.50,
      openai_cost: 0.75,
      total_cost: 2.25,
    };

    renderExpanded(auditWithAllCosts);

    // All three provider lines should be present
    expect(screen.getByText(/Claude Opus.*Validation/i)).toBeDefined();
    expect(screen.getByText(/Claude Sonnet.*Other Agents/i)).toBeDefined();
    expect(screen.getByText(/OpenAI:/i)).toBeDefined();

    // All costs should be displayed
    expect(screen.getByText('$1.00')).toBeDefined();
    expect(screen.getByText('$0.50')).toBeDefined();
    expect(screen.getByText('$0.75')).toBeDefined();
    expect(screen.getByText('$2.25')).toBeDefined();
  });

  it('renders cost section only when total_cost is a positive number', () => {
    // Only opus_cost defined, no total_cost — should NOT show
    const auditOnlyOpus: AuditMetadata = {
      ...baseAudit,
      opus_cost: 1.00,
    };

    const { rerender } = renderExpanded(auditOnlyOpus);
    expect(screen.queryByText(/API Cost Breakdown/i)).toBeNull();

    // Zero total_cost — should NOT show
    rerender(<EvidenceAuditPanel audit={{ ...baseAudit, total_cost: 0 }} />);
    expect(screen.queryByText(/API Cost Breakdown/i)).toBeNull();

    // Positive total_cost — should show
    rerender(<EvidenceAuditPanel audit={{ ...baseAudit, opus_cost: 1.00, total_cost: 1.00 }} />);
    expect(screen.getByText(/API Cost Breakdown/i)).toBeDefined();
  });
});
