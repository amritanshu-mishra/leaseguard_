import { AlertCircle, CheckCircle2, CircleAlert, ShieldCheck } from 'lucide-react';
import type { Lang } from '../api/types';
import { translate } from '../i18n';

export function StatusBadge({ status, lang }: { status: 'confirmed' | 'uncertain'; lang: Lang }) {
  const confirmed = status === 'confirmed';
  return (
    <span className={`status-badge ${confirmed ? 'badge-red' : 'badge-amber'}`}>
      {confirmed ? <CircleAlert size={15} /> : <AlertCircle size={15} />}
      {translate(lang, confirmed ? 'confirmed' : 'uncertain')}
    </span>
  );
}

export function VerifiedBadge({ validated, lang }: { validated: boolean; lang: Lang }) {
  return (
    <span className={`mini-badge ${validated ? 'mini-teal' : 'mini-amber'}`}>
      {validated ? <ShieldCheck size={13} /> : <AlertCircle size={13} />}
      {translate(lang, validated ? 'verified' : 'unverified')}
    </span>
  );
}

export function DecisionBadge({ decision, lang }: { decision: 'approved' | 'rejected' | null; lang: Lang }) {
  if (!decision) return null;
  return (
    <span className={`mini-badge ${decision === 'approved' ? 'mini-green' : 'mini-neutral'}`}>
      {decision === 'approved' ? <CheckCircle2 size={13} /> : <CircleAlert size={13} />}
      {translate(lang, decision)}
    </span>
  );
}
