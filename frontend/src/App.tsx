import { X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { api } from './api/client';
import type { AuditResponse, Config, DemoScenario, Impact, Lang, LeaseSummary } from './api/types';
import { Header, Page, SyntheticBanner } from './components/Layout';
import { SetupModal } from './components/SetupModal';
import { englishStrings, translate, type TranslationKey } from './i18n';
import { Audit } from './pages/Audit';
import { Dashboard } from './pages/Dashboard';
import { Help } from './pages/Help';
import { LeaseDetail } from './pages/LeaseDetail';
import { Letter } from './pages/Letter';

type View =
  | { name: 'dashboard' }
  | { name: 'lease'; id: string }
  | { name: 'audit'; id: string }
  | { name: 'letter'; id: string }
  | { name: 'help' };

function initialLang(): Lang {
  const saved = localStorage.getItem('leaseguard-lang');
  return saved === 'hi' || saved === 'en' ? saved : 'en';
}

export default function App() {
  const [lang, setLangState] = useState<Lang>(initialLang);
  const [view, setView] = useState<View>({ name: 'dashboard' });
  const [leases, setLeases] = useState<LeaseSummary[]>([]);
  const [impact, setImpact] = useState<Impact | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showSetup, setShowSetup] = useState(false);
  const [lastAudit, setLastAudit] = useState<AuditResponse | null>(null);

  const t = (key: TranslationKey) => translate(lang, key);

  const setLang = (next: Lang) => {
    setLangState(next);
    localStorage.setItem('leaseguard-lang', next);
    document.documentElement.lang = next === 'hi' ? 'hi' : 'en';
  };

  useEffect(() => { document.documentElement.lang = lang === 'hi' ? 'hi' : 'en'; }, [lang]);

  const showError = useCallback((message: string) => {
    const key = (Object.keys(englishStrings) as TranslationKey[]).find(
      (candidate) => englishStrings[candidate] === message,
    );
    setError(key ? t(key) : message);
  }, [lang]); // eslint-disable-line react-hooks/exhaustive-deps

  const refresh = useCallback(async () => {
    try {
      const [leaseList, overall, cfg, catalogue] = await Promise.all([
        api.leases(),
        api.impact(),
        api.config(),
        api.demoScenarios(lang),
      ]);
      setLeases(leaseList);
      setImpact(overall);
      setConfig(cfg);
      setScenarios(catalogue);
    } catch (err) {
      showError(err instanceof Error ? err.message : t('request_failed'));
    }
  }, [showError]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { void refresh(); }, [refresh]);

  const runAudit = async (leaseId: string) => {
    try {
      const audit = await api.audit(leaseId);
      setLastAudit(audit);
      setView({ name: 'audit', id: audit.audit_id });
      await refresh();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      showError(err instanceof Error ? err.message : t('request_failed'));
    }
  };

  const backTarget = (): View => {
    if (view.name === 'letter') return lastAudit ? { name: 'audit', id: lastAudit.audit_id } : { name: 'dashboard' };
    if (view.name === 'audit' && lastAudit) return { name: 'lease', id: lastAudit.lease_id };
    return { name: 'dashboard' };
  };

  const navigate = (next: View) => {
    setView(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="app-shell">
      <Header
        lang={lang}
        setLang={setLang}
        config={config}
        onHome={() => navigate({ name: 'dashboard' })}
        onHelp={() => navigate({ name: 'help' })}
        onSetup={() => setShowSetup(true)}
        onBack={view.name === 'dashboard' || view.name === 'help' ? undefined : () => navigate(backTarget())}
        backLabel={t('back')}
      />
      <SyntheticBanner lang={lang} />

      <Page wide={view.name === 'dashboard' || view.name === 'help'}>
        {view.name === 'dashboard' && (
          <Dashboard
            lang={lang}
            config={config}
            scenarios={scenarios}
            leases={leases}
            impact={impact}
            onOpenLease={(id) => navigate({ name: 'lease', id })}
            onLoaded={(id) => navigate({ name: 'lease', id })}
            onNewLease={(id) => navigate({ name: 'lease', id })}
            onRefresh={refresh}
            onError={showError}
          />
        )}
        {view.name === 'lease' && (
          <LeaseDetail
            leaseId={view.id}
            lang={lang}
            config={config}
            onRunAudit={(id) => { void runAudit(id); }}
            onDeleted={() => { void refresh().then(() => navigate({ name: 'dashboard' })); }}
            onError={showError}
          />
        )}
        {view.name === 'audit' && (
          <Audit
            auditId={view.id}
            lang={lang}
            onLetter={(id) => navigate({ name: 'letter', id })}
            onBack={() => navigate(backTarget())}
            onError={showError}
          />
        )}
        {view.name === 'letter' && (
          <Letter
            auditId={view.id}
            lang={lang}
            onBack={() => navigate(backTarget())}
            onError={showError}
          />
        )}
        {view.name === 'help' && <Help lang={lang} onBack={() => navigate({ name: 'dashboard' })} />}
      </Page>

      <footer className="site-footer">
        <span>{t('appName')} · {t('tagline')}</span>
        <span>Techbeez · Amritanshu Mishra · Kaushiki Upadhaya</span>
        <span>{t('impactDisclaimer')}</span>
      </footer>

      {showSetup && <SetupModal config={config} lang={lang} onClose={() => setShowSetup(false)} />}

      {error && (
        <div className="error-toast" role="alert">
          <span><strong>{t('errorTitle')}:</strong> {error}</span>
          <button onClick={() => setError(null)} aria-label={t('close')}><X size={18} /></button>
        </div>
      )}
    </div>
  );
}
