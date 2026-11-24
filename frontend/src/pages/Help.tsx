import { BookOpen, BrainCircuit, CircleAlert, Gauge, LockKeyhole, TerminalSquare } from 'lucide-react';
import type { Lang } from '../api/types';
import { translate } from '../i18n';

export function Help({ lang, onBack }: { lang: Lang; onBack: () => void }) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const sections = [
    { icon: <BrainCircuit size={20} />, title: t('helpMethod'), body: t('helpMethodBody') },
    { icon: <BookOpen size={20} />, title: t('helpEvidence'), body: t('helpEvidenceBody') },
    { icon: <CircleAlert size={20} />, title: t('helpUncertainty'), body: t('helpUncertaintyBody') },
    { icon: <Gauge size={20} />, title: t('helpImpact'), body: t('helpImpactBody') },
    { icon: <LockKeyhole size={20} />, title: t('helpPrivacy'), body: t('helpPrivacyBody') },
    { icon: <BookOpen size={20} />, title: t('helpScenarios'), body: t('helpScenariosBody') },
    { icon: <TerminalSquare size={20} />, title: t('helpSetup'), body: t('helpSetupBody') },
  ];
  return (
    <div className="help-page">
      <h1>{t('helpTitle')}</h1>
      <div className="help-grid">
        {sections.map((section) => (
          <article className="help-card" key={section.title}>
            <span className="help-icon">{section.icon}</span>
            <div>
              <h2>{section.title}</h2>
              <p>{section.body}</p>
            </div>
          </article>
        ))}
      </div>
      <button className="text-back" onClick={onBack}>← {t('back')}</button>
    </div>
  );
}
