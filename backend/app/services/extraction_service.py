"""Turn model output into domain Terms and apply the quote-validation gate."""

from __future__ import annotations

from datetime import date

from app.domain.models import Invoice, Term, TermType
from app.domain.quotes import quote_in_text
from app.infra.llm_base import ExtractionClient


class ExtractionService:
    def __init__(self, client: ExtractionClient) -> None:
        self._client = client

    def terms_from_document(
        self, doc_name: str, effective_date: date, pages: list[str], hint: str | None = None
    ) -> list[Term]:
        raw = self._client.extract_terms(doc_name, pages, hint)
        terms: list[Term] = []
        for item in raw.terms:
            # The quote must be on the page the model cites, not merely somewhere
            # in the document: the page number is part of the evidence we show.
            cited_page = pages[item.page - 1] if 1 <= item.page <= len(pages) else ""
            grounded = quote_in_text(item.source_quote, cited_page)
            terms.append(
                Term(
                    term_type=TermType(item.term_type),
                    value=item.value,
                    source_quote=item.source_quote,
                    page=item.page,
                    document_name=doc_name,
                    effective_date=effective_date,
                    validated=grounded,
                    ambiguous=item.ambiguous or item.value is None,
                    confidence=item.confidence,
                )
            )
        return terms

    def invoice_from_document(self, doc_name: str, pages: list[str], hint: str | None = None) -> Invoice:
        raw = self._client.extract_invoice(doc_name, pages, hint)
        return Invoice(raw.period_start, raw.rent_paise, raw.maintenance_paise)
