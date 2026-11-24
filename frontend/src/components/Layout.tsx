import { ChevronLeft, CircleHelp, KeyRound, Languages, ShieldCheck } from 'lucide-react';
import type { ReactNode } from 'react';
import type { Config, Lang } from '../api/types';
import { translate, type TranslationKey } from '../i18n';

interface HeaderProps {
  lang: Lang;
  setLang: (lang: Lang) => void;
  config: Config | null;
  onHome: () => void;
  onHelp: () => void;
  onSetup: () => void;
  onBack?: () => void;
  backLabel?: string;
}

export function Header({ lang, setLang, config, onHome, onHelp, onSetup, onBack, backLabel }: HeaderProps) {
  const t = (key: TranslationKey) => translate(lang, key);
  return (
    <header className="site-header">
      <div className="header-inner">
        {onBack ? (
          <button className="icon-button back-button" onClick={onBack} aria-label={backLabel ?? t('back')}>
            <ChevronLeft size={20} />
          </button>
        ) : null}
        <button className="brand" onClick={onHome} aria-label={`${t('appName')} — home`}>
          <span className="brand-mark"><ShieldCheck size={22} strokeWidth={2.2} /></span>
          <span className="brand-text">
            <strong>{t('appName')}</strong>
            <small>{t('tagline')}</small>
          </span>
        </button>
        <div className="header-actions">
          <div className="language-switch" role="group" aria-label={t('language')}>
            <Languages size={15} aria-hidden="true" />
            <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')} aria-pressed={lang === 'en'}>EN</button>
            <button className={lang === 'hi' ? 'active' : ''} onClick={() => setLang('hi')} aria-pressed={lang === 'hi'}>हिंदी</button>
          </div>
          <button className="icon-button" onClick={onSetup} aria-label={t('setup')} title={t('setup')}>
            <KeyRound size={19} />
          </button>
          <button className="icon-button" onClick={onHelp} aria-label={t('help')} title={t('help')}>
            <CircleHelp size={20} />
          </button>
        </div>
      </div>
      <div className="mode-strip" aria-live="polite">
        <span className={`mode-dot ${config?.live ? 'live' : ''}`} />
        {!config ? t('loading') : config.live ? t('liveMode') : config.degraded_reason ? t('keyMissing') : t('demoMode')}
      </div>
    </header>
  );
}

export function SyntheticBanner({ lang }: { lang: Lang }) {
  return (
    <div className="synthetic-banner" role="note">
      <span className="synthetic-banner-dot" aria-hidden="true" />
      <strong>{translate(lang, 'syntheticBanner')}</strong>
      <span className="synthetic-banner-detail">{translate(lang, 'syntheticLong')}</span>
    </div>
  );
}

export function Page({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return <main className={`page ${wide ? 'page-wide' : ''}`}>{children}</main>;
}
