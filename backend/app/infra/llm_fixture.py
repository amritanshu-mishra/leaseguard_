"""Pre-extracted results for tests and the demo fallback (no API key needed)."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import ExtractedInvoice, ExtractedTerms

from .llm_base import ExtractionError
from .text_extraction import fingerprint_pages, to_pages


class FixtureClient:
    """Match by content fingerprint first, filename second.

    Fingerprint matching means the demo works even when a judge renames the
    downloaded sample file or uploads the PDF version instead of the TXT.
    """

    def __init__(
        self,
        terms: dict[str, ExtractedTerms] | None = None,
        invoices: dict[str, ExtractedInvoice] | None = None,
        fingerprints: dict[str, str] | None = None,
        corpus_dir: Path | None = None,
    ) -> None:
        self._terms = terms or {}
        self._invoices = invoices or {}
        self._fingerprints = fingerprints or {}
        if corpus_dir and corpus_dir.exists():
            for path in corpus_dir.iterdir():
                if path.suffix.lower() not in {".txt", ".pdf"}:
                    continue
                try:
                    pages = to_pages(path.name, path.read_bytes(), max_pages=200)
                except Exception:
                    continue
                self._fingerprints[fingerprint_pages(pages)] = path.stem

    @classmethod
    def from_dir(cls, directory: Path, corpus_dir: Path | None = None) -> FixtureClient:
        terms: dict[str, ExtractedTerms] = {}
        invoices: dict[str, ExtractedInvoice] = {}
        for path in sorted(Path(directory).glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if "terms" in data:
                terms[path.stem] = ExtractedTerms.model_validate(data)
            elif "period_start" in data:
                invoices[path.stem] = ExtractedInvoice.model_validate(data)
        return cls(terms, invoices, corpus_dir=corpus_dir)

    def _key(self, doc_name: str, pages: list[str]) -> str:
        key = self._fingerprints.get(fingerprint_pages(pages))
        if key:
            return key
        # Only trust a filename when no corpus of known samples was registered
        # (e.g. a unit test built from an explicit fixture dictionary).
        if not self._fingerprints:
            return Path(doc_name).stem
        raise ExtractionError(
            "Demo mode recognises only the bundled synthetic samples. Add your Groq API key to read other documents.",
            "unsupported_sample",
        )

    def extract_terms(self, doc_name: str, pages: list[str], hint: str | None = None) -> ExtractedTerms:
        key = self._key(doc_name, pages)
        result = self._terms.get(key)
        if result is None:
            raise ExtractionError(
                "Demo mode recognises only the bundled synthetic samples. "
                "Add your Groq API key to read other documents.",
                "unsupported_sample",
            )
        return result

    def extract_invoice(self, doc_name: str, pages: list[str], hint: str | None = None) -> ExtractedInvoice:
        key = self._key(doc_name, pages)
        result = self._invoices.get(key)
        if result is None:
            raise ExtractionError(
                "Demo mode recognises only the bundled synthetic samples. "
                "Add your Groq API key to read other documents.",
                "unsupported_sample",
            )
        return result
