"""Money is integer paise everywhere. Floats are never used for amounts."""

from __future__ import annotations

from dataclasses import dataclass


def round_half_up_div(numerator: int, denominator: int) -> int:
    """Divide two non-negative integers, rounding half up."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (2 * numerator + denominator) // (2 * denominator)


def indian_group(n: int) -> str:
    """1250000 -> '12,50,000'."""
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) <= 3:
        return sign + s
    head, tail = s[:-3], s[-3:]
    parts: list[str] = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return sign + ",".join(parts + [tail])


@dataclass(frozen=True)
class Money:
    paise: int

    def __post_init__(self) -> None:
        if not isinstance(self.paise, int) or isinstance(self.paise, bool):
            raise TypeError("Money must be built from integer paise")

    @classmethod
    def from_rupees(cls, rupees: int) -> Money:
        return cls(rupees * 100)

    def apply_bp(self, basis_points: int) -> Money:
        """Increase by basis points (1000 = 10%), rounded half up to the paisa."""
        return Money(round_half_up_div(self.paise * (10_000 + basis_points), 10_000))

    def __sub__(self, other: Money) -> Money:
        return Money(self.paise - other.paise)

    def __gt__(self, other: Money) -> bool:
        return self.paise > other.paise

    def format(self) -> str:
        rupees, rem = divmod(abs(self.paise), 100)
        base = f"Rs. {indian_group(rupees)}"
        if rem:
            base += f".{rem:02d}"
        return f"-{base}" if self.paise < 0 else base
