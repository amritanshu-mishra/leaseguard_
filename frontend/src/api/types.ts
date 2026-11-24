export type Lang = 'en' | 'hi';
export type Decision = 'approved' | 'rejected';

export interface Impact {
  excess_detected_paise: number;
  awaiting_review_paise: number;
  confirmed_count: number;
  uncertain_count: number;
  document_count: number;
  audit_count: number;
  estimated_minutes_saved: number;
  estimate_basis: string;
  disclaimer: string;
}

export interface Evidence {
  term_type: string;
  label: string;
  value: number | null;
  unit: string;
  document: string;
  document_file: string;
  page: number;
  effective_date: string;
  quote: string;
  validated: boolean;
  ambiguous: boolean;
}

export interface Finding {
  id: string;
  check: 'rent_escalation' | 'maintenance_cap' | string;
  status: 'confirmed' | 'uncertain';
  reason: string | null;
  message: string;
  billed_paise: number | null;
  expected_paise: number | null;
  difference_paise: number | null;
  decision: Decision | null;
  evidence: Evidence[];
  calculation: string[];
}

export interface Term {
  type: string;
  term_type: string;
  label: string;
  value: number | null;
  unit: string;
  document: string;
  document_file: string;
  effective_date: string;
  quote: string;
  page: number;
  validated: boolean;
  ambiguous: boolean;
  confidence: number;
}

export interface DocumentRow {
  id: string;
  name: string;
  kind: 'lease' | 'amendment' | 'invoice';
  sha256: string;
  pages: number;
  effective_date: string | null;
}

export interface Invoice {
  period_start: string;
  rent_paise: number;
  maintenance_paise: number;
}

export interface DemoScenario {
  id: string;
  label_en: string;
  label_hi: string;
  description_en: string;
  description_hi: string;
  expected_en: string;
  expected_hi: string;
  label: string;
  description: string;
  expected: string;
  documents: string[];
}

export interface LeaseSummary {
  id: string;
  scenario_id?: string | null;
  property_label: string;
  start_date: string;
  created_at: string;
  document_count: number;
  invoice_count: number;
  finding_count: number;
  awaiting_count: number;
  impact: Impact;
}

export interface LeaseDetail extends LeaseSummary {
  documents: DocumentRow[];
  terms: Term[];
  invoices: Invoice[];
}

export interface AuditResponse {
  audit_id: string;
  lease_id: string;
  period_start: string;
  invoice: Invoice;
  findings: Finding[];
  impact: Impact;
}

export interface LetterResponse {
  letter: string;
  share_text: string;
  whatsapp_url: string;
  included_count: number;
  language: Lang;
}

export interface Config {
  provider: string;
  live: boolean;
  model: string | null;
  json_mode: string;
  api_key_configured: boolean;
  max_upload_mb: number;
  degraded_reason: string;
  demo_user: string;
}

export interface UploadResult {
  document: string;
  kind: string;
  sha256: string;
  pages: number;
  terms_found?: number;
  terms_unverified?: number;
  invoice?: Invoice;
}
