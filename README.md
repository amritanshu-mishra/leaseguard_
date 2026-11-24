# LeaseGuard — evidence-first lease charge audit

A working, bilingual (English/हिंदी) lease-charge checker for small tenants. Upload a lease, its amendment and an invoice. LeaseGuard extracts terms with **verbatim quotes**, resolves which amendment controls, recomputes rent and maintenance **deterministically in integer paise**, and shows the clause, page, effective date and calculation behind every flagged difference. It never guesses, never claims a recovery, and never sends anything to a landlord: a tenant approves findings before a letter is prepared, and the letter can be shared as a WhatsApp draft.

> All bundled documents are **synthetic demo data** derived from the attached technical specification. No real tenant documents or personal data are used. See [`docs/synthetic-data.md`](docs/synthetic-data.md).

---

## 0. Where to open this project

| Thing | Path / URL |
| --- | --- |
| Repository root | `/home/user/leaseguard_` |
| Backend code | `backend/` (FastAPI on `http://localhost:8000`, docs at `/docs`) |
| Frontend code | `frontend/` (Vite on `http://localhost:5173`) |
| Groq API key file | `backend/.env` — **not** the repo root, **not** the frontend |
| In-app setup guide | Click the **key icon** in the app header |

Both servers are already started in this workspace. If you restart them, follow §1.

**Recording the demo?** Use [`docs/demo-video-script.md`](docs/demo-video-script.md) — it has a ready 2-minute voiceover, click-by-click actions, screen-recorder options, and a browser preview URL that needs no laptop installation.

## 1. Quick start (no API key needed)

Requires Python 3.11+ and Node 18+.

```bash
# Terminal 1 — API (http://localhost:8000, docs at /docs)
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload

# Terminal 2 — UI (http://localhost:5173)
cd frontend
npm install
npm run dev
```

The frontend uses the same-origin base path `/api/v1` by default (see `frontend/.env.example`). For a separate backend host, set `VITE_API_URL=https://host/api/v1` before building.

Open the app and press **Load sample case / सैंपल केस लोड करें**. It creates a lease, attaches the synthetic lease, amendment and invoice through the same upload path a real file uses, and opens the lease. Then press **Run invoice audit / बिल की जाँच करें** → review evidence → approve → **Generate letter** → **Share on WhatsApp**.

The dashboard also offers **Try a demo scenario / डेमो परिदृश्य आज़माएँ**: six labelled cases are assembled dynamically from the bundled sample library and pushed through the *same* upload, quote-gate and audit pipeline. Each card shows its expected outcome before you load it:

| Scenario | What it demonstrates |
| --- | --- |
| `amendment` | 5% amendment overrides 10% lease → two confirmed discrepancies (₹3,200) |
| `ambiguous` | "reasonable increase" → uncertain, no amount invented |
| `conflict` | two amendments on the same date → both quotes shown, no amount calculated |
| `future` | amendment effective in July is ignored for an April invoice → no finding |
| `missing-cap` | no maintenance cap in the documents → uncertain, not assumed |
| `clean` | matching invoice → no findings |

`POST /api/v1/leases/{id}/demo/documents?kind=lease|amendment|invoice` attaches a bundled sample to a lease you created yourself, so the upload flow always works in demo mode.

The catalogue is served by `GET /api/v1/demo/scenarios?lang=en|hi`; `POST /api/v1/demo/load?scenario=<id>&lang=<lang>` composes the case. Unknown IDs fall back safely to `amendment`.

The default provider is `fixtures`: the three bundled synthetic documents are matched by **content fingerprint**, so renaming them or uploading the PDF version still works. No API key is required for the demo.

---

## 2. Where to put the Groq API key

**Put the key in `backend/.env`.** This file is git-ignored; never commit the key. You can also click the **key icon** in the app header for the same instructions and a copyable template.

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

```dotenv
EXTRACTION_PROVIDER=groq
LLM_API_KEY=gsk_your_real_key_here
EXTRACTION_MODEL=<copy a CURRENT model id from https://console.groq.com/docs/models>
EXTRACTION_JSON_MODE=object
ALLOWED_ORIGINS=http://localhost:5173
MAX_UPLOAD_MB=10
MAX_PAGES=50
```

Restart the API after changing `.env`. Verify it in the UI: the header strip switches from **Demo mode · bundled samples** to **Live extraction · Groq**. The `/api/v1/config` endpoint shows `live: true` and never exposes the key.

Then run the one-call smoke test:

```bash
cd backend
python -m scripts.smoke_groq
```

Expected: three terms with `quote verified`. If it fails, the usual causes are a stale model id, a key with no credit, or a model that does not support `json_schema` (leave `EXTRACTION_JSON_MODE=object`). In fixtures mode the same endpoint is instant and free.

**Key facts about the Groq change**

- Only extraction uses the model. Precedence, arithmetic, quote validation and decisions stay in deterministic Python.
- The adapter calls Groq's OpenAI-compatible endpoint (`https://api.groq.com/openai/v1`) with temperature 0, page markers, structured JSON and one retry that feeds validation errors back.
- `EXTRACTION_MODEL` is never hard-coded: Groq retires models frequently, so copy a current id from the console.
- `EXTRACTION_JSON_MODE=object` works broadly; use `schema` only for models that advertise `json_schema` support.
- With a key configured, any text-layer PDF or TXT can be read. In fixtures mode only the bundled synthetic samples are recognised — the UI says so honestly.
- Photos/scans have no OCR in this build. Use a text PDF or TXT.

---

## 3. What was built for the hackathon brief

| Requirement | Implementation |
| --- | --- |
| Groq instead of Anthropic | `app/infra/llm_groq.py`, env-driven model, `.env.example`, smoke test, fixtures fallback |
| WhatsApp share for the letter | Deterministic letter plus `share_text` and a `https://wa.me/?text=…` draft link; the button is a real link (more reliable than a popup), with a **More share options** dialog offering copy link, native device share and an alternate `api.whatsapp.com` link for preview environments |
| Hindi for key screens | Full EN/हिंदी dictionary, header toggle, translated dashboard, lease, audit, decisions, error messages and letter; persisted in `localStorage` |
| Stronger evidence UI | Every finding shows the clause quote, document, page, effective date, term value/unit, a verified badge and the step-by-step calculation |
| Impact metric | Excess detected, amount awaiting review, estimated minutes saved; each is labelled as review-only, with an explicit "no money recovered" disclaimer and a transparent estimate basis |
| Synthetic demo data | Ten text files matching the spec's golden cases, PDF twins generated from the same text, content-hash fixture matching, six dynamically composed scenarios |
| Working upload | Extension + magic-byte checks, size/page limits, duplicate detection, PDF text layer or TXT, renamed-file and PDF fallback matching, clear errors, drag-and-drop + mobile file picker, plus a **Use a bundled sample** button in demo mode |
| Correct tenancy dates | New-lease dialog asks for the start date; uploading the base lease corrects a placeholder date; editable start date on the lease screen |
| Refined UX | Five responsive screens, calm design system, status by icon + text + colour, 44px touch targets, mobile sticky action bar, focus rings, reduced-motion support |

### Impact definitions (important)

- **Excess detected** = sum of `billed − expected` for all confirmed findings.
- **Awaiting your review** = confirmed excess whose finding has not been approved or rejected.
- **Time saved** = illustrative estimate (3 min per document read + 5 min per audit reviewed), shown with its basis. It is **not** a measured result.
- Nothing in the product claims money recovered, sent, or legally owed.

---

## 4. Architecture

```
browser (React + Vite, EN/HI)
   │  same-origin /api (Vite proxy in dev)
   ▼
FastAPI  ── services ── domain (pure: money, precedence, checks, quotes)
   │                     ▲
   ├── infra/repo.py     └── infra/text_extraction.py
   ├── infra/llm_groq.py  ← Groq API (LLM_API_KEY)
   └── infra/llm_fixture.py ← content-hash matched synthetic fixtures
```

- **The model reads; code decides.** The LLM only emits validated structured terms with quotes. All amounts and precedence are computed in Python; `Money` uses integer paise and half-up rounding.
- **Quote gate.** A term is a fact only if its quote appears verbatim (whitespace-normalised, case-insensitive) in the same document. Failures become "needs your input", never numbers.
- **Precedence.** Latest validated effective date wins; ties with different values conflict; missing, ambiguous and unverified terms are explicit outcomes.
- **Approval gate.** The letter includes only confirmed findings the tenant approved. Re-running a letter with no approval returns HTTP 409.
- **Per-user scoping.** Every read is filtered by `user_id`; a foreign lease returns the same 404 as a missing one. Single documented demo user for the hackathon.

Detailed design: [`docs/architecture.md`](docs/architecture.md), submission status: [`docs/submission-checklist.md`](docs/submission-checklist.md). API docs are generated at `http://localhost:8000/docs`.

---

## 5. Verification

```bash
cd backend
ruff check .
python -m pytest -q          # 44 tests: domain, G1–G6/U1–U2, API, uploads, Groq adapter, impact, six demo scenarios
python -m scripts.smoke_pipeline   # against a running API — full pipeline, no key needed

cd ../frontend
npm run typecheck
npm test                     # 10 tests: formatting, i18n, API base path, audit/letter/dashboard/setup rendering, decisions, scenario picker
npm run build
```

The Groq adapter is tested with a fake OpenAI-compatible client; the live call is verified with `python -m scripts.smoke_groq` once a key is configured. `smoke_pipeline.py` can be pointed at the running UI proxy with `LEASEGUARD_API=http://localhost:5173`. Component tests render the audit screen with a full API payload, so a missing field or a blank translation cannot silently ship. CI runs lint, tests, typecheck and build on every push: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

### If PowerShell says “'vite' is not recognized”

Node dependencies were not installed in `frontend/` yet. `npm run dev` only works after `npm install` (or `npm ci`) has created `frontend\node_modules\.bin\vite`. From the repo root on Windows:

```powershell
cd $HOME\leaseguard_
powershell -ExecutionPolicy Bypass -File setup_laptop.ps1
```

Or, to fix just the UI folder:

```powershell
cd $HOME\leaseguard_\frontend
npm install
npm run dev
```

If `npm` itself is not recognized, install Node.js 18+ LTS from <https://nodejs.org> and **open a new PowerShell window** before retrying. Keep one terminal for the API (`backend/`) and a second for the UI (`frontend/`).

### If WhatsApp does not open

The **Share on WhatsApp** button is a normal link to `wa.me`. Preview iframes and popup blockers can still swallow external navigation. Use **More share options → Copy link** and paste it into WhatsApp, or **Share via device** on a phone. Nothing is sent automatically.

### If a lease upload says “could not be read reliably”

Fixture (demo) mode only recognises the bundled synthetic documents, by content hash. Either press **Use a bundled sample** in the upload panel, load a scenario from the dashboard, or add a Groq key in `backend/.env` and restart the API to read your own text-layer PDF/TXT files.

### If the UI shows no data

The browser must call `/api/v1/...`, not `/api/...`. This is the default in `src/api/client.ts` and `frontend/.env.example`. Restart `npm run dev` after changing `VITE_API_URL`. Check `curl http://localhost:8000/health` and `curl http://localhost:5173/api/v1/config`.

### 60-second demo script

1. **0–10 s** — Dashboard: "Synthetic data. A shopkeeper has a lease, an amendment and this month's invoice." Press **Load sample case**. Point at the six scenario cards to show the range of cases.
2. **10–25 s** — Lease detail: show the amendment marked *In force* and the older escalation *Superseded*, with the exact clause quote.
3. **25–40 s** — Audit: "Billed ₹44,000, expected ₹42,000. Here is the quote, page, effective date and calculation — ₹2,000 excess."
4. **40–50 s** — Impact strip: ₹3,200 excess detected, ₹3,200 awaiting review, estimated time saved. "No money is recovered."
5. **50–60 s** — Approve both → Generate letter → **Share on WhatsApp**. "A draft opens; nothing is sent automatically." Toggle **हिंदी** at any point.

---

## 6. Honest limits

- In-memory repository: data resets when the API restarts. The repository interface is isolated so Postgres can replace it without touching the domain.
- One demo user; Supabase JWT auth is a documented next step.
- One invoice per lease is audited (the latest uploaded); annual percentage escalation and a flat maintenance cap are the two implemented checks.
- Text-layer PDFs and TXT only; scanned documents need OCR.
- Groq free-tier limits and model ids change; fixtures mode is always available for a reliable live demo.

These limits are intentional scope decisions from the technical specification's cut list. Quote validation, deterministic arithmetic and the approval gate were never cut.
