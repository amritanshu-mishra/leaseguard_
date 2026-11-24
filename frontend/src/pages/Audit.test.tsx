import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../api/client';
import type { AuditResponse, Finding, LetterResponse } from '../api/types';
import { Audit } from './Audit';

vi.mock('../api/client', () => ({
  api: {
    getAudit: vi.fn(),
    decide: vi.fn(),
    letter: vi.fn(),
  },
}));

const finding: Finding = {
  id: 'f1',
  check: 'rent_escalation',
  status: 'confirmed',
  reason: null,
  message: 'Rent billed is Rs. 44,000 but the controlling terms give Rs. 42,000.',
  billed_paise: 4_400_000,
  expected_paise: 4_200_000,
  difference_paise: 200_000,
  decision: null,
  evidence: [
    {
      term_type: 'escalation_rate_bp',
      label: 'Annual escalation',
      value: 500,
      unit: 'basis points',
      document: 'Amendment 1',
      document_file: 'amendment1',
      page: 1,
      effective_date: '2026-01-01',
      quote: 'escalation shall not exceed five percent (5%) per annum',
      validated: true,
      ambiguous: false,
    },
  ],
  calculation: ['Base rent: Rs. 40,000 per month', 'Anniversary 1: 500 bp → Rs. 42,000'],
};

const audit: AuditResponse = {
  audit_id: 'a1',
  lease_id: 'l1',
  period_start: '2026-04-01',
  invoice: { period_start: '2026-04-01', rent_paise: 4_400_000, maintenance_paise: 520_000 },
  findings: [finding],
  impact: {
    excess_detected_paise: 200_000,
    awaiting_review_paise: 200_000,
    confirmed_count: 1,
    uncertain_count: 0,
    document_count: 3,
    audit_count: 1,
    estimated_minutes_saved: 14,
    estimate_basis: 'Estimate',
    disclaimer: 'No money is recovered or sent by LeaseGuard.',
  },
};

const letter: LetterResponse = {
  letter: 'Subject: Invoice April 2026 - discrepancies for review',
  share_text: 'Subject: Invoice April 2026 - discrepancies for review',
  whatsapp_url: 'https://wa.me/?text=test',
  included_count: 1,
  language: 'en',
};

describe('Audit screen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getAudit).mockResolvedValue(audit);
    vi.mocked(api.decide).mockResolvedValue({ ...finding, decision: 'approved' });
    vi.mocked(api.letter).mockResolvedValue(letter);
  });

  it('renders the refreshed audit payload without crashing', async () => {
    render(<Audit auditId="a1" lang="en" onLetter={vi.fn()} onBack={vi.fn()} onError={vi.fn()} />);
    expect(await screen.findByText('April 2026')).toBeTruthy();
    expect(screen.getAllByText('₹44,000').length).toBeGreaterThan(0);
    expect(screen.getAllByText('₹42,000').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Rent escalation/).length).toBeGreaterThan(0);
    expect(screen.getByText(/escalation shall not exceed five percent/)).toBeTruthy();
    expect(screen.getAllByText(/500 bp/).length).toBeGreaterThan(0);
  });

  it('re-reads the audit after a decision so impact and approval stay in sync', async () => {
    const approved = { ...audit, findings: [{ ...finding, decision: 'approved' as const }], impact: { ...audit.impact, awaiting_review_paise: 0 } };
    vi.mocked(api.getAudit).mockResolvedValueOnce(audit).mockResolvedValueOnce(approved);
    render(<Audit auditId="a1" lang="en" onLetter={vi.fn()} onBack={vi.fn()} onError={vi.fn()} />);
    await screen.findByText('April 2026');
    fireEvent.click(screen.getByRole('button', { name: /Approve/i }));
    await waitFor(() => expect(api.getAudit).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getAllByText('Approved').length).toBeGreaterThan(0));
  });
});
