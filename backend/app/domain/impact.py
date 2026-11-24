"""Impact accounting. Estimates are labelled and never claim recovered money."""

from __future__ import annotations

from dataclasses import dataclass

# Transparent, illustrative planning figures - NOT measured outcomes.
MINUTES_PER_DOCUMENT = 3
MINUTES_PER_AUDIT = 5


@dataclass(frozen=True)
class Impact:
    excess_detected_paise: int
    awaiting_review_paise: int
    confirmed_count: int
    uncertain_count: int
    document_count: int
    audit_count: int
    estimated_minutes_saved: int

    def as_dict(self) -> dict:
        return {
            "excess_detected_paise": self.excess_detected_paise,
            "awaiting_review_paise": self.awaiting_review_paise,
            "confirmed_count": self.confirmed_count,
            "uncertain_count": self.uncertain_count,
            "document_count": self.document_count,
            "audit_count": self.audit_count,
            "estimated_minutes_saved": self.estimated_minutes_saved,
            "estimate_basis": (
                f"Estimate: {MINUTES_PER_DOCUMENT} min per document read + "
                f"{MINUTES_PER_AUDIT} min per audit reviewed. Illustrative, not measured."
            ),
            "disclaimer": "No money is recovered or sent by LeaseGuard. All figures are for review only.",
        }


def compute_impact(findings: list[dict], document_count: int, audit_count: int) -> Impact:
    """Aggregate findings rows carrying 'finding' and 'decision' keys."""
    confirmed = [r for r in findings if r["finding"].status.value == "confirmed"]
    uncertain = [r for r in findings if r["finding"].status.value == "uncertain"]
    excess = sum(r["finding"].difference_paise or 0 for r in confirmed)
    awaiting = sum(r["finding"].difference_paise or 0 for r in confirmed if r.get("decision") is None)
    return Impact(
        excess_detected_paise=excess,
        awaiting_review_paise=awaiting,
        confirmed_count=len(confirmed),
        uncertain_count=len(uncertain),
        document_count=document_count,
        audit_count=audit_count,
        estimated_minutes_saved=(document_count * MINUTES_PER_DOCUMENT + audit_count * MINUTES_PER_AUDIT),
    )
