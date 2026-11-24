import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../api/client';
import type { Config, DemoScenario } from '../api/types';
import { Dashboard } from './Dashboard';

vi.mock('../api/client', () => ({ api: { loadDemo: vi.fn(), createLease: vi.fn() } }));

const scenarios = [
  {
    id: 'amendment',
    label: 'Amendment controls',
    description: 'Lease 10%, amendment 5%.',
    expected: '2 discrepancies',
    documents: ['lease.txt', 'amendment1.txt', 'invoice_apr2026.txt'],
  },
  {
    id: 'conflict',
    label: 'Conflicting amendments',
    description: 'Two amendments, same date.',
    expected: 'Conflict flagged',
    documents: ['lease.txt', 'amendment_5.txt', 'amendment_7.txt'],
  },
] as DemoScenario[];

const config = { provider: 'fixtures', max_upload_mb: 10 } as Config;

describe('Dashboard scenario picker', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.loadDemo).mockResolvedValue({
      lease: { id: 'l1' } as never,
      documents: [],
      scenario: scenarios[0],
    });
  });

  it('renders dynamic scenarios and loads the chosen one', async () => {
    const onLoaded = vi.fn();
    render(
      <Dashboard
        lang="en"
        config={config}
        scenarios={scenarios}
        leases={[]}
        impact={null}
        onOpenLease={vi.fn()}
        onLoaded={onLoaded}
        onNewLease={vi.fn()}
        onRefresh={vi.fn().mockResolvedValue(undefined)}
        onError={vi.fn()}
      />,
    );
    expect(screen.getByText('Try a demo scenario')).toBeTruthy();
    expect(screen.getByText('Conflicting amendments')).toBeTruthy();
    const buttons = screen.getAllByRole('button', { name: /Load this case/ });
    expect(buttons).toHaveLength(2);
    fireEvent.click(buttons[1]);
    await waitFor(() => expect(api.loadDemo).toHaveBeenCalledWith('conflict', 'en'));
    await waitFor(() => expect(onLoaded).toHaveBeenCalledWith('l1'));
  });
});
