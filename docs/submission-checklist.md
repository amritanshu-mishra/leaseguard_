# Submission checklist — LeaseGuard

**Team:** Techbeez · **Members:** Amritanshu Mishra, Kaushiki Upadhaya

| Item | Status | Evidence |
| --- | --- | --- |
| Working application, same-origin API | Ready | `npm run dev` + `uvicorn …`; `/health` 200; UI calls `/api/v1` |
| End-to-end flow (lease → amendment → invoice → audit → approval → letter → WhatsApp draft) | Ready | `python -m scripts.smoke_pipeline` prints `PIPELINE OK` |
| Groq instead of Anthropic | Ready | `app/infra/llm_groq.py`, `.env.example`, `python -m scripts.smoke_groq` with a real key |
| Hindi key screens + letter | Ready | Header EN/हिंदी toggle; translated buttons, findings, errors and letter |
| Evidence for every discrepancy | Ready | Quote, document, page, effective date, value and calculation steps in every finding |
| Impact metrics without recovery claims | Ready | Excess detected, awaiting review, estimated time saved; explicit disclaimer |
| Synthetic data only, labelled | Ready | `docs/synthetic-data.md`, banner on every screen, stamped sample files |
| Tests and CI | Ready | 44 backend tests, 10 frontend tests, ruff, typecheck, production build, pipeline smoke in CI |
| Dynamic synthetic scenarios | Ready | `GET /demo/scenarios`, `POST /demo/load?scenario=…`; six cases verified in `smoke_pipeline.py` |
| WhatsApp share is robust | Ready | Direct `wa.me` link + More share options (copy link, native share, alternate link) |
| Groq setup is discoverable | Ready | Key icon in app header opens bilingual setup guide; README §0–2 |
| API documentation | Ready | FastAPI `/docs` and `/openapi.json` |
| README with run steps, architecture, test results, synthetic-data statement | Ready | `README.md`, `docs/architecture.md` |
| Demo video (2 min) | Script ready | `docs/demo-video-script.md` — final voiceover names Techbeez, Amritanshu Mishra, Kaushiki Upadhaya |
| Live preview on Arena | Ready | Open the **Live Preview** panel for port **5173** → **Open in new tab**; bare `e2b.app` URL is token-gated and shows “traffic token missing” |
| Team identity | Ready | Techbeez — Amritanshu Mishra, Kaushiki Upadhaya in README, checklist and video script |

## Before you present

1. Start both processes; warm `/health`.
2. Open the app; confirm the amber synthetic banner and **Demo mode / Live Groq** strip.
3. Press **Load sample case**, then **Run invoice audit**. Expect ₹2,000 + ₹1,200 = ₹3,200 excess. Optionally load a second scenario (for example *Conflicting amendments*) to show uncertainty.
4. Show one evidence block: quote, Amendment 1, page 1, effective 1 Jan 2026, calculation.
5. Show impact strip and say "review only — no money recovered".
6. Approve both → Generate letter → Share on WhatsApp (draft only). Toggle हिंदी once.
7. Keep `EXTRACTION_PROVIDER=fixtures` as the fallback if a live Groq call is rate-limited.
