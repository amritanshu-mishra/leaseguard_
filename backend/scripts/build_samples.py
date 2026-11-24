"""Generate text-layer PDF twins of the synthetic TXT fixtures.

Run from backend/: python -m scripts.build_samples
The PDFs are generated from exactly the same text as the TXT fixtures so the
content fingerprint in the fixture provider matches both formats.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def main() -> None:
    for source in sorted(SAMPLES.glob("*.txt")):
        target = source.with_suffix(".pdf")
        c = canvas.Canvas(str(target), pagesize=A4)
        _width, height = A4
        for _page_number, page in enumerate(source.read_text(encoding="utf-8").split("\f"), 1):
            y = height - 60
            for line in page.splitlines():
                for wrapped in textwrap.wrap(line, width=95) or [""]:
                    if wrapped.strip():
                        c.setFont("Helvetica", 10)
                        c.drawString(50, y, wrapped)
                        y -= 16
            c.showPage()
        c.save()
        print(f"wrote {target.name}")


if __name__ == "__main__":
    main()
