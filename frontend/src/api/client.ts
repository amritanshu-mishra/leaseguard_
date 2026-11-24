import type { AuditResponse, Config, Decision, DemoScenario, Finding, Impact, LeaseDetail, LeaseSummary, LetterResponse, UploadResult } from './types';

const BASE = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/$/, '');

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      headers: init.body instanceof FormData ? init.headers : { 'Content-Type': 'application/json', ...init.headers },
    });
  } catch {
    throw new ApiError('network_error', 'Cannot reach the server. Check your connection and try again.', 0);
  }
  if (!response.ok) {
    let body: { error?: { code?: string; message?: string } } = {};
    try {
      body = (await response.json()) as typeof body;
    } catch {
      /* keep the generic message */
    }
    throw new ApiError(body.error?.code ?? 'request_failed', body.error?.message ?? 'Request failed.', response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  config: () => request<Config>('/config'),
  leases: () => request<LeaseSummary[]>('/leases'),
  lease: (id: string) => request<LeaseDetail>(`/leases/${id}`),
  createLease: (label: string, startDate: string) =>
    request<LeaseSummary>('/leases', { method: 'POST', body: JSON.stringify({ property_label: label, start_date: startDate }) }),
  deleteLease: (id: string) => request<void>(`/leases/${id}`, { method: 'DELETE' }),
  updateLease: (id: string, label: string, startDate: string) =>
    request<LeaseSummary>(`/leases/${id}`, { method: 'PATCH', body: JSON.stringify({ property_label: label, start_date: startDate }) }),
  demoScenarios: (lang: 'en' | 'hi') => request<DemoScenario[]>(`/demo/scenarios?lang=${lang}`),
  loadDemo: (scenario: string, lang: 'en' | 'hi') =>
    request<{ lease: LeaseSummary; documents: string[]; scenario: DemoScenario }>(
      `/demo/load?scenario=${encodeURIComponent(scenario)}&lang=${lang}`,
      { method: 'POST' },
    ),
  uploadDemoDocument: (leaseId: string, kind: string, effectiveDate: string | null) =>
    request<UploadResult>(
      `/leases/${leaseId}/demo/documents?kind=${encodeURIComponent(kind)}${
        effectiveDate ? `&effective_date=${effectiveDate}` : ''
      }`,
      { method: 'POST' },
    ),
  upload: (leaseId: string, kind: string, effectiveDate: string | null, file: File) => {
    const form = new FormData();
    form.append('kind', kind);
    if (effectiveDate) form.append('effective_date', effectiveDate);
    form.append('file', file);
    return request<UploadResult>(`/leases/${leaseId}/documents`, { method: 'POST', body: form });
  },
  audit: (leaseId: string) => request<AuditResponse>(`/leases/${leaseId}/audits`, { method: 'POST' }),
  getAudit: (auditId: string) => request<AuditResponse>(`/audits/${auditId}`),
  decide: (findingId: string, decision: Decision) =>
    request<Finding>(`/findings/${findingId}`, { method: 'PATCH', body: JSON.stringify({ decision }) }),
  letter: (auditId: string, lang: 'en' | 'hi') => request<LetterResponse>(`/audits/${auditId}/letter?lang=${lang}`, { method: 'POST' }),
  impact: () => request<Impact>('/impact'),
};
