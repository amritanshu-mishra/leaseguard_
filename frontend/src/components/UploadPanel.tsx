import { CheckCircle2, FilePlus2, FlaskConical, Loader2, UploadCloud } from 'lucide-react';
import { useRef, useState, type DragEvent } from 'react';
import { api } from '../api/client';
import type { Lang, UploadResult } from '../api/types';
import { translate } from '../i18n';

type Kind = 'lease' | 'amendment' | 'invoice';

interface Props {
  leaseId: string;
  lang: Lang;
  maxMb: number;
  demoMode: boolean;
  onUploaded: (result: UploadResult) => void;
  onError: (message: string) => void;
}

const KINDS: Kind[] = ['lease', 'amendment', 'invoice'];
const LABELS: Record<Kind, Parameters<typeof translate>[1]> = {
  lease: 'leaseDoc',
  amendment: 'amendment',
  invoice: 'invoice',
};

export function UploadPanel({ leaseId, lang, maxMb, demoMode, onUploaded, onError }: Props) {
  const t = (key: Parameters<typeof translate>[1]) => translate(lang, key);
  const [kind, setKind] = useState<Kind>('lease');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [sampleBusy, setSampleBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptFile = (candidate: File | undefined) => {
    if (!candidate) return;
    const name = candidate.name.toLowerCase();
    if (!name.endsWith('.pdf') && !name.endsWith('.txt')) {
      onError(t('unsupported_file'));
      return;
    }
    if (candidate.size > maxMb * 1024 * 1024) {
      onError(t('file_too_large'));
      return;
    }
    setFile(candidate);
    setDone(null);
  };

  const submit = async () => {
    if (!file || busy) return;
    setBusy(true);
    setDone(null);
    try {
      const result = await api.upload(leaseId, kind, kind === 'invoice' ? null : effectiveDate || null, file);
      setDone(`${result.document} · ${result.pages} ${t('pages')}`);
      setFile(null);
      setEffectiveDate('');
      if (inputRef.current) inputRef.current.value = '';
      onUploaded(result);
    } catch (error) {
      onError(error instanceof Error ? error.message : t('request_failed'));
    } finally {
      setBusy(false);
    }
  };

  const useSample = async () => {
    setSampleBusy(true);
    setDone(null);
    try {
      const result = await api.uploadDemoDocument(leaseId, kind, kind === 'invoice' ? null : effectiveDate || null);
      setDone(`${result.document} · ${result.pages} ${t('pages')}`);
      onUploaded(result);
    } catch (error) {
      onError(error instanceof Error ? error.message : t('request_failed'));
    } finally {
      setSampleBusy(false);
    }
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files[0]);
  };

  return (
    <section className="upload-panel" aria-labelledby="upload-heading">
      <h3 id="upload-heading"><FilePlus2 size={18} /> {t('addDocuments')}</h3>
      <div className="kind-pills" role="group" aria-label={t('kind')}>
        {KINDS.map((option) => (
          <button
            key={option}
            className={`pill ${kind === option ? 'pill-active' : ''}`}
            onClick={() => { setKind(option); setDone(null); }}
            aria-pressed={kind === option}
          >
            {t(LABELS[option])}
          </button>
        ))}
      </div>

      <div className="upload-fields">
        {kind !== 'invoice' && (
          <label className="field">
            <span>{t('effectiveDate')}</span>
            <input type="date" value={effectiveDate} onChange={(event) => setEffectiveDate(event.target.value)} />
          </label>
        )}
        <div
          className={`dropzone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
          onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <UploadCloud size={26} aria-hidden="true" />
          <p>{file ? file.name : t('dropHere')}</p>
          <span className="muted small">PDF (text layer) or TXT · {maxMb} MB max</span>
          <button className="button button-secondary button-sm" onClick={() => inputRef.current?.click()} type="button">
            {t('chooseFile')}
          </button>
          <input
            ref={inputRef}
            className="visually-hidden"
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            onChange={(event) => acceptFile(event.target.files?.[0])}
            aria-label={t('chooseFile')}
          />
        </div>
      </div>

      <div className="upload-actions">
        <button className="button button-primary" onClick={submit} disabled={!file || busy || (kind !== 'invoice' && !effectiveDate)}>
          {busy ? <><Loader2 size={16} className="spin" /> {t('uploading')}</> : t('upload')}
        </button>
        {demoMode && (
          <div className="sample-upload">
            <p className="muted small">{t('demoUploadHint')}</p>
            <button className="button button-secondary button-sm button-full" onClick={useSample} disabled={sampleBusy || busy}>
              {sampleBusy ? <Loader2 size={15} className="spin" /> : <FlaskConical size={15} />}
              {t('useSampleDoc')}
            </button>
          </div>
        )}
        {done && <span className="success-text"><CheckCircle2 size={16} /> {t('uploaded')}: {done}</span>}
      </div>
    </section>
  );
}
