"""Unit tests for pure domain rules."""

from __future__ import annotations

from datetime import date

import pytest

from app.domain.models import Term, TermType
from app.domain.money import Money, indian_group, round_half_up_div
from app.domain.precedence import (
    Conflict,
    Controlling,
    Missing,
    Unverified,
    controlling_term,
)
from app.domain.quotes import quote_in_text


def test_money_rejects_floats_and_bools() -> None:
    with pytest.raises(TypeError):
        Money(10.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Money(True)  # type: ignore[arg-type]


def test_round_half_up_div() -> None:
    assert round_half_up_div(5, 2) == 3
    assert round_half_up_div(4_200_000 * 10_500, 10_000) == 4_410_000


def test_apply_bp_exact_and_rounding() -> None:
    assert Money(4_000_000).apply_bp(500).paise == 4_200_000
    assert Money(101).apply_bp(1000).paise == 111
    assert Money(1).apply_bp(5000).paise == 2


def test_indian_grouping_and_format() -> None:
    assert indian_group(1_250_000) == "12,50,000"
    assert indian_group(999) == "999"
    assert Money(4_200_000).format() == "Rs. 42,000"
    assert Money(-120_000).format() == "-Rs. 1,200"


def test_quote_gate_ignores_whitespace_and_case() -> None:
    assert quote_in_text("The   Monthly Rent", "the monthly\nrent is Rs. 40,000")
    assert not quote_in_text("Rs. 50,000", "the monthly rent is Rs. 40,000")


def _term(value: int, when: date, validated: bool = True, ambiguous: bool = False) -> Term:
    return Term(TermType.ESCALATION, value, "quote", 1, "doc", when, validated, ambiguous)


def test_latest_effective_term_wins() -> None:
    outcome = controlling_term(
        [_term(1000, date(2025, 4, 1)), _term(500, date(2026, 1, 1))],
        TermType.ESCALATION,
        date(2026, 4, 1),
    )
    assert isinstance(outcome, Controlling) and outcome.term.value == 500


def test_future_amendment_does_not_apply() -> None:
    outcome = controlling_term(
        [_term(1000, date(2025, 4, 1)), _term(500, date(2026, 7, 1))],
        TermType.ESCALATION,
        date(2026, 4, 1),
    )
    assert isinstance(outcome, Controlling) and outcome.term.value == 1000


def test_same_date_different_values_conflict() -> None:
    outcome = controlling_term(
        [_term(500, date(2026, 1, 1)), _term(700, date(2026, 1, 1))],
        TermType.ESCALATION,
        date(2026, 4, 1),
    )
    assert isinstance(outcome, Conflict) and len(outcome.terms) == 2


def test_missing_unverified_and_ambiguous() -> None:
    assert isinstance(controlling_term([], TermType.ESCALATION, date(2026, 1, 1)), Missing)
    assert isinstance(
        controlling_term([_term(500, date(2025, 1, 1), validated=False)], TermType.ESCALATION, date(2026, 1, 1)),
        Unverified,
    )
    from app.domain.precedence import Ambiguous

    assert isinstance(
        controlling_term([_term(0, date(2025, 1, 1), ambiguous=True)], TermType.ESCALATION, date(2026, 1, 1)),
        Ambiguous,
    )
