import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import EvaluationDashboard from '@/components/EvaluationDashboard';

const metrics = (score: number, total: number) => ({
  quality_parity_score: score,
  construct_fidelity_score: score,
  stylistic_similarity_score: score,
  psychometric_properties_score: score,
  overall_score: score,
  total_comparisons: total,
});

const improvement = {
  overall_improvement: 17.6,
  quality_parity_improvement: 23.1,
  construct_fidelity_improvement: 21.0,
  stylistic_similarity_improvement: -2.9,
  psychometric_properties_improvement: 25.0,
};

function mockResponse(body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: true, json: async () => body }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('EvaluationDashboard', () => {
  it('shows undetermined success and truthful labels for a synthetic baseline', async () => {
    mockResponse({
      baseline_source: 'synthetic',
      improvement_basis: 'synthetic_reference',
      mode: 'mock',
      pairing_method: 'lexical_nearest_neighbor',
      evaluated_scales: ['A', 'B'],
      failed_scales: [],
      current: metrics(7.5, 25),
      baseline: metrics(6.4, 0),
      improvement,
      success_criteria: {
        meets_improvement_threshold: true,
        all_dimensions_passing: true,
        success: null,
        success_reason: 'Baseline is a synthetic reference, not a measured run.',
      },
    });

    render(<EvaluationDashboard />);
    fireEvent.click(screen.getByRole('button', { name: /run evaluation/i }));

    expect(await screen.findByText('Success Criteria Undetermined')).toBeInTheDocument();
    expect(screen.getByText(/not a measured run\./)).toBeInTheDocument();
    expect(screen.getByText('Stylistic Similarity')).toBeInTheDocument();
    expect(screen.queryByText('Workflow Efficiency')).not.toBeInTheDocument();
    expect(screen.getByText(/-2\.9% vs synthetic reference/)).toBeInTheDocument();
  });

  it('lists failed scales and reports success as not met', async () => {
    mockResponse({
      baseline_source: 'measured',
      improvement_basis: 'measured_baseline',
      failed_scales: [{ name: 'PHQ-9', domain: 'clinical', error: 'judge exploded' }],
      current: metrics(8, 20),
      baseline: metrics(6, 20),
      improvement,
      success_criteria: {
        meets_improvement_threshold: true,
        all_dimensions_passing: true,
        success: false,
        success_reason: '1 benchmark scale(s) failed and were excluded: PHQ-9',
      },
    });

    render(<EvaluationDashboard />);
    fireEvent.click(screen.getByRole('button', { name: /run evaluation/i }));

    expect(await screen.findByText(/Success Criteria Not Met/)).toBeInTheDocument();
    expect(screen.getByText(/1 scale failed/)).toBeInTheDocument();
    expect(screen.getByText(/judge exploded/)).toBeInTheDocument();
  });
});
