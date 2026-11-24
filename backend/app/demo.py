"""Labelled synthetic scenarios assembled from the bundled sample documents.

Each scenario is composed dynamically at request time and pushed through the
same upload/extraction/quote-gate pipeline as a real user file.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DocumentSpec:
    filename: str
    kind: str
    effective_date: date


@dataclass(frozen=True)
class Scenario:
    id: str
    label_en: str
    label_hi: str
    description_en: str
    description_hi: str
    expected_en: str
    expected_hi: str
    property_en: str
    property_hi: str
    start_date: date
    documents: tuple[DocumentSpec, ...]

    def as_dict(self) -> dict:
        expected = EXPECTED_RESULTS[self.id]
        return {
            "id": self.id,
            "label_en": self.label_en,
            "label_hi": self.label_hi,
            "description_en": self.description_en,
            "description_hi": self.description_hi,
            "expected_en": self.expected_en,
            "expected_hi": self.expected_hi,
            "expected_statuses": list(expected["statuses"]),
            "expected_reasons": list(expected["reasons"]),
            "documents": [doc.filename for doc in self.documents],
        }


LEASE = DocumentSpec("lease.txt", "lease", date(2025, 4, 1))
AMENDMENT = DocumentSpec("amendment1.txt", "amendment", date(2026, 1, 1))
INVOICE = DocumentSpec("invoice_apr2026.txt", "invoice", date(2026, 4, 1))

SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        id="amendment",
        label_en="Amendment controls",
        label_hi="संशोधन लागू",
        description_en="Lease says 10% escalation; a January amendment caps it at 5%. April's invoice still uses 10%.",
        description_hi="पट्टे में 10% वृद्धि, जनवरी के संशोधन में 5% की सीमा। अप्रैल के बिल में अब भी 10% लगाया गया।",
        expected_en="2 discrepancies · ₹3,200 excess",
        expected_hi="2 अंतर · ₹3,200 अतिरिक्त",
        property_en="Shop 12 · Amendment case",
        property_hi="दुकान 12 · संशोधन केस",
        start_date=date(2025, 4, 1),
        documents=(LEASE, AMENDMENT, INVOICE),
    ),
    Scenario(
        id="ambiguous",
        label_en="Unclear clause",
        label_hi="अस्पष्ट धारा",
        description_en="The escalation clause says only 'a reasonable increase'. The app must not invent a number.",
        description_hi="वृद्धि की धारा में केवल 'उचित वृद्धि' लिखा है। ऐप को संख्या नहीं बनानी चाहिए।",
        expected_en="1 unclear clause + ₹1,200 maintenance excess",
        expected_hi="1 अस्पष्ट धारा + ₹1,200 रखरखाव अतिरिक्त",
        property_en="Shop 12 · Unclear clause",
        property_hi="दुकान 12 · अस्पष्ट धारा",
        start_date=date(2025, 4, 1),
        documents=(
            DocumentSpec("lease_ambiguous.txt", "lease", date(2025, 4, 1)),
            INVOICE,
        ),
    ),
    Scenario(
        id="conflict",
        label_en="Conflicting amendments",
        label_hi="संशोधनों में मतभेद",
        description_en="Two amendments take effect on the same date with 5% and 7% caps. Both quotes are shown.",
        description_hi="एक ही तिथि से 5% और 7% के दो संशोधन। दोनों उद्धरण दिखाए जाते हैं।",
        expected_en="Conflict flagged + ₹1,200 maintenance excess",
        expected_hi="मतभेद flagged + ₹1,200 रखरखाव अतिरिक्त",
        property_en="Shop 12 · Conflicting amendments",
        property_hi="दुकान 12 · संशोधनों में मतभेद",
        start_date=date(2025, 4, 1),
        documents=(
            LEASE,
            DocumentSpec("amendment_5.txt", "amendment", date(2026, 1, 1)),
            DocumentSpec("amendment_7.txt", "amendment", date(2026, 1, 1)),
            INVOICE,
        ),
    ),
    Scenario(
        id="future",
        label_en="Amendment not yet due",
        label_hi="संशोधन अभी लागू नहीं",
        description_en="The 5% amendment starts in July. April's invoice correctly uses the lease rate of 10%.",
        description_hi="5% वाला संशोधन जुलाई से है। अप्रैल के बिल में 10% सही है।",
        expected_en="No discrepancy · future amendment ignored",
        expected_hi="कोई अंतर नहीं · भविष्य का संशोधन नहीं लगाया",
        property_en="Shop 12 · Future amendment",
        property_hi="दुकान 12 · भविष्य का संशोधन",
        start_date=date(2025, 4, 1),
        documents=(
            LEASE,
            DocumentSpec("amendment_late.txt", "amendment", date(2026, 7, 1)),
            DocumentSpec("invoice_apr2026_lease_rate.txt", "invoice", date(2026, 4, 1)),
        ),
    ),
    Scenario(
        id="missing-cap",
        label_en="Missing maintenance cap",
        label_hi="रखरखाव सीमा नहीं",
        description_en="No maintenance cap exists in the documents, so the billed amount cannot be judged.",
        description_hi="दस्तावेज़ों में रखरखाव की कोई सीमा नहीं है, इसलिए बिल की जाँच नहीं हो सकती।",
        expected_en="Uncertain · no amount invented",
        expected_hi="अनिश्चित · कोई राशि नहीं बनाई",
        property_en="Shop 12 · Missing cap",
        property_hi="दुकान 12 · सीमा नहीं",
        start_date=date(2025, 4, 1),
        documents=(
            DocumentSpec("lease_no_cap.txt", "lease", date(2025, 4, 1)),
            INVOICE,
        ),
    ),
    Scenario(
        id="clean",
        label_en="Clean invoice",
        label_hi="सही बिल",
        description_en="A 5% amendment and a matching invoice. The audit should find nothing to dispute.",
        description_hi="5% का संशोधन और उसी के अनुसार बिल। जाँच में कुछ नहीं मिलना चाहिए।",
        expected_en="No findings · invoice matches",
        expected_hi="कोई निष्कर्ष नहीं · बिल सही है",
        property_en="Shop 12 · Clean invoice",
        property_hi="दुकान 12 · सही बिल",
        start_date=date(2025, 4, 1),
        documents=(
            LEASE,
            AMENDMENT,
            DocumentSpec("invoice_apr2026_clean.txt", "invoice", date(2026, 4, 1)),
        ),
    ),
)

# Deterministic audit outcomes used by tests, the smoke script and the UI badge.
EXPECTED_RESULTS: dict[str, dict[str, list]] = {
    "amendment": {"statuses": ["confirmed", "confirmed"], "reasons": [None, None]},
    "ambiguous": {"statuses": ["uncertain", "confirmed"], "reasons": ["clause_ambiguous", None]},
    "conflict": {"statuses": ["uncertain", "confirmed"], "reasons": ["conflicting_terms", None]},
    "future": {"statuses": [], "reasons": []},
    "missing-cap": {"statuses": ["uncertain"], "reasons": ["term_not_found"]},
    "clean": {"statuses": [], "reasons": []},
}

SCENARIOS_BY_ID = {scenario.id: scenario for scenario in SCENARIOS}
DEFAULT_SCENARIO = "amendment"


def get_scenario(scenario_id: str) -> Scenario:
    return SCENARIOS_BY_ID.get(scenario_id, SCENARIOS_BY_ID[DEFAULT_SCENARIO])
