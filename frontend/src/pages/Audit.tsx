import { AlertCircle, ArrowRight, CheckCircle2, FileSearch, ReceiptText, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { formatDate, formatMonth, formatPaise } from '../api/format';
import type { AuditResponse, Decision, Finding, Lang } from '../api/types';
import { translate } from '../i18n';
import { EvidencePanel } from '../components/EvidencePanel';
import { ImpactStrip } from '../components/ImpactStrip';
import { DecisionBadge, StatusBadge } from '../components/StatusBadge';

interface Props {
  auditId: string;
  lang: Lang;
  onLetter: (auditId: string) => void;
  onBack: () => void;
  onError: (message: string) => void;
}

export function Audit({ auditId, lang, onLetter, onBack, onError }: Props) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    let active = true;
    api.getAudit(auditId)
      .then((result) => { if (active) setAudit(result); })
      .catch((error: unknown) => onError(error instanceof Error ? error.message : t('request_failed')));
    return () => { active = false; };
  }, [auditId]); // eslint-disable-line react-hooks/exhaustive-deps

  const decide = async (finding: Finding, decision: Decision) => {
    setBusyId(finding.id);
    try {
      await api.decide(finding.id, decision);
      // Re-read the audit so decisions AND the derived impact are consistent.
      setAudit(await api.getAudit(auditId));
    } catch (error) {
      onError(error instanceof Error ? error.message : t('request_failed'));
    } finally {
      setBusyId(null);
    }
  };

  const generate = async () => {
    setGenerating(true);
    try {
      onLetter(auditId);
    } finally {
      setGenerating(false);
    }
  };

  if (!audit) return <div className="loading-card"><span className="skeleton" /><span className="skeleton" /></div>;

  const approved = audit.findings.filter((f) => f.decision === 'approved' && f.status === 'confirmed').length;
  const confirmed = audit.findings.filter((f) => f.status === 'confirmed');
  const confirmedTotal = confirmed.reduce((sum, f) => sum + (f.difference_paise ?? 0), 0);

  return (
    <>
      <div className="page-title-row">
        <div>
          <span className="eyebrow">{t('auditTitle')}</span>
          <h1>{formatMonth(audit.period_start, lang)}</h1>
          <p className="muted">{t('period')}: {formatDate(audit.period_start, lang)}</p>
        </div>
      </div>

      <section className="panel invoice-panel" aria-label={t('invoiceSummary')}>
        <div className="invoice-title"><ReceiptText size={18} /> <strong>{t('invoiceSummary')}</strong></div>
        <div className="invoice-values">
          <div><span>{t('rent')}</span><strong>{formatPaise(audit.invoice.rent_paise)}</strong></div>
          <div><span>{t('maintenance')}</span><strong>{formatPaise(audit.invoice.maintenance_paise)}</strong></div>
        </div>
      </section>

      <ImpactStrip impact={audit.impact} lang={lang} compact />

      <section className="findings-section" aria-labelledby="findings-heading">
        <div className="section-heading">
          <h2 id="findings-heading">{t('findings')}</h2>
          <span className="count-chip">{audit.findings.length}</span>
        </div>
        {audit.findings.length === 0 && (
          <div className="empty-state success-empty"><CheckCircle2 size={32} /><p>{t('noFindings')}</p></div>
        )}
        <div className="findings-list">
          {audit.findings.map((finding) => {
            const isConfirmed = finding.status === 'confirmed';
            return (
              <article className={`finding-card ${isConfirmed ? 'finding-confirmed' : 'finding-uncertain'}`} key={finding.id}>
                <div className="finding-head">
                  <div>
                    <div className="finding-badges">
                      <StatusBadge status={finding.status} lang={lang} />
                      <DecisionBadge decision={finding.decision} lang={lang} />
                    </div>
                    <h3>{t(`check_${finding.check}` as Parameters<typeof translate>[1])}</h3>
                    <p className="finding-message">{finding.message}</p>
                    {!isConfirmed && finding.reason && (
                      <p className="uncertain-reason"><AlertCircle size={15} /> {t(`reason_${finding.reason}` as Parameters<typeof translate>[1])}</p>
                    )}
                  </div>
                </div>

                {isConfirmed ? (
                  <div className="amount-grid">
                    <div><span>{t('billed')}</span><strong>{formatPaise(finding.billed_paise)}</strong></div>
                    <div><span>{t('expected')}</span><strong>{formatPaise(finding.expected_paise)}</strong></div>
                    <div className="amount-highlight"><span>{t('difference')}</span><strong>{formatPaise(finding.difference_paise)}</strong></div>
                  </div>
                ) : (
                  <p className="uncertain-note"><AlertCircle size={15} /> {t('uncertainNote')}</p>
                )}

                <EvidencePanel evidence={finding.evidence} calculation={finding.calculation} lang={lang} openByDefault={isConfirmed} />

                {isConfirmed && (
                  <div className="decision-row">
                    {finding.decision ? (
                      <>
                        <span className="muted small">{t(finding.decision)}</span>
                        <button className="button button-ghost button-sm" disabled={busyId === finding.id} onClick={() => decide(finding, finding.decision === 'approved' ? 'rejected' : 'approved')}>
                          {t('changeDecision')}
                        </button>
                      </>
                    ) : (
                      <>
                        <button className="button button-primary button-sm" disabled={busyId === finding.id} onClick={() => decide(finding, 'approved')}>
                          <CheckCircle2 size={16} /> {t('approve')}
                        </button>
                        <button className="button button-secondary button-sm" disabled={busyId === finding.id} onClick={() => decide(finding, 'rejected')}>
                          <XCircle size={16} /> {t('reject')}
                        </button>
                      </>
                    )}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </section>

      <div className="sticky-action" role="region" aria-label={t('generateLetter')}>
        <div className="sticky-inner">
          <div>
            <span className="sticky-label">{t('confirmTotal')}</span>
            <strong className="sticky-value">{formatPaise(confirmedTotal)}</strong>
          </div>
          <button className="button button-primary" disabled={approved === 0 || generating} onClick={generate}>
            <FileSearch size={17} /> {generating ? t('generating') : `${t('generateLetter')} (${approved})`}
            <ArrowRight size={16} />
          </button>
        </div>
        <p className="sticky-note">{approved === 0 ? t('noApproved') : t('shareNote')}</p>
      </div>
      <button className="text-back" onClick={onBack}>← {t('back')}</button>
    </>
  );
}
