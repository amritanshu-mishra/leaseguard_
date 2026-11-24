"""Golden synthetic cases G1-G6 and uncertainty cases U1-U2."""

from __future__ import annotations

from datetime import date

from app.domain.checks import audit_invoice, check_rent_escalation
from app.domain.models import Invoice, Reason, Status, Term, TermType
from app.domain.quotes import quote_in_text
from app.services.extraction_service import ExtractionService


def _lease_terms(rate: int = 1000, effective: date = date(2025, 4, 1), validated: bool = True) -> list[Term]:
    return [
        Term(TermType.BASE_RENT, 4_000_000, "rent Rs. 40,000", 2, "Lease", date(2025, 4, 1)),
        Term(
            TermType.ESCALATION,
            rate,
            "escalation percent",
            3,
            "Lease",
            effective,
            validated,
        ),
        Term(TermType.MAINTENANCE_CAP, 400_000, "cap Rs. 4,000", 4, "Lease", date(2025, 4, 1)),
    ]


def test_g1_amendment_ignored_old_rate_is_not_used() -> None:
    terms = _lease_terms() + [Term(TermType.ESCALATION, 500, "cap 5%", 1, "Amendment 1", date(2026, 1, 1))]
    finding = check_rent_escalation(terms, Invoice(date(2026, 4, 1), 4_400_000, 520_000), date(2025, 4, 1))
    assert finding and finding.difference_paise == 200_000
    assert "Amendment 1" in " ".join(finding.calculation)


def test_g2_maintenance_over_cap() -> None:
    findings = audit_invoice(_lease_terms(), Invoice(date(2026, 4, 1), 4_200_000, 520_000), date(2025, 4, 1))
    cap = next(f for f in findings if f.check == "maintenance_cap")
    assert cap.status == Status.CONFIRMED and cap.difference_paise == 120_000


def test_g3_clean_invoice_has_no_findings() -> None:
    assert audit_invoice(_lease_terms(), Invoice(date(2026, 4, 1), 4_200_000, 380_000), date(2025, 4, 1)) == []


def test_g4_ambiguous_clause_is_uncertain() -> None:
    terms = [
        _lease_terms()[0],
        Term(
            TermType.ESCALATION,
            None,
            "reasonable increase in line with the market rate",
            1,
            "Lease",
            date(2025, 4, 1),
            ambiguous=True,
        ),
        _lease_terms()[2],
    ]
    finding = check_rent_escalation(terms, Invoice(date(2026, 4, 1), 4_400_000, 0), date(2025, 4, 1))
    assert finding and finding.status == Status.UNCERTAIN
    assert finding.reason == Reason.CLAUSE_AMBIGUOUS and finding.difference_paise is None


def test_g5_conflicting_amendments() -> None:
    terms = _lease_terms() + [
        Term(TermType.ESCALATION, 500, "5% cap", 1, "Amendment A", date(2026, 1, 1)),
        Term(TermType.ESCALATION, 700, "7% cap", 1, "Amendment B", date(2026, 1, 1)),
    ]
    finding = check_rent_escalation(terms, Invoice(date(2026, 4, 1), 4_400_000, 0), date(2025, 4, 1))
    assert (
        finding
        and finding.reason == Reason.CONFLICTING_TERMS
        and len(finding.evidence if hasattr(finding, "evidence") else finding.terms) == 2
    )


def test_g6_amendment_not_yet_effective() -> None:
    terms = _lease_terms() + [Term(TermType.ESCALATION, 500, "5% cap", 1, "Amendment", date(2026, 7, 1))]
    finding = check_rent_escalation(terms, Invoice(date(2026, 4, 1), 4_400_000, 0), date(2025, 4, 1))
    assert finding is None


def test_u1_unverifiable_quote_becomes_uncertain() -> None:
    from app.schemas import ExtractedTerm, ExtractedTerms

    class HallucinatingClient:
        def extract_terms(self, doc_name, pages, hint=None):
            return ExtractedTerms(
                terms=[
                    ExtractedTerm(
                        term_type="base_rent_paise",
                        value=5_000_000,
                        source_quote="the rent is Rs. 50,000",
                        page=1,
                    )
                ]
            )

        def extract_invoice(self, doc_name, pages, hint=None):
            raise AssertionError("not used")

    terms = ExtractionService(HallucinatingClient()).terms_from_document(
        "lease", date(2025, 4, 1), ["the rent is Rs. 40,000"]
    )
    assert len(terms) == 1 and terms[0].validated is False


def test_u2_missing_term_is_uncertain() -> None:
    findings = audit_invoice(
        [Term(TermType.BASE_RENT, 4_000_000, "rent", 1, "Lease", date(2025, 4, 1))],
        Invoice(date(2026, 4, 1), 4_200_000, 520_000),
        date(2025, 4, 1),
    )
    assert any(f.reason == Reason.TERM_NOT_FOUND for f in findings)
    assert all(not quote_in_text("fabricated", "") for _ in [0])


def test_quote_must_be_on_the_cited_page() -> None:
    from app.schemas import ExtractedTerm, ExtractedTerms

    class WrongPageClient:
        def extract_terms(self, doc_name, pages, hint=None):
            return ExtractedTerms(
                terms=[
                    ExtractedTerm(
                        term_type="base_rent_paise",
                        value=4_000_000,
                        source_quote="rent on page two",
                        page=1,
                    )
                ]
            )

        def extract_invoice(self, doc_name, pages, hint=None):
            raise AssertionError("not used")

    terms = ExtractionService(WrongPageClient()).terms_from_document(
        "lease", date(2025, 4, 1), ["nothing here", "rent on page two"]
    )
    assert terms[0].validated is False
    assert terms[0].page == 1
