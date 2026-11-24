"""Every selectable synthetic scenario must load and audit as advertised."""

from __future__ import annotations

import pytest

from app.demo import EXPECTED_RESULTS, SCENARIOS

EXPECTED = EXPECTED_RESULTS


def test_scenario_catalogue_is_bilingual_and_complete(client):
    catalogue = client.get("/api/v1/demo/scenarios?lang=hi").json()
    assert {item["id"] for item in catalogue} == set(EXPECTED)
    for item in catalogue:
        assert item["label"] and item["description"] and item["expected"]
        assert item["label_en"] and item["label_hi"]
        assert item["documents"]


@pytest.mark.parametrize("scenario_id", sorted(EXPECTED))
def test_each_scenario_loads_through_the_pipeline(client, scenario_id):
    result = client.post(f"/api/v1/demo/load?scenario={scenario_id}&lang=hi").json()
    lease = result["lease"]
    assert lease["scenario_id"] == scenario_id
    assert lease["document_count"] == len(result["documents"])

    audit = client.post(f"/api/v1/leases/{lease['id']}/audits").json()
    findings = sorted(audit["findings"], key=lambda f: f["status"] != "uncertain")
    expected = EXPECTED[scenario_id]
    assert [f["status"] for f in findings] == expected["statuses"], scenario_id
    assert [f["reason"] for f in findings] == expected["reasons"], scenario_id

    if scenario_id == "amendment":
        assert sorted(f["difference_paise"] for f in findings) == [120_000, 200_000]
    if scenario_id == "conflict":
        uncertain = next(f for f in findings if f["status"] == "uncertain")
        assert len(uncertain["evidence"]) == 2
    if scenario_id in {"ambiguous", "missing-cap", "conflict"}:
        uncertain = next(f for f in findings if f["status"] == "uncertain")
        assert uncertain["difference_paise"] is None
        assert uncertain["calculation"] == []


def test_unknown_scenario_falls_back_to_default(client):
    response = client.post("/api/v1/demo/load?scenario=does-not-exist")
    assert response.status_code == 201
    assert response.json()["lease"]["scenario_id"] == "amendment"
    assert len(SCENARIOS) >= 6


def test_bundled_document_can_be_attached_to_an_existing_lease(client):
    lease_id = client.post(
        "/api/v1/leases", json={"property_label": "Manual upload", "start_date": "2026-11-24"}
    ).json()["id"]
    for kind, expected_key in (("lease", "terms_found"), ("amendment", "terms_found"), ("invoice", "invoice")):
        response = client.post(f"/api/v1/leases/{lease_id}/demo/documents?kind={kind}")
        assert response.status_code == 201, response.text
        assert expected_key in response.json()
    detail = client.get(f"/api/v1/leases/{lease_id}").json()
    assert detail["document_count"] == 3
    assert detail["start_date"] == "2025-04-01"
    audit = client.post(f"/api/v1/leases/{lease_id}/audits").json()
    assert sorted(f["difference_paise"] for f in audit["findings"]) == [120_000, 200_000]
