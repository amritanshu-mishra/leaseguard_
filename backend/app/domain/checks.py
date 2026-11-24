"""Deterministic charge checks. The model never calculates anything."""

from __future__ import annotations

from datetime import date

from .models import Finding, Invoice, Reason, Status, Term, TermType
from .money import Money
from .precedence import Ambiguous, Conflict, Controlling, Unverified, controlling_term

CHECK_RENT = "rent_escalation"
CHECK_MAINTENANCE = "maintenance_cap"


def _uncertain(check: str, outcome, label: str) -> Finding:
    if isinstance(outcome, Conflict):
        return Finding(
            check,
            Status.UNCERTAIN,
            f"Two documents disagree about {label}. Please choose before any amount is calculated.",
            Reason.CONFLICTING_TERMS,
            terms=outcome.terms,
        )
    if isinstance(outcome, Ambiguous):
        return Finding(
            check,
            Status.UNCERTAIN,
            f"The clause on {label} is unclear, so no amount was calculated.",
            Reason.CLAUSE_AMBIGUOUS,
            terms=(outcome.term,),
        )
    if isinstance(outcome, Unverified):
        return Finding(
            check,
            Status.UNCERTAIN,
            f"The quoted text for {label} could not be verified in the document.",
            Reason.QUOTE_UNVERIFIED,
            terms=(outcome.term,),
        )
    return Finding(
        check,
        Status.UNCERTAIN,
        f"No term for {label} was found. Nothing was assumed.",
        Reason.TERM_NOT_FOUND,
    )


def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # 29 February
        return d.replace(year=d.year + years, day=28)


def _anniversaries(start: date, period: date) -> int:
    return max(period.year - start.year - ((period.month, period.day) < (start.month, start.day)), 0)


def _source(t: Term) -> str:
    return f"{t.document_name}, eff. {t.effective_date.isoformat()}"


def check_rent_escalation(terms: list[Term], invoice: Invoice, lease_start: date) -> Finding | None:
    """Apply the controlling escalation once per completed anniversary."""
    base = controlling_term(terms, TermType.BASE_RENT, lease_start)
    if not isinstance(base, Controlling):
        return _uncertain(CHECK_RENT, base, "the base rent")

    rent = Money(base.term.value or 0)
    steps = [
        f"Base rent: {rent.format()} per month — {_source(base.term)}",
    ]
    used: list[Term] = []
    for year in range(1, _anniversaries(lease_start, invoice.period_start) + 1):
        anniversary = _add_years(lease_start, year)
        rate = controlling_term(terms, TermType.ESCALATION, anniversary)
        if not isinstance(rate, Controlling):
            return _uncertain(CHECK_RENT, rate, "the rent escalation")
        bp = rate.term.value or 0
        before = rent.paise
        rent = rent.apply_bp(bp)
        steps.append(
            f"Anniversary {year} ({anniversary.isoformat()}): {bp:,} bp from "
            f"{_source(rate.term)} → {before:,} × {10_000 + bp:,} ÷ 10,000 = {rent.paise:,} paise"
        )
        used.append(rate.term)

    billed = Money(invoice.rent_paise)
    if not billed > rent:
        return None
    difference = billed - rent
    steps.append(f"Expected {rent.format()} vs billed {billed.format()} → excess {difference.format()}")
    return Finding(
        CHECK_RENT,
        Status.CONFIRMED,
        f"Rent billed is {billed.format()} but the controlling terms give {rent.format()}.",
        billed_paise=billed.paise,
        expected_paise=rent.paise,
        difference_paise=difference.paise,
        terms=tuple(used or [base.term]),
        calculation=tuple(steps),
    )


def check_maintenance_cap(terms: list[Term], invoice: Invoice, lease_start: date) -> Finding | None:
    """Compare the billed maintenance amount with the controlling flat monthly cap."""
    if invoice.maintenance_paise <= 0:
        return None
    cap = controlling_term(terms, TermType.MAINTENANCE_CAP, invoice.period_start)
    if not isinstance(cap, Controlling):
        return _uncertain(CHECK_MAINTENANCE, cap, "the maintenance cap")
    expected, billed = Money(cap.term.value or 0), Money(invoice.maintenance_paise)
    if not billed > expected:
        return None
    difference = billed - expected
    steps = (
        f"Cap: {expected.format()} per month — {_source(cap.term)}",
        f"Billed: {billed.format()} − cap {expected.format()} → excess {difference.format()}",
    )
    return Finding(
        CHECK_MAINTENANCE,
        Status.CONFIRMED,
        f"Maintenance billed is {billed.format()} but the cap is {expected.format()}.",
        billed_paise=billed.paise,
        expected_paise=expected.paise,
        difference_paise=difference.paise,
        terms=(cap.term,),
        calculation=steps,
    )


def audit_invoice(terms: list[Term], invoice: Invoice, lease_start: date) -> list[Finding]:
    """Return confirmed discrepancies and uncertain items; undercharges are omitted."""
    results = [
        check_rent_escalation(terms, invoice, lease_start),
        check_maintenance_cap(terms, invoice, lease_start),
    ]
    return [finding for finding in results if finding is not None]
