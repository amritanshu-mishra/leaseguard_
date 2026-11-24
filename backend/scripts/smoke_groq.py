"""Run ONE live extraction against Groq to verify key, model and JSON mode.

From backend/: python -m scripts.smoke_groq
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import load_settings
from app.domain.quotes import quote_in_text
from app.infra.llm_base import ExtractionError
from app.infra.llm_groq import GroqExtractionClient


def main() -> None:
    settings = load_settings()
    if settings.provider != "groq" or not settings.api_key or not settings.model:
        raise SystemExit("Set EXTRACTION_PROVIDER=groq, LLM_API_KEY and EXTRACTION_MODEL in backend/.env first.")
    pages = Path("samples/lease.txt").read_text(encoding="utf-8").split("\f")
    try:
        result = GroqExtractionClient(settings.api_key, settings.model, settings.json_mode).extract_terms(
            "lease", pages
        )
    except ExtractionError as exc:
        raise SystemExit(f"FAILED: {exc}") from exc
    text = "\n".join(pages)
    for term in result.terms:
        state = "quote verified" if quote_in_text(term.source_quote, text) else "QUOTE NOT FOUND"
        print(f"{term.term_type:24} value={term.value} page={term.page} ambiguous={term.ambiguous} [{state}]")
    print("Expected: base rent 4000000, escalation 1000, maintenance cap 400000, all verified.")


if __name__ == "__main__":
    main()
