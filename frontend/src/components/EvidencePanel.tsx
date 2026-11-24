import { ChevronDown, FileText, MapPin, Quote, Sigma } from 'lucide-react';
import { useState } from 'react';
import type { Evidence, Lang } from '../api/types';
import { formatDate, formatPaise } from '../api/format';
import { translate } from '../i18n';
import { VerifiedBadge } from './StatusBadge';

interface Props {
  evidence: Evidence[];
  calculation: string[];
  lang: Lang;
  openByDefault?: boolean;
}

export function EvidencePanel({ evidence, calculation, lang, openByDefault = true }: Props) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const [open, setOpen] = useState(openByDefault);

  return (
    <div className="evidence-panel">
      <div className="evidence-heading">
        <FileText size={16} aria-hidden="true" />
        <strong>{t('evidence')}</strong>
        {evidence.length > 0 && <VerifiedBadge validated={evidence.every((e) => e.validated)} lang={lang} />}
      </div>

      {evidence.length === 0 ? (
        <p className="muted small">{t('uncertainNote')}</p>
      ) : (
        <div className="evidence-list">
          {evidence.map((item, index) => (
            <blockquote className="evidence-quote" key={`${item.document}-${index}`}>
              <Quote size={15} aria-hidden="true" />
              <div>
                <p className="quote-text">{item.quote}</p>
                <div className="evidence-meta">
                  <span><FileText size={12} /> {item.document}</span>
                  <span><MapPin size={12} /> {t('page')} {item.page}</span>
                  <span>{formatDate(item.effective_date, lang)}</span>
                  {item.value !== null && (
                    <span>{item.label}: {item.term_type === 'escalation_rate_bp' ? `${item.value} bp` : formatPaise(item.value)}</span>
                  )}
                </div>
              </div>
            </blockquote>
          ))}
        </div>
      )}

      {calculation.length > 0 && (
        <div className="calculation-block">
          <button className="calculation-toggle" onClick={() => setOpen(!open)} aria-expanded={open}>
            <Sigma size={16} /> {t('calculation')}
            <ChevronDown size={16} className={open ? 'chevron open' : 'chevron'} />
          </button>
          {open && (
            <ol className="calculation-steps">
              {calculation.map((step, index) => (
                <li key={index}><span className="step-number">{index + 1}</span><code>{step}</code></li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  );
}
