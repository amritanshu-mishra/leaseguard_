"""End-to-end API tests: upload, audit, evidence, decisions, letter, share, impact."""

from __future__ import annotations

from pathlib import Path

from app.domain.quotes import quote_in_text

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def _upload(client, lease_id, filename, kind, effective):
    return client.post(
        f"/api/v1/leases/{lease_id}/documents",
        data={"kind": kind, "effective_date": effective},
        files={"file": (filename, (SAMPLES / filename).read_bytes(), "application/octet-stream")},
    )


def _prepare_lease(client):
    lease_id = client.post("/api/v1/leases", json={"property_label": "Shop 12", "start_date": "2025-04-01"}).json()[
        "id"
    ]
    assert _upload(client, lease_id, "lease.txt", "lease", "2025-04-01").status_code == 201
    assert _upload(client, lease_id, "amendment1.txt", "amendment", "2026-01-01").status_code == 201
    assert _upload(client, lease_id, "invoice_apr2026.txt", "invoice", "2026-04-01").status_code == 201
    return lease_id


def test_health_and_config(client):
    assert client.get("/health").json()["status"] == "ok"
    config = client.get("/api/v1/config").json()
    assert config["provider"] == "fixtures" and config["live"] is False


def test_demo_loader_creates_complete_case(client):
    response = client.post("/api/v1/demo/load")
    assert response.status_code == 201
    body = response.json()
    assert body["lease"]["document_count"] == 3
    assert len(body["documents"]) == 3
    assert client.get(f"/api/v1/leases/{body['lease']['id']}").status_code == 200


def test_end_to_end_flow_with_evidence_and_letter(client):
    lease_id = _prepare_lease(client)
    terms = client.get(f"/api/v1/leases/{lease_id}/terms").json()
    assert len(terms) == 4
    assert all(t["validated"] for t in terms)
    assert all(quote_in_text(t["quote"], (SAMPLES / f"{t['document_file']}.txt").read_text()) for t in terms)

    audit = client.post(f"/api/v1/leases/{lease_id}/audits").json()
    assert len(audit["findings"]) == 2
    confirmed = [f for f in audit["findings"] if f["status"] == "confirmed"]
    assert sorted(f["difference_paise"] for f in confirmed) == [120_000, 200_000]
    for finding in confirmed:
        assert finding["evidence"]
        assert finding["calculation"]
        evidence = finding["evidence"][0]
        assert evidence["quote"] and evidence["document"] and evidence["page"] and evidence["effective_date"]
        assert "Rs." in " ".join(finding["calculation"])

    blocked = client.post(f"/api/v1/audits/{audit['audit_id']}/letter")
    assert blocked.status_code == 409
    for finding in confirmed:
        response = client.patch(f"/api/v1/findings/{finding['id']}", json={"decision": "approved"})
        assert response.json()["decision"] == "approved"

    letter = client.post(f"/api/v1/audits/{audit['audit_id']}/letter").json()
    assert "discrepancies for review" in letter["letter"]
    assert "Amendment 1" in letter["letter"]
    assert letter["whatsapp_url"].startswith("https://wa.me/?text=")
    assert letter["included_count"] == 2

    hindi = client.post(f"/api/v1/audits/{audit['audit_id']}/letter?lang=hi").json()
    assert "समीक्षा" in hindi["letter"] and "पृष्ठ" in hindi["letter"]


def test_impact_has_no_recovery_claim(client):
    lease_id = _prepare_lease(client)
    audit = client.post(f"/api/v1/leases/{lease_id}/audits").json()
    assert audit["impact"]["excess_detected_paise"] == 320_000
    assert audit["impact"]["awaiting_review_paise"] == 320_000
    assert audit["impact"]["estimated_minutes_saved"] > 0
    assert "No money is recovered" in audit["impact"]["disclaimer"]
    overall = client.get("/api/v1/impact").json()
    assert overall["excess_detected_paise"] == 320_000


def test_upload_renamed_and_pdf_samples_work(client):
    lease_id = client.post("/api/v1/leases", json={"property_label": "Renamed", "start_date": "2025-04-01"}).json()[
        "id"
    ]
    first = _upload(client, lease_id, "lease.txt", "lease", "2025-04-01")
    assert first.status_code == 201
    renamed = client.post(
        f"/api/v1/leases/{lease_id}/documents",
        data={"kind": "amendment", "effective_date": "2026-01-01"},
        files={"file": ("my-renamed-file.pdf", (SAMPLES / "amendment1.pdf").read_bytes(), "application/pdf")},
    )
    assert renamed.status_code == 201, renamed.text
    assert renamed.json()["terms_found"] == 1


def test_upload_rejects_bad_files_and_duplicates(client):
    lease_id = client.post("/api/v1/leases", json={"property_label": "Bad files", "start_date": "2025-04-01"}).json()[
        "id"
    ]
    bad = client.post(
        f"/api/v1/leases/{lease_id}/documents",
        data={"kind": "lease", "effective_date": "2025-04-01"},
        files={"file": ("virus.exe", b"MZ\x00\x01", "application/octet-stream")},
    )
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "unsupported_file"
    fake_pdf = client.post(
        f"/api/v1/leases/{lease_id}/documents",
        data={"kind": "lease", "effective_date": "2025-04-01"},
        files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
    )
    assert fake_pdf.status_code == 400
    original = _upload(client, lease_id, "lease.txt", "lease", "2025-04-01")
    assert original.status_code == 201
    duplicate = _upload(client, lease_id, "lease.txt", "lease", "2025-04-01")
    assert duplicate.status_code == 409


def test_user_isolation_and_not_found(client):
    lease_id = _prepare_lease(client)
    assert client.get(f"/api/v1/leases/{lease_id}").status_code == 200
    assert client.get("/api/v1/leases/does-not-exist").status_code == 404
    audit = client.post(f"/api/v1/leases/{lease_id}/audits").json()
    assert client.post(f"/api/v1/audits/{audit['audit_id']}/letter").status_code == 409
    assert client.delete(f"/api/v1/leases/{lease_id}").status_code == 204
    assert client.get(f"/api/v1/leases/{lease_id}").status_code == 404


def test_audit_without_invoice_is_409(client):
    lease_id = client.post("/api/v1/leases", json={"property_label": "No invoice", "start_date": "2025-04-01"}).json()[
        "id"
    ]
    assert client.post(f"/api/v1/leases/{lease_id}/audits").status_code == 409


def test_get_audit_has_same_shape_as_create_and_reflects_decisions(client):
    lease_id = _prepare_lease(client)
    created = client.post(f"/api/v1/leases/{lease_id}/audits").json()
    for key in ("audit_id", "lease_id", "period_start", "invoice", "findings", "impact"):
        assert key in created, f"create response missing {key}"

    refreshed = client.get(f"/api/v1/audits/{created['audit_id']}").json()
    for key in ("audit_id", "lease_id", "period_start", "invoice", "findings", "impact"):
        assert key in refreshed, f"refresh response missing {key}"
    assert refreshed["period_start"] == created["period_start"] == "2026-04-01"
    assert refreshed["invoice"] == created["invoice"]
    assert [f["id"] for f in refreshed["findings"]] == [f["id"] for f in created["findings"]]

    first = created["findings"][0]
    updated = client.patch(f"/api/v1/findings/{first['id']}", json={"decision": "approved"}).json()
    assert updated["decision"] == "approved"
    after = client.get(f"/api/v1/audits/{created['audit_id']}").json()
    assert next(f for f in after["findings"] if f["id"] == first["id"])["decision"] == "approved"
    assert after["impact"]["awaiting_review_paise"] == 320_000 - first["difference_paise"]


def test_fixture_mode_rejects_edited_sample_instead_of_guessing(client):
    lease_id = client.post("/api/v1/leases", json={"property_label": "Edited", "start_date": "2025-04-01"}).json()["id"]
    original = (SAMPLES / "lease.txt").read_bytes()
    edited = original.replace(b"Rs. 40,000", b"Rs. 99,000")
    response = client.post(
        f"/api/v1/leases/{lease_id}/documents",
        data={"kind": "lease", "effective_date": "2025-04-01"},
        files={"file": ("lease.txt", edited, "text/plain")},
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "extraction_failed"


def test_uploading_base_lease_corrects_placeholder_start_date(client):
    lease_id = client.post("/api/v1/leases", json={"property_label": "Placeholder", "start_date": "2026-11-24"}).json()[
        "id"
    ]
    assert _upload(client, lease_id, "lease.txt", "lease", "2025-04-01").status_code == 201
    assert client.get(f"/api/v1/leases/{lease_id}").json()["start_date"] == "2025-04-01"
    assert _upload(client, lease_id, "amendment1.txt", "amendment", "2026-01-01").status_code == 201
    assert _upload(client, lease_id, "invoice_apr2026.txt", "invoice", "2026-04-01").status_code == 201
    audit = client.post(f"/api/v1/leases/{lease_id}/audits").json()
    assert any(f["difference_paise"] == 200_000 for f in audit["findings"])
