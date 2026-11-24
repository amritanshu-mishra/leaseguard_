"""Set the Groq key locally without showing it in chat, shell history or logs.

Usage (from backend/): python -m scripts.set_groq_key
The key is read with hidden input and written only to backend/.env (chmod 600).
"""

from __future__ import annotations

import getpass
import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def upsert(lines: list[str], key: str, value: str) -> list[str]:
    """Replace or append one KEY=value entry, preserving unrelated lines."""
    prefix = f"{key}="
    for index, line in enumerate(lines):
        if line.strip().startswith(prefix):
            lines[index] = f"{prefix}{value}"
            break
    else:
        lines.append(f"{prefix}{value}")
    return lines


def main() -> None:
    api_key = getpass.getpass("Paste your Groq API key (input is hidden): ").strip()
    if not api_key:
        raise SystemExit("No key entered. Nothing was changed.")
    model = input("Paste a CURRENT model id from console.groq.com/docs/models: ").strip()
    if not model:
        raise SystemExit("No model id entered. Nothing was changed.")

    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    for key, value in (
        ("EXTRACTION_PROVIDER", "groq"),
        ("LLM_API_KEY", api_key),
        ("EXTRACTION_MODEL", model),
        ("EXTRACTION_JSON_MODE", "object"),
    ):
        lines = upsert(lines, key, value)
    ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    os.chmod(ENV_PATH, 0o600)

    print(f"Saved to {ENV_PATH}")
    print(f"Key: {api_key[:6]}…{api_key[-4:]} (hidden in file, never printed in full)")
    print("Restart the API, then run: python -m scripts.smoke_groq")


if __name__ == "__main__":
    main()
