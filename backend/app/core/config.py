"""Environment-backed settings. Secrets are never stored in source code."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # optional during minimal installs; the loader below is a fallback
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - requirements always install dotenv

    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


BACKEND_DIR = Path(__file__).resolve().parents[2]
SAMPLES_DIR = BACKEND_DIR / "samples"


@dataclass(frozen=True)
class Settings:
    provider: str  # "groq" or "fixtures"
    api_key: str
    model: str
    json_mode: str  # "schema" or "object"
    allowed_origins: list[str]
    max_upload_mb: int
    max_pages: int

    @property
    def is_live(self) -> bool:
        return self.provider.lower() == "groq" and bool(self.api_key)


def load_settings(env: dict[str, str] | None = None, dotenv_path: Path | None = None) -> Settings:
    """Load settings from the environment, including backend/.env when present."""
    load_dotenv(dotenv_path or BACKEND_DIR / ".env", override=False)
    source = os.environ if env is None else env
    return Settings(
        provider=source.get("EXTRACTION_PROVIDER", "fixtures").strip().lower(),
        api_key=source.get("LLM_API_KEY", "").strip(),
        model=source.get("EXTRACTION_MODEL", "").strip(),
        json_mode=source.get("EXTRACTION_JSON_MODE", "object").strip().lower(),
        allowed_origins=[
            o.strip() for o in source.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()
        ],
        max_upload_mb=int(source.get("MAX_UPLOAD_MB", "10")),
        max_pages=int(source.get("MAX_PAGES", "50")),
    )
