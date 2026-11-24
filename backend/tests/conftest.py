"""Shared fixtures for the backend test suite."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.api.main import create_app
from app.domain.models import Invoice, Term, TermType
from app.infra.llm_fixture import FixtureClient

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.fixture
def sample_client() -> FixtureClient:
    return FixtureClient.from_dir(SAMPLES / "fixtures", corpus_dir=SAMPLES)


@pytest.fixture
def client(sample_client):
    from fastapi.testclient import TestClient

    with TestClient(create_app(client=sample_client)) as test_client:
        yield test_client


@pytest.fixture
def lease(client):
    response = client.post("/api/v1/leases", json={"property_label": "Shop 12", "start_date": "2025-04-01"})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def sample_terms() -> list[Term]:
    return [
        Term(TermType.BASE_RENT, 4_000_000, "The monthly rent shall be Rs. 40,000", 2, "Lease", date(2025, 4, 1)),
        Term(
            TermType.ESCALATION,
            1000,
            "increase by ten percent (10%) per annum",
            3,
            "Lease",
            date(2025, 4, 1),
        ),
        Term(
            TermType.MAINTENANCE_CAP,
            400_000,
            "maintenance capped at Rs. 4,000",
            4,
            "Lease",
            date(2025, 4, 1),
        ),
    ]


@pytest.fixture
def april_invoice() -> Invoice:
    return Invoice(date(2026, 4, 1), 4_400_000, 520_000)
