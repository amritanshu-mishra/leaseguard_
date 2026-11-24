import { AlertTriangle, Clock3, TrendingUp } from 'lucide-react';
import type { Impact, Lang } from '../api/types';
import { formatPaise, shortNumber } from '../api/format';
import { translate } from '../i18n';

export function ImpactStrip({ impact, lang, compact = false }: { impact: Impact | null; lang: Lang; compact?: boolean }) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const cards = [
    { key: 'excess', value: formatPaise(impact?.excess_detected_paise ?? 0), icon: <TrendingUp size={18} />, tone: 'red' },
    { key: 'awaiting', value: formatPaise(impact?.awaiting_review_paise ?? 0), icon: <AlertTriangle size={18} />, tone: 'amber' },
    { key: 'timeSaved', value: shortNumber(impact?.estimated_minutes_saved ?? 0), icon: <Clock3 size={18} />, tone: 'teal' },
  ] as const;

  return (
    <section className={`impact ${compact ? 'impact-compact' : ''}`} aria-labelledby="impact-title">
      <div className="section-heading">
        <div>
          <h2 id="impact-title">{t('impactTitle')}</h2>
          <p className="muted small">{t('impactDisclaimer')}</p>
        </div>
      </div>
      <div className="impact-grid">
        {cards.map((card) => (
          <article className={`impact-card tone-${card.tone}`} key={card.key}>
            <span className="impact-icon" aria-hidden="true">{card.icon}</span>
            <span className="impact-label">{t(card.key)}</span>
            <strong className="impact-value">{card.value}</strong>
          </article>
        ))}
      </div>
      <p className="impact-footnote">
        {impact ? t('estimateBasis') : t('impactEmpty')}
      </p>
    </section>
  );
}
