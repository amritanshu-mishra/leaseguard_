import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../api/client';
import type { AuditResponse, Finding, LetterResponse } from '../api/types';
import { Letter } from './Letter';

vi.mock('../api/client', () => ({ api: { getAudit: vi.fn(), letter: vi.fn() } }));

const finding: Finding = {
  id: 'f1',
  check: 'rent_escalation',
  status: 'confirmed',
  reason: null,
  message: 'Rent differs.',
  billed_paise: 4_400_000,
  expected_paise: 4_200_000,
  difference_paise: 200_000,
  decision: 'approved',
  evidence: [],
  calculation: [],
};

const audit = { audit_id: 'a1', lease_id: 'l1', findings: [finding] } as AuditResponse;
const letter: LetterResponse = {
  letter: 'Subject: Invoice April 2026 - discrepancies for review\n1. Rent escalation: excess Rs. 2,000',
  share_text: 'Share text',
  whatsapp_url: 'https://wa.me/?text=Share',
  included_count: 1,
  language: 'en',
};

describe('Letter screen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getAudit).mockResolvedValue(audit);
    vi.mocked(api.letter).mockResolvedValue(letter);
  });

  it('renders approved findings with translated labels and the letter preview', async () => {
    render(<Letter auditId="a1" lang="en" onBack={vi.fn()} onError={vi.fn()} />);
    expect(await screen.findByText(/discrepancies for review/)).toBeTruthy();
    expect(screen.getByText('Rent escalation')).toBeTruthy();
    const shareLink = screen.getByRole('link', { name: /Share on WhatsApp/ });
    expect(shareLink.getAttribute('href')).toBe('https://wa.me/?text=Share');
    fireEvent.click(screen.getByRole('button', { name: /More share options/ }));
    expect(screen.getByText('Share letter on WhatsApp')).toBeTruthy();
    expect(screen.getByRole('link', { name: /Open WhatsApp/ })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Copy text/ })).toBeTruthy();
  });
});
