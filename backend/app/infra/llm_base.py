"""Provider interface. Services depend on this, never on a vendor SDK."""

from __future__ import annotations

from typing import Protocol

from app.schemas import ExtractedInvoice, ExtractedTerms


class ExtractionError(Exception):
    """Raised when a provider cannot return usable structured output."""

    def __init__(self, message: str, code: str = "extraction_failed") -> None:
        super().__init__(message)
        self.code = code


class ExtractionClient(Protocol):
    def extract_terms(self, doc_name: str, pages: list[str], hint: str | None = None) -> ExtractedTerms: ...

    def extract_invoice(self, doc_name: str, pages: list[str], hint: str | None = None) -> ExtractedInvoice: ...
