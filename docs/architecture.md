# Architecture and key decisions

## Layers

| Layer | Files | Rule |
| --- | --- | --- |
| API | `backend/app/api/main.py` | Parse, authorise, call a service, map errors. No business logic. |
| Services | `backend/app/services/` | Extraction + quote gate, deterministic bilingual letters. |
| Domain | `backend/app/domain/` | Pure functions and dataclasses. No I/O, no framework, no model. |
| Infrastructure | `backend/app/infra/` | Provider adapters, file parsing, repository. |
| Schemas | `backend/app/schemas.py` | Strict Pydantic contracts (`extra="forbid"`) for LLM output and request bodies. |

## Request flow

0. `GET /api/v1/demo/scenarios` lists the synthetic scenario catalogue; `POST /api/v1/demo/load?scenario=…` composes one from the sample library through the real ingest path below.

1. `POST /leases/{id}/documents` checks ownership, kind, size and duplicate SHA-256.
2. `to_pages()` enforces `.pdf`/`.txt`, `%PDF-` magic bytes, page limits and a text layer.
3. `ExtractionService` calls the configured provider (Groq or fixtures), then applies `quote_in_text()` to every term.
4. Terms are stored with document, page, effective date and validation state.
5. `POST /leases/{id}/audits` takes the latest invoice and calls `audit_invoice()`, which resolves precedence and does integer-paise arithmetic.
6. Findings carry billed, expected, difference, evidence terms and calculation steps.
7. `PATCH /findings/{id}` records an approval/rejection and an audit-log event.
8. `POST /audits/{id}/letter?lang=en|hi` builds a deterministic letter from approved confirmed findings only and returns a WhatsApp draft URL.

## Decisions

1. **Model reads, code decides** — reproducible, explainable arithmetic; the model never calculates.
2. **Integer paise** — no floating point anywhere in money handling; half-up rounding via integer arithmetic.
3. **Verbatim quote gate** — the cheapest strong control against invented clauses; invalid quotes become uncertainty.
4. **Five explicit precedence outcomes** — Controlling, Missing, Unverified, Conflict, Ambiguous; no silent fallbacks.
5. **Fixtures by content fingerprint** — demo survives renamed files and PDF/TXT substitution; no API key required.
6. **Bilingual from the start** — one translation dictionary, no hard-coded UI strings; letter generated in either language.
7. **Share, don't send** — WhatsApp opens a draft; nothing is auto-sent and the app never claims a recovery.
8. **Single demo user** — documented; all repository reads are user-scoped so JWT auth can be dropped in later.

## Threat / safety notes

- Document text is passed to the model as data inside a fixed instruction frame; output is schema-validated and no tools are exposed.
- Prompt-injection clauses cannot change arithmetic because only quoted, verified values enter the rules engine.
- Uploads are extension- and magic-checked, size- and page-limited, never executed.
- Errors are mapped to a single shape with user-safe messages; logs contain IDs only.
- Status is conveyed by icon, text and colour; focus rings, 44px targets and reduced-motion are supported.
