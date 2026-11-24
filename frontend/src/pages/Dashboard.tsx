import { ArrowRight, FileStack, Loader2, Plus, ShieldCheck, Sparkles, X } from 'lucide-react';
import { useState } from 'react';
import { api } from '../api/client';
import { formatDate, formatPaise } from '../api/format';
import type { Config, DemoScenario, Impact, Lang, LeaseSummary } from '../api/types';
import { translate } from '../i18n';
import { ImpactStrip } from '../components/ImpactStrip';

interface Props {
  lang: Lang;
  config: Config | null;
  scenarios: DemoScenario[];
  leases: LeaseSummary[];
  impact: Impact | null;
  onOpenLease: (id: string) => void;
  onLoaded: (id: string) => void;
  onNewLease: (id: string) => void;
  onRefresh: () => Promise<void>;
  onError: (message: string) => void;
}

export function Dashboard({ lang, config, scenarios, leases, impact, onOpenLease, onLoaded, onNewLease, onRefresh, onError }: Props) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const [busy, setBusy] = useState<'sample' | 'new' | string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [label, setLabel] = useState('');
  const [startDate, setStartDate] = useState('');

  const loadSample = async (scenarioId = 'amendment') => {
    setBusy(scenarioId);
    try {
      const result = await api.loadDemo(scenarioId, lang);
      await onRefresh();
      onLoaded(result.lease.id);
    } catch (error) {
      onError(error instanceof Error ? error.message : t('request_failed'));
    } finally {
      setBusy(null);
    }
  };

  const createLease = async () => {
    if (!label.trim() || !startDate) {
      onError(lang === 'hi' ? 'कृपया नाम और तिथि भरें।' : 'Enter a property name and start date.');
      return;
    }
    setBusy('new');
    try {
      const lease = await api.createLease(label.trim(), startDate);
      setShowForm(false);
      setLabel('');
      setStartDate('');
      await onRefresh();
      onNewLease(lease.id);
    } catch (error) {
      onError(error instanceof Error ? error.message : t('request_failed'));
    } finally {
      setBusy(null);
    }
  };

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow"><Sparkles size={14} /> {config?.live ? t('liveMode') : t('demoMode')}</span>
          <h1>{t('heroTitle')}</h1>
          <p>{t('heroSubtitle')}</p>
          <div className="hero-actions">
            <button className="button button-primary button-lg" onClick={() => loadSample()} disabled={busy !== null}>
              {busy === 'amendment' ? <Loader2 size={18} className="spin" /> : <Sparkles size={18} />}
              {t('loadSample')}
            </button>
            <button className="button button-secondary button-lg" onClick={() => setShowForm(true)} disabled={busy !== null}>
              <Plus size={18} /> {t('newLease')}
            </button>
          </div>
          <p className="hero-note"><ShieldCheck size={15} /> {t('nothingSent')}</p>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="paper paper-back"><span className="paper-line" /><span className="paper-line short" /><span className="paper-line" /></div>
          <div className="paper paper-front">
            <div className="paper-head" />
            <span className="paper-line" /><span className="paper-line short" /><span className="paper-line" />
            <div className="paper-result"><span>₹ 2,000</span><small>{t('difference')}</small></div>
          </div>
        </div>
      </section>

      <ImpactStrip impact={impact} lang={lang} />

      <section className="how-section" aria-labelledby="how-title">
        <h2 id="how-title">{t('howTitle')}</h2>
        <div className="how-grid">
          {(['step1', 'step2', 'step3', 'step4'] as const).map((key, index) => (
            <article className="how-card" key={key}>
              <span className="how-number">{index + 1}</span>
              <p>{t(key)}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="scenarios-section" aria-labelledby="scenarios-title">
        <div className="section-heading">
          <div>
            <h2 id="scenarios-title">{t('demoScenarios')}</h2>
            <p className="muted small">{t('demoScenariosSubtitle')}</p>
          </div>
          <span className="count-chip">{scenarios.length}</span>
        </div>
        <div className="scenario-grid">
          {scenarios.map((scenario) => (
            <article className="scenario-card" key={scenario.id}>
              <div className="scenario-card-top">
                <h3>{scenario.label}</h3>
                <span className="scenario-docs">{scenario.documents.length} {t('documents')}</span>
              </div>
              <p className="scenario-description">{scenario.description}</p>
              <p className="scenario-expected"><span>{t('scenarioExpected')}:</span> {scenario.expected}</p>
              <button className="button button-secondary button-sm button-full" onClick={() => loadSample(scenario.id)} disabled={busy !== null}>
                {busy === scenario.id ? <Loader2 size={15} className="spin" /> : <Sparkles size={15} />}
                {t('loadThis')}
              </button>
            </article>
          ))}
        </div>
      </section>

      <section className="leases-section" aria-labelledby="leases-title">
        <div className="section-heading">
          <h2 id="leases-title">{t('leasesTitle')}</h2>
          <span className="count-chip">{leases.length}</span>
        </div>
        {leases.length === 0 ? (
          <div className="empty-state">
            <FileStack size={32} />
            <p>{t('noLeases')}</p>
          </div>
        ) : (
          <div className="lease-grid">
            {leases.map((lease) => (
              <button className="lease-card" key={lease.id} onClick={() => onOpenLease(lease.id)}>
                <div className="lease-card-top">
                  <span className="lease-icon"><FileStack size={20} /></span>
                  {lease.awaiting_count > 0 && <span className="mini-badge mini-amber">{lease.awaiting_count} {t('awaitingReview')}</span>}
                </div>
                <h3>{lease.property_label}</h3>
                <p className="muted small">{formatDate(lease.start_date, lang)} — {lease.document_count} {t('documents')} · {lease.invoice_count} {t('invoices')}</p>
                <div className="lease-card-foot">
                  <span>{t('excess')}: <strong>{formatPaise(lease.impact.excess_detected_paise)}</strong></span>
                  <ArrowRight size={18} />
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      {showForm && (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowForm(false)}>
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="new-lease-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-head">
              <h2 id="new-lease-title">{t('newLease')}</h2>
              <button className="icon-button" onClick={() => setShowForm(false)} aria-label={t('close')}><X size={18} /></button>
            </div>
            <p className="muted small">{t('enterDetails')}</p>
            <label className="field">
              <span>{t('propertyLabel')}</span>
              <input value={label} onChange={(event) => setLabel(event.target.value)} placeholder=" Shop 12" maxLength={120} autoFocus />
            </label>
            <label className="field">
              <span>{t('leaseStartDate')}</span>
              <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
            </label>
            <div className="modal-actions">
              <button className="button button-secondary" onClick={() => setShowForm(false)}>{t('cancel')}</button>
              <button className="button button-primary" onClick={createLease} disabled={busy === 'new'}>
                {busy === 'new' ? <Loader2 size={16} className="spin" /> : <Plus size={16} />} {t('create')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
