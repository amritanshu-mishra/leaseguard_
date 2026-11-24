import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Config } from '../api/types';
import { SetupModal } from './SetupModal';

describe('Groq setup guide', () => {
  it('shows the exact env file location and key links in Hindi', () => {
    const config = { live: false, provider: 'fixtures' } as Config;
    render(<SetupModal config={config} lang="hi" onClose={vi.fn()} />);
    expect(screen.getByText('Groq कनेक्ट करें (वैकल्पिक)')).toBeTruthy();
    expect(screen.getAllByText(/backend\/\.env/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/LLM_API_KEY/).length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: /API कुंजियाँ/ }).getAttribute('href')).toBe('https://console.groq.com/keys');
    expect(screen.getByRole('link', { name: /मॉडल सूची/ }).getAttribute('href')).toBe('https://console.groq.com/docs/models');
  });
});
