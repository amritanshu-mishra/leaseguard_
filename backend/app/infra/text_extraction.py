"""Uploaded files to page text. Text-layer PDFs and TXT only; no OCR in this build."""

from __future__ import annotations

import hashlib
import io

from app.domain.quotes import normalise

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_UPLOAD_BYTES_ERROR = "file_too_large"


class UnsupportedFile(Exception):
    """The file type, contents or page count cannot be handled safely."""


def to_pages(filename: str, data: bytes, max_pages: int = 50) -> list[str]:
    """Extract one string per page, enforcing extension, magic bytes and page limits."""
    lower = filename.lower()
    if "." not in lower or lower.rsplit(".", 1)[1] not in ("pdf", "txt"):
        raise UnsupportedFile("Only PDF and TXT files are supported. Convert the file and try again.")
    if lower.endswith(".pdf"):
        if not data.lstrip()[:5] == b"%PDF-":
            raise UnsupportedFile("This file is not a valid PDF. Check the file and try again.")
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover
            raise UnsupportedFile("PDF reading is unavailable on the server.") from exc
        try:
            reader = PdfReader(io.BytesIO(data))
            if len(reader.pages) > max_pages:
                raise UnsupportedFile(f"PDF has more than {max_pages} pages. Upload a shorter extract.")
            pages = [(page.extract_text() or "") for page in reader.pages]
        except UnsupportedFile:
            raise
        except Exception as exc:
            raise UnsupportedFile("The PDF could not be opened. It may be damaged or encrypted.") from exc
        if not any(page.strip() for page in pages):
            raise UnsupportedFile("No text layer found. Scanned PDFs need OCR; use a text PDF or TXT file.")
        return pages
    text = data.decode("utf-8", errors="replace")
    pages = text.split("\f")
    if not any(page.strip() for page in pages):
        raise UnsupportedFile("The text file is empty.")
    if len(pages) > max_pages:
        raise UnsupportedFile(f"Text file has more than {max_pages} pages.")
    return pages


def fingerprint_pages(pages: list[str]) -> str:
    """Stable content hash used to match uploaded synthetic samples to fixtures."""
    canonical = "\n".join(normalise(page) for page in pages)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
