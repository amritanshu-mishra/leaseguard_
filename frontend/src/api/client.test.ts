import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './client';
import { formatDate, formatPaise } from './format';

describe('money formatting', () => {
  it('uses Indian grouping and integer paise', () => {
    expect(formatPaise(4_200_000)).toBe('₹42,000');
    expect(formatPaise(1_250_000_50)).toBe('₹12,50,000.50');
    expect(formatPaise(null)).toBe('—');
  });
  it('formats dates for both languages', () => {
    expect(formatDate('2026-04-01')).toBe('1 Apr 2026');
    expect(formatDate('2026-04-01', 'hi')).toBe('1 अप्र 2026');
  });
});

import { translate } from '../i18n';

describe('bilingual interface', () => {
  it('translates key actions into Hindi', () => {
    const keys = ['loadSample', 'newLease', 'approve', 'reject', 'generateLetter', 'shareWhatsApp', 'copy'] as const;
    for (const key of keys) {
      const hindi = translate('hi', key);
      expect(hindi).not.toBe(translate('en', key));
      expect(hindi.length).toBeGreaterThan(2);
    }
  });
});


describe('API base path', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('calls the versioned /api/v1 endpoints', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ provider: 'fixtures' }),
    });
    vi.stubGlobal('fetch', fetchMock);
    await api.config();
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/config', expect.anything());
  });
});


describe('demo scenarios API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('requests localized scenarios and loads a selected scenario', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });
    vi.stubGlobal('fetch', fetchMock);
    await api.demoScenarios('hi');
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/demo/scenarios?lang=hi');
    await api.loadDemo('missing-cap', 'hi');
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/demo/load?scenario=missing-cap&lang=hi');
    expect(fetchMock.mock.calls[1][1]).toEqual(expect.objectContaining({ method: 'POST' }));
  });
});
