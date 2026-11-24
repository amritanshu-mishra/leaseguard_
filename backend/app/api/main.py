"""HTTP layer: validate, authorise, call a service, map errors. No business logic."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import SAMPLES_DIR, Settings, load_settings
from app.demo import DEFAULT_SCENARIO, SCENARIOS, get_scenario
from app.domain.checks import audit_invoice
from app.domain.impact import compute_impact
from app.domain.models import (
    TERM_LABELS,
    TERM_UNITS,
    Finding,
    Status,
    TermType,
    display_document_name,
)
from app.infra.llm_base import ExtractionError
from app.infra.llm_fixture import FixtureClient
from app.infra.llm_groq import GroqExtractionClient
from app.infra.repo import ConflictError, InMemoryRepo, NotFound
from app.infra.text_extraction import UnsupportedFile, to_pages
from app.schemas import Decision, LeaseCreate, LeaseUpdate
from app.services.extraction_service import ExtractionService
from app.services.letter_service import build_letter

DEMO_USER = "demo-user"


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int) -> None:
        self.code, self.message, self.status = code, message, status


def current_user() -> str:
    """Single demo user. Replace with JWT verification for real accounts."""
    return DEMO_USER


def build_client(settings: Settings, fixtures_dir: Path = SAMPLES_DIR / "fixtures"):
    """Select the extraction provider; fixtures are key-free and deterministic."""
    if settings.provider == "groq":
        return GroqExtractionClient(settings.api_key, settings.model, settings.json_mode)
    return FixtureClient.from_dir(fixtures_dir, corpus_dir=SAMPLES_DIR)


def finding_dict(row: dict, decision: str | None) -> dict:
    finding: Finding = row["finding"]
    evidence = []
    for term in finding.terms:
        try:
            term_type = TermType(term.term_type)
            label, unit = TERM_LABELS[term_type], TERM_UNITS[term_type]
        except ValueError:
            label, unit = str(term.term_type), ""
        evidence.append(
            {
                "term_type": term.term_type.value,
                "label": label,
                "value": term.value,
                "unit": unit,
                "document": display_document_name(term.document_name),
                "document_file": term.document_name,
                "page": term.page,
                "effective_date": term.effective_date.isoformat(),
                "quote": term.source_quote,
                "validated": term.validated,
                "ambiguous": term.ambiguous,
            }
        )
    return {
        "id": row["id"],
        "check": finding.check,
        "status": finding.status.value,
        "reason": finding.reason.value if finding.reason else None,
        "message": finding.message,
        "billed_paise": finding.billed_paise,
        "expected_paise": finding.expected_paise,
        "difference_paise": finding.difference_paise,
        "decision": decision,
        "evidence": evidence,
        "calculation": list(finding.calculation),
    }


def term_dict(term) -> dict:
    return {
        "id": getattr(term, "id", None),
        "type": term.term_type.value,
        "term_type": term.term_type.value,
        "label": TERM_LABELS.get(term.term_type, term.term_type.value),
        "value": term.value,
        "unit": TERM_UNITS.get(term.term_type, ""),
        "document": display_document_name(term.document_name),
        "document_file": term.document_name,
        "effective_date": term.effective_date.isoformat(),
        "quote": term.source_quote,
        "page": term.page,
        "validated": term.validated,
        "ambiguous": term.ambiguous,
        "confidence": term.confidence,
    }


def with_decisions(repo: InMemoryRepo, rows: list[dict]) -> list[dict]:
    """Attach the current decision to finding rows before impact aggregation."""
    return [{**row, "decision": repo.approvals.get(row["id"])} for row in rows]


def audit_payload(audit: dict, repo: InMemoryRepo, user: str) -> dict:
    """One canonical audit response for both POST (create) and GET (refresh)."""
    lease_id = audit["lease_id"]
    if not repo.invoices[lease_id]:
        raise AppError("no_invoice", "Upload an invoice before running an audit.", 409)
    invoice = repo.invoices[lease_id][-1]
    finding_rows = [repo.findings[fid] for fid in audit["finding_ids"]]
    return {
        "audit_id": audit["id"],
        "lease_id": lease_id,
        "period_start": invoice.period_start.isoformat(),
        "invoice": {
            "period_start": invoice.period_start.isoformat(),
            "rent_paise": invoice.rent_paise,
            "maintenance_paise": invoice.maintenance_paise,
        },
        "findings": [finding_dict(row, repo.approvals.get(row["id"])) for row in finding_rows],
        "impact": compute_impact(
            with_decisions(repo, finding_rows),
            document_count=len(repo.documents[lease_id]),
            audit_count=len(repo.audit_rows(user)),
        ).as_dict(),
    }


def lease_summary(lease: dict, repo: InMemoryRepo, user: str) -> dict:
    lease_id = lease["id"]
    audit_ids = {a["id"] for a in repo.audit_rows(user) if a["lease_id"] == lease_id}
    rows = [repo.findings[fid] for aid in audit_ids for fid in repo.audits[aid]["finding_ids"]]
    impact = compute_impact(
        with_decisions(repo, rows),
        document_count=len(repo.documents[lease_id]),
        audit_count=len(audit_ids),
    ).as_dict()
    return {
        "id": lease_id,
        "property_label": lease["property_label"],
        "scenario_id": lease.get("scenario_id"),
        "start_date": lease["start_date"].isoformat(),
        "created_at": lease["created_at"],
        "document_count": len(repo.documents[lease_id]),
        "invoice_count": len(repo.invoices[lease_id]),
        "finding_count": len(rows),
        "awaiting_count": sum(1 for r in rows if r["finding"].status == Status.CONFIRMED and r.get("decision") is None),
        "impact": impact,
    }


def create_app(settings: Settings | None = None, client=None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="LeaseGuard API", version="2.0", description="Evidence-first lease charge audit")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_origin_regex=r"https://.*\.e2b\.app",
        allow_methods=["*"],
        allow_headers=["*"],
    )
    repo = InMemoryRepo()
    degraded_reason = ""
    if client is not None:
        extraction = ExtractionService(client)
    else:
        try:
            extraction = ExtractionService(build_client(settings))
        except (ValueError, ExtractionError) as exc:
            degraded_reason = str(exc)
            extraction = ExtractionService(FixtureClient.from_dir(SAMPLES_DIR / "fixtures", corpus_dir=SAMPLES_DIR))

    def add_error_handlers() -> None:
        @app.exception_handler(AppError)
        async def _app_error(_, exc: AppError) -> JSONResponse:
            return JSONResponse(
                status_code=exc.status,
                content={"error": {"code": exc.code, "message": exc.message}},
            )

        @app.exception_handler(NotFound)
        async def _not_found(_, exc: NotFound) -> JSONResponse:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "not_found", "message": f"That {exc} was not found."}},
            )

        @app.exception_handler(ConflictError)
        async def _conflict(_, exc: ConflictError) -> JSONResponse:
            return JSONResponse(
                status_code=409,
                content={"error": {"code": "duplicate_document", "message": str(exc)}},
            )

        @app.exception_handler(RequestValidationError)
        async def _validation(_, exc: RequestValidationError) -> JSONResponse:
            return JSONResponse(
                status_code=422,
                content={"error": {"code": "validation_error", "message": "Check the submitted fields and try again."}},
            )

    add_error_handlers()

    async def ingest(
        lease_id: str,
        kind: str,
        effective_date: date | None,
        filename: str,
        data: bytes,
        user: str,
    ) -> dict:
        lease = repo.get_lease(user, lease_id)
        if kind not in ("lease", "amendment", "invoice"):
            raise AppError("bad_kind", "Kind must be lease, amendment or invoice.", 400)
        if kind != "invoice" and effective_date is None:
            raise AppError("missing_effective_date", "An effective date is required for leases and amendments.", 400)
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise AppError("file_too_large", f"File is larger than {settings.max_upload_mb} MB.", 413)
        try:
            pages = to_pages(filename, data, settings.max_pages)
        except UnsupportedFile as exc:
            raise AppError("unsupported_file", str(exc), 400) from exc
        name = Path(filename).stem
        sha = hashlib.sha256(data).hexdigest()
        if any(doc["sha256"] == sha for doc in repo.documents[lease_id]):
            raise AppError("duplicate_document", "This exact file is already attached to this lease.", 409)
        # A base lease document's effective date IS the tenancy start. Correct a
        # placeholder start date so anniversaries are computed from real evidence.
        if kind == "lease" and effective_date and effective_date < lease["start_date"]:
            repo.update_lease(user, lease_id, start_date=effective_date)
        try:
            if kind == "invoice":
                invoice = extraction.invoice_from_document(name, pages, kind)
                repo.add_invoice(lease_id, invoice)
                result = {
                    "document": name,
                    "kind": kind,
                    "sha256": sha,
                    "pages": len(pages),
                    "invoice": {
                        "period_start": invoice.period_start.isoformat(),
                        "rent_paise": invoice.rent_paise,
                        "maintenance_paise": invoice.maintenance_paise,
                    },
                }
            else:
                terms = extraction.terms_from_document(name, effective_date, pages, kind)
                repo.add_terms(lease_id, terms)
                result = {
                    "document": name,
                    "kind": kind,
                    "sha256": sha,
                    "pages": len(pages),
                    "terms_found": len(terms),
                    "terms_unverified": sum(1 for term in terms if not term.validated),
                }
        except ExtractionError as exc:
            code = "provider_error" if exc.code == "provider_error" else "extraction_failed"
            message = (
                "The AI provider could not read this document. Check the API key, model and rate limit, then retry."
                if code == "provider_error"
                else "This document could not be read reliably. Try the TXT version or upload a bundled synthetic sample."
            )
            raise AppError(code, message, 502) from exc
        repo.add_document(
            lease_id,
            {
                "id": sha[:12],
                "name": name,
                "kind": kind,
                "sha256": sha,
                "pages": len(pages),
                "effective_date": effective_date.isoformat() if effective_date else None,
            },
        )
        return result

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "provider": settings.provider}

    @app.get("/api/v1/config")
    def config() -> dict:
        return {
            "provider": settings.provider,
            "live": settings.is_live,
            "model": settings.model if settings.is_live else None,
            "json_mode": settings.json_mode,
            "api_key_configured": bool(settings.api_key),
            "max_upload_mb": settings.max_upload_mb,
            "degraded_reason": degraded_reason,
            "demo_user": DEMO_USER,
        }

    @app.post("/api/v1/leases", status_code=201)
    def create_lease(body: LeaseCreate, user: str = Depends(current_user)) -> dict:
        lease = repo.create_lease(user, body.property_label, body.start_date)
        return lease_summary(lease, repo, user)

    @app.patch("/api/v1/leases/{lease_id}")
    def update_lease(lease_id: str, body: LeaseUpdate, user: str = Depends(current_user)) -> dict:
        changes = body.model_dump(exclude_none=True)
        lease = repo.update_lease(user, lease_id, **changes)
        return lease_summary(lease, repo, user)

    @app.get("/api/v1/leases")
    def list_leases(user: str = Depends(current_user)) -> list[dict]:
        return [lease_summary(lease, repo, user) for lease in repo.list_leases(user)]

    @app.get("/api/v1/leases/{lease_id}")
    def get_lease(lease_id: str, user: str = Depends(current_user)) -> dict:
        lease = repo.get_lease(user, lease_id)
        return {
            **lease_summary(lease, repo, user),
            "documents": repo.documents[lease_id],
            "terms": [term_dict(t) for t in repo.terms[lease_id]],
            "invoices": [
                {
                    "period_start": inv.period_start.isoformat(),
                    "rent_paise": inv.rent_paise,
                    "maintenance_paise": inv.maintenance_paise,
                }
                for inv in repo.invoices[lease_id]
            ],
        }

    @app.delete("/api/v1/leases/{lease_id}", status_code=204)
    def delete_lease(lease_id: str, user: str = Depends(current_user)) -> None:
        repo.delete_lease(user, lease_id)

    @app.post("/api/v1/leases/{lease_id}/documents", status_code=201)
    async def upload_document(
        lease_id: str,
        kind: str = Form(...),
        effective_date: date | None = Form(None),
        file: UploadFile = File(...),
        user: str = Depends(current_user),
    ) -> dict:
        return await ingest(lease_id, kind, effective_date, file.filename or "document", await file.read(), user)

    @app.get("/api/v1/demo/scenarios")
    def demo_scenarios(lang: str = Query("en", pattern="^(en|hi)$")) -> list[dict]:
        """List selectable synthetic scenarios with bilingual descriptions."""
        return [
            {
                **scenario.as_dict(),
                "label": scenario.label_hi if lang == "hi" else scenario.label_en,
                "description": scenario.description_hi if lang == "hi" else scenario.description_en,
                "expected": scenario.expected_hi if lang == "hi" else scenario.expected_en,
            }
            for scenario in SCENARIOS
        ]

    @app.post("/api/v1/demo/load", status_code=201)
    def load_demo_case(
        scenario: str = Query(DEFAULT_SCENARIO, min_length=1, max_length=40),
        lang: str = Query("en", pattern="^(en|hi)$"),
        user: str = Depends(current_user),
    ) -> dict:
        """Compose a labelled synthetic scenario through the real upload pipeline."""
        selected = get_scenario(scenario)
        lease = repo.create_lease(
            user,
            selected.property_hi if lang == "hi" else selected.property_en,
            selected.start_date,
        )
        repo.update_lease(user, lease["id"], scenario_id=selected.id)
        loaded = []
        for spec in selected.documents:
            path = SAMPLES_DIR / spec.filename
            # Run the real ingest path on the real sample bytes (synchronously here).
            result = asyncio.run(
                ingest(lease["id"], spec.kind, spec.effective_date, spec.filename, path.read_bytes(), user)
            )
            loaded.append(result["document"])
        return {
            "lease": lease_summary(lease, repo, user),
            "documents": loaded,
            "scenario": {
                **selected.as_dict(),
                "label": selected.label_hi if lang == "hi" else selected.label_en,
                "expected": selected.expected_hi if lang == "hi" else selected.expected_en,
            },
        }

    @app.post("/api/v1/leases/{lease_id}/demo/documents", status_code=201)
    def upload_demo_document(
        lease_id: str,
        kind: str = Query("lease", pattern="^(lease|amendment|invoice)$"),
        effective_date: date | None = Query(None),
        user: str = Depends(current_user),
    ) -> dict:
        """Attach the bundled sample for a document type (works in either provider mode)."""
        repo.get_lease(user, lease_id)
        defaults = {
            "lease": ("lease.txt", date(2025, 4, 1)),
            "amendment": ("amendment1.txt", date(2026, 1, 1)),
            "invoice": ("invoice_apr2026.txt", date(2026, 4, 1)),
        }
        filename, default_date = defaults[kind]
        path = SAMPLES_DIR / filename
        return asyncio.run(ingest(lease_id, kind, effective_date or default_date, filename, path.read_bytes(), user))

    @app.get("/api/v1/leases/{lease_id}/terms")
    def list_terms(lease_id: str, user: str = Depends(current_user)) -> list[dict]:
        repo.get_lease(user, lease_id)
        return [term_dict(t) for t in repo.terms[lease_id]]

    @app.post("/api/v1/leases/{lease_id}/audits", status_code=201)
    def run_audit(lease_id: str, user: str = Depends(current_user)) -> dict:
        lease = repo.get_lease(user, lease_id)
        if not repo.invoices[lease_id]:
            raise AppError("no_invoice", "Upload an invoice before running an audit.", 409)
        invoice = repo.invoices[lease_id][-1]
        findings = audit_invoice(repo.terms[lease_id], invoice, lease["start_date"])
        audit = repo.save_audit(user, lease_id, findings)
        return audit_payload(audit, repo, user)

    @app.get("/api/v1/audits/{audit_id}")
    def get_audit(audit_id: str, user: str = Depends(current_user)) -> dict:
        return audit_payload(repo.get_audit(user, audit_id), repo, user)

    @app.patch("/api/v1/findings/{finding_id}")
    def decide(finding_id: str, body: Decision, user: str = Depends(current_user)) -> dict:
        repo.decide(user, finding_id, body.decision)
        return finding_dict(repo.get_finding(user, finding_id), body.decision)

    @app.post("/api/v1/audits/{audit_id}/letter")
    def letter(
        audit_id: str,
        lang: str = Query("en", pattern="^(en|hi)$"),
        user: str = Depends(current_user),
    ) -> dict:
        audit = repo.get_audit(user, audit_id)
        lease = repo.get_lease(user, audit["lease_id"])
        approved = [
            repo.findings[fid]["finding"]
            for fid in audit["finding_ids"]
            if repo.approvals.get(fid) == "approved" and repo.findings[fid]["finding"].status == Status.CONFIRMED
        ]
        if not approved:
            raise AppError("no_approved_findings", "Approve at least one confirmed finding first.", 409)
        if not repo.invoices[audit["lease_id"]]:
            raise AppError("no_invoice", "No invoice is attached to this lease.", 409)
        period = repo.invoices[audit["lease_id"]][-1].period_start.strftime("%B %Y")
        result = build_letter(lease["property_label"], period, approved, lang)
        return {
            "letter": result.text,
            "share_text": result.whatsapp_message,
            "whatsapp_url": result.whatsapp_url,
            "included_count": result.included_count,
            "language": lang,
        }

    @app.get("/api/v1/impact")
    def overall_impact(user: str = Depends(current_user)) -> dict:
        findings = repo.all_findings(user)
        documents = sum(
            len(repo.documents[lease["id"]]) for lease in repo.list_leases(user) if lease["id"] in repo.documents
        )
        return compute_impact(with_decisions(repo, findings), documents, len(repo.audit_rows(user))).as_dict()

    @app.get("/api/v1/leases/{lease_id}/impact")
    def lease_impact(lease_id: str, user: str = Depends(current_user)) -> dict:
        return lease_summary(repo.get_lease(user, lease_id), repo, user)["impact"]

    return app


app = create_app()
