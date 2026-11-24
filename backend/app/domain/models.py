"""Framework-free domain objects and enumerations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TermType(StrEnum):
    BASE_RENT = "base_rent_paise"
    ESCALATION = "escalation_rate_bp"
    MAINTENANCE_CAP = "maintenance_cap_paise"


TERM_LABELS: dict[TermType, str] = {
    TermType.BASE_RENT: "Base rent",
    TermType.ESCALATION: "Annual escalation",
    TermType.MAINTENANCE_CAP: "Maintenance cap",
}

TERM_UNITS: dict[TermType, str] = {
    TermType.BASE_RENT: "paise/month",
    TermType.ESCALATION: "basis points",
    TermType.MAINTENANCE_CAP: "paise/month",
}


class Status(StrEnum):
    CONFIRMED = "confirmed"
    UNCERTAIN = "uncertain"


class Reason(StrEnum):
    QUOTE_UNVERIFIED = "quote_unverified"
    CLAUSE_AMBIGUOUS = "clause_ambiguous"
    CONFLICTING_TERMS = "conflicting_terms"
    TERM_NOT_FOUND = "term_not_found"


@dataclass(frozen=True)
class Term:
    term_type: TermType
    value: int | None
    source_quote: str
    page: int
    document_name: str
    effective_date: date
    validated: bool = True
    ambiguous: bool = False
    confidence: float = 1.0


@dataclass(frozen=True)
class Invoice:
    period_start: date
    rent_paise: int
    maintenance_paise: int


@dataclass(frozen=True)
class Finding:
    check: str
    status: Status
    message: str
    reason: Reason | None = None
    billed_paise: int | None = None
    expected_paise: int | None = None
    difference_paise: int | None = None
    terms: tuple[Term, ...] = ()
    calculation: tuple[str, ...] = ()


def display_document_name(stem: str) -> str:
    """Turn a fixture file stem into the name shown to a tenant."""
    import re

    match = re.fullmatch(r"amendment[_ ]?(\d+)", stem, flags=re.IGNORECASE)
    if match:
        return f"Amendment {match.group(1)}"
    if stem.lower() == "lease":
        return "Lease Agreement"
    if stem.lower().startswith("invoice"):
        return stem.replace("_", " ").replace("apr", "April").title()
    return stem.replace("_", " ").title()
