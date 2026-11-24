import { ArrowLeft, Check, ClipboardCopy, ExternalLink, Languages, Link2, MessageCircle, Share2, ShieldCheck, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { formatPaise } from '../api/format';
import type { Finding, Lang, LetterResponse } from '../api/types';
import { translate } from '../i18n';

interface Props {
  auditId: string;
  lang: Lang;
  onBack: () => void;
  onError: (message: string) => void;
}

export function Letter({ auditId, lang, onBack, onError }: Props) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const [letterLang, setLetterLang] = useState<Lang>(lang);
  const [letter, setLetter] = useState<LetterResponse | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [copied, setCopied] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  useEffect(() => {
    let active = true;
    // Always re-read decisions from the server; local navigation state can be stale.
    api.getAudit(auditId)
      .then((result) => { if (active) setFindings(result.findings); })
      .catch((error: unknown) => onError(error instanceof Error ? error.message : t('request_failed')));
    api.letter(auditId, letterLang)
      .then((result) => { if (active) setLetter(result); })
      .catch((error: unknown) => onError(error instanceof Error ? error.message : t('request_failed')));
    return () => { active = false; };
  }, [auditId, letterLang]); // eslint-disable-line react-hooks/exhaustive-deps

  const copy = async () => {
    if (!letter) return;
    try {
      await navigator.clipboard.writeText(letter.letter);
    } catch {
      const area = document.createElement('textarea');
      area.value = letter.letter;
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      area.remove();
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2500);
  };

  const copyLink = async () => {
    if (!letter) return;
    try {
      await navigator.clipboard.writeText(letter.whatsapp_url);
    } catch {
      const area = document.createElement('textarea');
      area.value = letter.whatsapp_url;
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      area.remove();
    }
    setLinkCopied(true);
    window.setTimeout(() => setLinkCopied(false), 2500);
  };

  const nativeShare = async () => {
    if (!letter || !navigator.share) return;
    try {
      await navigator.share({ title: t('appName'), text: letter.share_text });
    } catch {
      /* the user dismissed the native sheet */
    }
  };

  const alternateUrl = letter
    ? letter.whatsapp_url.replace('https://wa.me/?text=', 'https://api.whatsapp.com/send?text=')
    : '';

  const included = findings.filter((f) => f.decision === 'approved' && f.status === 'confirmed');

  return (
    <>
      <div className="page-title-row">
        <div>
          <span className="eyebrow">{t('letterTitle')}</span>
          <h1>{t('letterTitle')}</h1>
          <p className="muted">{t('letterSubtitle')}</p>
        </div>
        <div className="language-switch letter-language" role="group" aria-label={t('letterLanguage')}>
          <Languages size={15} aria-hidden="true" />
          <button className={letterLang === 'en' ? 'active' : ''} onClick={() => setLetterLang('en')}>English</button>
          <button className={letterLang === 'hi' ? 'active' : ''} onClick={() => setLetterLang('hi')}>हिंदी</button>
        </div>
      </div>

      <div className="letter-layout">
        <section className="panel letter-preview" aria-label={t('letterTitle')}>
          <div className="letter-paper">
            {letter ? <pre>{letter.letter}</pre> : <div className="loading-card"><span className="skeleton" /></div>}
          </div>
          <p className="letter-disclaimer"><ShieldCheck size={16} /> {t('letterDisclaimer')}</p>
        </section>

        <aside className="letter-side">
          <div className="side-card">
            <h3>{t('included')} ({included.length})</h3>
            <ul className="included-list">
              {included.map((finding) => (
                <li key={finding.id}>
                  <span><Check size={14} /> {t(`check_${finding.check}` as Parameters<typeof translate>[1])}</span>
                  <strong>{formatPaise(finding.difference_paise)}</strong>
                </li>
              ))}
            </ul>
          </div>
          <div className="side-card action-card">
            {letter ? (
              <a className="button button-whatsapp button-full" href={letter.whatsapp_url} target="_blank" rel="noopener noreferrer">
                <MessageCircle size={18} /> {t('shareWhatsApp')} <ExternalLink size={15} />
              </a>
            ) : (
              <button className="button button-whatsapp button-full" disabled><MessageCircle size={18} /> {t('shareWhatsApp')}</button>
            )}
            <button className="button button-secondary button-full" onClick={() => setShowShare(true)} disabled={!letter}>
              <Share2 size={17} /> {t('shareOptions')}
            </button>
            <button className="button button-secondary button-full" onClick={copy} disabled={!letter}>
              {copied ? <Check size={18} /> : <ClipboardCopy size={18} />} {copied ? t('copied') : t('copy')}
            </button>
            <p className="muted small">{t('shareNote')}</p>
          </div>
          <button className="text-back" onClick={onBack}><ArrowLeft size={15} /> {t('backToFindings')}</button>
        </aside>
      </div>
      {showShare && letter && (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowShare(false)}>
          <div className="modal share-modal" role="dialog" aria-modal="true" aria-labelledby="share-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-head">
              <h2 id="share-title"><MessageCircle size={19} /> {t('shareModalTitle')}</h2>
              <button className="icon-button" onClick={() => setShowShare(false)} aria-label={t('close')}><X size={18} /></button>
            </div>
            <p className="muted small">{t('shareModalNote')}</p>
            <a className="button button-whatsapp button-full" href={letter.whatsapp_url} target="_blank" rel="noopener noreferrer">
              <MessageCircle size={18} /> {t('openWhatsApp')} <ExternalLink size={15} />
            </a>
            <button className="button button-secondary button-full" onClick={copyLink}>
              {linkCopied ? <Check size={17} /> : <Link2 size={17} />} {linkCopied ? t('linkCopied') : t('copyLink')}
            </button>
            {typeof navigator !== 'undefined' && 'share' in navigator && (
              <button className="button button-secondary button-full" onClick={nativeShare}>
                <Share2 size={17} /> {t('nativeShare')}
              </button>
            )}
            <label className="field">
              <span>{t('shareTextLabel')}</span>
              <textarea className="share-text" readOnly value={letter.share_text} rows={5} />
            </label>
            <a className="share-alt-link" href={alternateUrl} target="_blank" rel="noopener noreferrer">
              {t('alternateLink')} <ExternalLink size={13} />
            </a>
          </div>
        </div>
      )}
    </>
  );
}
