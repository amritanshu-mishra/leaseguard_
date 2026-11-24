"""Exercise the whole API pipeline against a running server.

Usage (from backend/, with the API running): python -m scripts.smoke_pipeline
Uses the bundled synthetic samples, so no API key is required.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx

BASE = os.environ.get("LEASEGUARD_API", "http://127.0.0.1:8000")
SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def check(client: httpx.Client, condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {label}")
    print(f"PASS: {label}")


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=20) as api:
        check(api, api.get("/health").json()["status"] == "ok", "health")
        config = api.get("/api/v1/config").json()
        check(api, config["provider"] in {"fixtures", "groq"}, f"provider = {config['provider']}")

        lease = api.post("/api/v1/leases", json={"property_label": "Shop 12", "start_date": "2026-11-24"}).json()
        lease_id = lease["id"]
        check(api, bool(lease_id), "create lease with placeholder start date")

        for name, kind, effective in (
            ("lease.pdf", "lease", "2025-04-01"),
            ("amendment1.txt", "amendment", "2026-01-01"),
            ("invoice_apr2026.txt", "invoice", "2026-04-01"),
        ):
            response = api.post(
                f"/api/v1/leases/{lease_id}/documents",
                data={"kind": kind, "effective_date": effective},
                files={"file": (name, (SAMPLES / name).read_bytes())},
            )
            check(api, response.status_code == 201, f"upload {name} -> {response.status_code}")

        detail = api.get(f"/api/v1/leases/{lease_id}").json()
        check(api, detail["start_date"] == "2025-04-01", "base lease corrected start date")
        check(api, len(detail["terms"]) == 4, "four grounded terms extracted")
        check(api, all(t["validated"] for t in detail["terms"]), "all quotes verified on cited pages")

        created = api.post(f"/api/v1/leases/{lease_id}/audits")
        check(api, created.status_code == 201, "run audit")
        audit = created.json()
        differences = sorted(f["difference_paise"] for f in audit["findings"])
        check(api, differences == [120_000, 200_000], f"differences {differences}")
        check(
            api,
            all(f["evidence"] and f["calculation"] for f in audit["findings"]),
            "evidence + calculation on every finding",
        )

        refreshed = api.get(f"/api/v1/audits/{audit['audit_id']}").json()
        check(api, refreshed["invoice"] == audit["invoice"], "GET audit matches POST payload")
        check(api, refreshed["period_start"] == "2026-04-01", "GET audit has period")

        first = audit["findings"][0]
        decision = api.patch(f"/api/v1/findings/{first['id']}", json={"decision": "approved"})
        check(api, decision.json()["decision"] == "approved", "approve finding")
        after = api.get(f"/api/v1/audits/{audit['audit_id']}").json()
        check(
            api,
            after["impact"]["awaiting_review_paise"] == 320_000 - first["difference_paise"],
            "awaiting-review impact updates after decision",
        )

        for finding in audit["findings"]:
            api.patch(f"/api/v1/findings/{finding['id']}", json={"decision": "approved"})
        for lang, marker in (("en", "discrepancies for review"), ("hi", "समीक्षा")):
            response = api.post(f"/api/v1/audits/{audit['audit_id']}/letter?lang={lang}")
            check(api, marker in response.json()["letter"], f"{lang} letter generated")
            check(
                api,
                response.json()["whatsapp_url"].startswith("https://wa.me/?text="),
                f"{lang} WhatsApp draft link generated",
            )

        impact = api.get("/api/v1/impact").json()
        check(api, impact["excess_detected_paise"] == 320_000, "overall excess impact")
        check(api, "No money is recovered" in impact["disclaimer"], "no recovery claim")
        check(api, api.delete(f"/api/v1/leases/{lease_id}").status_code == 204, "delete lease")

        catalogue = api.get("/api/v1/demo/scenarios").json()
        check(api, len(catalogue) >= 6, f"{len(catalogue)} demo scenarios available")
        for scenario in catalogue:
            loaded = api.post(f"/api/v1/demo/load?scenario={scenario['id']}").json()
            scenario_lease_id = loaded["lease"]["id"]
            scenario_audit = api.post(f"/api/v1/leases/{scenario_lease_id}/audits").json()
            findings = sorted(scenario_audit["findings"], key=lambda f: f["status"] != "uncertain")
            statuses = [f["status"] for f in findings]
            reasons = [f["reason"] for f in findings]
            check(
                api,
                statuses == scenario["expected_statuses"] and reasons == scenario["expected_reasons"],
                f"scenario {scenario['id']}: {statuses or 'no findings'}",
            )
            api.delete(f"/api/v1/leases/{scenario_lease_id}")

    print("\nPIPELINE OK — ready for demo.")


if __name__ == "__main__":
    main()
