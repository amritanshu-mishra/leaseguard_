"""In-memory repository with per-user scoping and an append-only audit log.

The demo intentionally keeps data in memory; see README for the persistence
trade-off. Every lease-scoped read is filtered by user ID (defence in depth).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from app.domain.models import Finding


class NotFound(Exception):
    pass


class ConflictError(Exception):
    pass


class InMemoryRepo:
    def __init__(self) -> None:
        self.leases: dict[str, dict] = {}
        self.terms: dict[str, list] = {}
        self.invoices: dict[str, list] = {}
        self.documents: dict[str, list] = {}
        self.audits: dict[str, dict] = {}
        self.findings: dict[str, dict] = {}
        self.approvals: dict[str, str] = {}
        self.log: list[dict] = []

    def _event(self, user: str, action: str, entity_id: str) -> None:
        # IDs only - never document text, tokens or personal data.
        self.log.append({"user": user, "action": action, "entity_id": entity_id, "at": datetime.now(UTC).isoformat()})

    def create_lease(self, user: str, label: str, start: date) -> dict:
        lease = {
            "id": str(uuid.uuid4()),
            "user_id": user,
            "property_label": label,
            "start_date": start,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.leases[lease["id"]] = lease
        self.terms[lease["id"]] = []
        self.invoices[lease["id"]] = []
        self.documents[lease["id"]] = []
        self._event(user, "lease.create", lease["id"])
        return lease

    def update_lease(self, user: str, lease_id: str, **changes) -> dict:
        lease = self.get_lease(user, lease_id)
        lease.update(changes)
        self._event(user, "lease.update", lease_id)
        return lease

    def get_lease(self, user: str, lease_id: str) -> dict:
        lease = self.leases.get(lease_id)
        if not lease or lease["user_id"] != user:
            raise NotFound("lease")  # same answer for missing and foreign rows
        return lease

    def list_leases(self, user: str) -> list[dict]:
        return [lease for lease in self.leases.values() if lease["user_id"] == user]

    def add_document(self, lease_id: str, document: dict) -> None:
        if any(d["sha256"] == document["sha256"] for d in self.documents[lease_id]):
            raise ConflictError("This exact file has already been uploaded for this lease.")
        self.documents[lease_id].append(document)
        self._event(self.leases[lease_id]["user_id"], f"document.{document['kind']}", document["id"])

    def add_terms(self, lease_id: str, terms: list) -> None:
        self.terms[lease_id].extend(terms)

    def add_invoice(self, lease_id: str, invoice) -> None:
        self.invoices[lease_id].append(invoice)

    def save_audit(self, user: str, lease_id: str, findings: list[Finding]) -> dict:
        audit_id = str(uuid.uuid4())
        stored: list[str] = []
        for finding in findings:
            finding_id = str(uuid.uuid4())
            self.findings[finding_id] = {
                "id": finding_id,
                "audit_id": audit_id,
                "finding": finding,
                "user_id": user,
            }
            stored.append(finding_id)
        self.audits[audit_id] = {
            "id": audit_id,
            "lease_id": lease_id,
            "user_id": user,
            "finding_ids": stored,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._event(user, "audit.create", audit_id)
        return self.audits[audit_id]

    def get_audit(self, user: str, audit_id: str) -> dict:
        row = self.audits.get(audit_id)
        if not row or row["user_id"] != user:
            raise NotFound("audit")
        return row

    def get_finding(self, user: str, finding_id: str) -> dict:
        row = self.findings.get(finding_id)
        if not row or row["user_id"] != user:
            raise NotFound("finding")
        return row

    def decide(self, user: str, finding_id: str, decision: str) -> None:
        self.get_finding(user, finding_id)
        self.approvals[finding_id] = decision
        self._event(user, f"finding.{decision}", finding_id)

    def delete_lease(self, user: str, lease_id: str) -> None:
        self.get_lease(user, lease_id)
        audit_ids = [a["id"] for a in self.audits.values() if a["lease_id"] == lease_id]
        finding_ids = [fid for aid in audit_ids for fid in self.audits[aid]["finding_ids"]]
        for fid in finding_ids:
            self.findings.pop(fid, None)
            self.approvals.pop(fid, None)
        for aid in audit_ids:
            self.audits.pop(aid, None)
        for key in (lease_id,):
            self.terms.pop(key, None)
            self.invoices.pop(key, None)
            self.documents.pop(key, None)
        self.leases.pop(lease_id, None)
        self._event(user, "lease.delete", lease_id)

    def all_findings(self, user: str) -> list[dict]:
        return [row for row in self.findings.values() if row["user_id"] == user]

    def audit_rows(self, user: str) -> list[dict]:
        return [row for row in self.audits.values() if row["user_id"] == user]
