"""Amendment precedence as a pure function with five explicit outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .models import Term, TermType


@dataclass(frozen=True)
class Controlling:
    term: Term


@dataclass(frozen=True)
class Missing:
    term_type: TermType


@dataclass(frozen=True)
class Unverified:
    term: Term


@dataclass(frozen=True)
class Conflict:
    terms: tuple[Term, ...]


@dataclass(frozen=True)
class Ambiguous:
    term: Term


def controlling_term(terms: list[Term], term_type: TermType, as_of: date):
    """Latest validated effective term on or before `as_of` wins.

    Ties with different values are conflicts; unverified terms never become facts.
    """
    same = [t for t in terms if t.term_type == term_type and t.effective_date <= as_of]
    eligible = [t for t in same if t.validated]
    if not eligible:
        unverified = [t for t in same if not t.validated]
        return Unverified(unverified[0]) if unverified else Missing(term_type)
    latest = max(t.effective_date for t in eligible)
    top = [t for t in eligible if t.effective_date == latest]
    if len({t.value for t in top}) > 1:
        return Conflict(tuple(top))
    term = top[0]
    if term.ambiguous or term.value is None:
        return Ambiguous(term)
    return Controlling(term)
