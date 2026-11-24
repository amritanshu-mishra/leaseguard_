import { Check, Copy, ExternalLink, KeyRound, X, Zap } from 'lucide-react';
import { useState } from 'react';
import type { Config, Lang } from '../api/types';
import { translate } from '../i18n';

const ENV_TEMPLATE = `EXTRACTION_PROVIDER=groq
LLM_API_KEY=gsk_your_real_key_here
EXTRACTION_MODEL=copy-a-current-id-from-groq
EXTRACTION_JSON_MODE=object`;

export function SetupModal({ config, lang, onClose }: { config: Config | null; lang: Lang; onClose: () => void }) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const [copied, setCopied] = useState(false);
  const live = Boolean(config?.live);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(ENV_TEMPLATE);
    } catch {
      const area = document.createElement('textarea');
      area.value = ENV_TEMPLATE;
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      area.remove();
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal setup-modal" role="dialog" aria-modal="true" aria-labelledby="setup-title" onClick={(event) => event.stopPropagation()}>
        <div className="modal-head">
          <h2 id="setup-title"><KeyRound size={19} /> {t('setupTitle')}</h2>
          <button className="icon-button" onClick={onClose} aria-label={t('close')}><X size={18} /></button>
        </div>
        <span className={`status-badge ${live ? 'mini-green' : 'mini-amber'}`}>
          {live ? <Zap size={14} /> : <KeyRound size={14} />}
          {t(live ? 'setupLive' : 'setupDemo')}
        </span>
        <p className="muted small">{t('setupIntro')}</p>
        <ol className="setup-steps">
          <li><code>{t('setupStep1')}</code></li>
          <li><code>{t('setupStep2')}</code></li>
          <li><code>{t('setupStep3')}</code></li>
        </ol>
        <pre className="env-block">{ENV_TEMPLATE}</pre>
        <div className="setup-actions">
          <button className="button button-primary button-sm" onClick={copy}>
            {copied ? <Check size={15} /> : <Copy size={15} />} {copied ? t('envCopied') : t('copyEnv')}
          </button>
          <a className="button button-secondary button-sm" href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer">
            {t('keysPage')} <ExternalLink size={14} />
          </a>
          <a className="button button-secondary button-sm" href="https://console.groq.com/docs/models" target="_blank" rel="noopener noreferrer">
            {t('modelsPage')} <ExternalLink size={14} />
          </a>
        </div>
        <p className="muted small setup-note">{t('keySafety')}</p>
      </div>
    </div>
  );
}
