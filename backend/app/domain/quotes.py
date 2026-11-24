"""The anti-hallucination gate: every fact must be grounded in source text."""

from __future__ import annotations

import re


def normalise(text: str) -> str:
    """Case-fold and collapse all whitespace, including line breaks."""
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_in_text(quote: str, text: str) -> bool:
    """Require a verbatim (whitespace-normalised) substring match."""
    needle = normalise(quote)
    return bool(needle) and needle in normalise(text)
