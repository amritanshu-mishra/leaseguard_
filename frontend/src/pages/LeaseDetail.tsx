import { ArrowRight, FileCheck2, FileText, PlayCircle, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { formatDate, formatPaise } from '../api/format';
import type { Config, Lang, LeaseDetail as LeaseDetailType, Term, UploadResult } from '../api/types';
import { translate } from '../i18n';
import { EvidencePanel } from '../components/EvidencePanel';
import { UploadPanel } from '../components/UploadPanel';
import { VerifiedBadge } from '../components/StatusBadge';

interface Props {
  leaseId: string;
  lang: Lang;
  config: Config | null;
  onRunAudit: (leaseId: string) => void;
  onDeleted: () => void;
  onError: (message: string) => void;
}

const kindLabel = { lease: 'leaseDoc', amendment: 'amendment', invoice: 'invoice' } as const;

function termValue(term: Term): string {
  if (term.value === null) return '—';
  return term.type === 'escalation_rate_bp' ? `${term.value} bp` : formatPaise(term.value);
}

export function LeaseDetail({ leaseId, lang, config, onRunAudit, onDeleted, onError }: Props) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const [lease, setLease] = useState<LeaseDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [startDraft, setStartDraft] = useState('');
  const [savedNote, setSavedNote] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const detail = await api.lease(leaseId);
      setLease(detail);
      setStartDraft(detail.start_date);
    } catch (error) {
      onError(error instanceof Error ? error.message : t('request_failed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [leaseId]); // eslint-disable-line react-hooks/exhaustive-deps

  const onUploaded = (_result: UploadResult) => { void load(); };

  const saveStart = async () => {
    if (!lease || !startDraft || startDraft === lease.start_date) return;
    try {
      const updated = await api.updateLease(lease.id, lease.property_label, startDraft);
      setLease((current) => (current ? { ...current, ...updated, documents: current.documents, terms: current.terms, invoices: current.invoices } : current));
      setSavedNote(true);
      window.setTimeout(() => setSavedNote(false), 2500);
    } catch (error) {
      onError(error instanceof Error ? error.message : t('request_failed'));
    }
  };

  const remove = async () => {
    if (!window.confirm(`${t('deleteLease')}?`)) return;
    try {
      await api.deleteLease(leaseId);
      onDeleted();
    } catch (error) {
      onError(error instanceof Error ? error.message : t('request_failed'));
    }
  };

  if (loading || !lease) return <div className="loading-card"><span className="skeleton" /><span className="skeleton" /></div>;

  // The latest validated term of each type is the one in force for this demo period.
  const controlling = new Map<string, string>();
  for (const term of lease.terms) {
    if (!term.validated || term.value === null) continue;
    const current = controlling.get(term.type);
    if (!current || term.effective_date > current) controlling.set(term.type, term.effective_date);
  }

  return (
    <div className="detail-layout">
      <div className="detail-main">
        <div className="page-title-row">
          <div>
            <h1>{lease.property_label}</h1>
            <p className="muted">{formatDate(lease.start_date, lang)} · {lease.document_count} {t('documents')} · {lease.invoice_count} {t('invoices')}</p>
          </div>
          <button className="button button-danger-ghost button-sm" onClick={remove}><Trash2 size={15} /> {t('deleteLease')}</button>
        </div>

        <section className="panel" aria-labelledby="docs-heading">
          <h2 id="docs-heading">{t('documentsTitle')}</h2>
          {lease.documents.length === 0 ? (
            <p className="muted">{t('noDocuments')}</p>
          ) : (
            <ul className="document-list">
              {lease.documents.map((doc) => (
                <li key={doc.id}>
                  <span className={`doc-icon doc-${doc.kind}`}><FileText size={17} /></span>
                  <div>
                    <strong>{doc.name}</strong>
                    <small className="muted">{doc.pages} {t('page').toLowerCase()}{doc.pages > 1 ? 's' : ''} · SHA-256 {doc.sha256.slice(0, 10)}…</small>
                  </div>
                  <span className="kind-tag">{t(kindLabel[doc.kind])}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel" aria-labelledby="terms-heading">
          <div className="section-heading">
            <h2 id="terms-heading">{t('termsTitle')}</h2>
            <span className="count-chip">{lease.terms.length}</span>
          </div>
          {lease.terms.length === 0 ? (
            <p className="muted">{t('noDocuments')}</p>
          ) : (
            <div className="term-list">
              {lease.terms.map((term, index) => {
                const inForce = controlling.get(term.type) === term.effective_date && term.validated && term.value !== null;
                return (
                  <article className={`term-row ${inForce ? '' : 'term-muted'}`} key={`${term.type}-${index}`}>
                    <div className="term-top">
                      <div>
                        <strong>{term.label}</strong>
                        <div className="term-badges">
                          <span className={`mini-badge ${inForce ? 'mini-teal' : 'mini-neutral'}`}>{t(inForce ? 'controlling' : 'superseded')}</span>
                          <VerifiedBadge validated={term.validated} lang={lang} />
                        </div>
                      </div>
                      <span className="term-value">{termValue(term)}</span>
                    </div>
                    <p className="term-source muted small">
                      {term.document} · {t('page')} {term.page} · {formatDate(term.effective_date, lang)}
                    </p>
                    <EvidencePanel
                      evidence={[term]}
                      calculation={[]}
                      lang={lang}
                      openByDefault={false}
                    />
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>

      <aside className="detail-side">
        <UploadPanel
          leaseId={leaseId}
          lang={lang}
          maxMb={config?.max_upload_mb ?? 10}
          demoMode={config?.live === false}
          onUploaded={onUploaded}
          onError={onError}
        />
        <div className="side-card">
          <FileCheck2 size={22} />
          <h3>{t('auditTitle')}</h3>
          <p className="muted small">{lease.invoice_count > 0 ? t('auditReady') : t('no_invoice')}</p>
          <label className="field">
            <span>{t('leaseStartDate')}</span>
            <input type="date" value={startDraft} onChange={(event) => setStartDraft(event.target.value)} />
          </label>
          <button className="button button-secondary button-sm" onClick={saveStart} disabled={startDraft === lease.start_date || !startDraft}>
            {savedNote ? t('saved') : t('save')}
          </button>
          <button className="button button-primary button-full" onClick={() => onRunAudit(leaseId)} disabled={lease.invoice_count === 0}>
            <PlayCircle size={17} /> {t('runAudit')} <ArrowRight size={16} />
          </button>
        </div>
      </aside>
    </div>
  );
}
