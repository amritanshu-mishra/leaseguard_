# Synthetic data provenance

**Source.** All demo documents were authored from the *LeaseGuard Technical Design and UI/UX Specification* supplied with this task, specifically **Appendix C (Synthetic sample documents, p. 32)**, **§5.2 (worked example, p. 11)** and **§10.4 (golden cases, p. 26)**. Additional extractor-fixture values come from **§5.4 (extraction contract)** and the *Build Guide and Groq Change Addendum* §3–§5. No real lease, invoice, tenant record or personal data is included.

| File | Source | Key synthetic facts |
| --- | --- | --- |
| `lease.txt` / `.pdf` | Appendix C, §5.2 | Start 1 Apr 2025; rent ₹40,000/mo (cl. 2); 10% annual escalation (cl. 3); maintenance cap ₹4,000 (cl. 7); vague late-fee clause (cl. 9) |
| `amendment1.txt` / `.pdf` | §5.2, G1 | Effective 1 Jan 2026; escalation capped at 5% |
| `invoice_apr2026.txt` / `.pdf` | §5.2 | Period 1 Apr 2026; rent ₹44,000; maintenance ₹5,200 |
| `lease_ambiguous.txt` | G4 | Escalation "a reasonable increase in line with the market rate" → no amount computed |
| `amendment_5.txt`, `amendment_7.txt` | G5 | Two amendments with the same effective date, 5% and 7% → conflict |
| `amendment_late.txt` | G6 | Amendment effective 1 Jul 2026 → not in force for April 2026 |
| `lease_no_cap.txt` | U2 | No maintenance cap → uncertain, term_not_found |

Additional invoice variants: `invoice_apr2026_clean.txt` (rent ₹42,000, maintenance ₹3,800) and `invoice_apr2026_lease_rate.txt` (rent ₹44,000, maintenance ₹3,800) are derived from the same §5.2 worked example to demonstrate a clean invoice and an amendment-not-yet-effective case.

Expected results: G1 ₹2,000 excess; G2 ₹1,200 excess; G3 no findings; G4/G5 uncertain; G6 no finding; U1 unverifiable quote; U2 missing term. All are covered by `backend/tests/test_golden.py` and by `backend/tests/test_scenarios.py`, which loads every selectable scenario through the real API.

The six scenarios (`amendment`, `ambiguous`, `conflict`, `future`, `missing-cap`, `clean`) are declared in `backend/app/demo.py`. They are composed at request time from the documents above; nothing is hard-coded into the frontend. The catalogue includes bilingual labels, descriptions, expected outcomes and machine-checkable expected statuses.

Every document is stamped **"SYNTHETIC SAMPLE — Not a real agreement"** and the UI shows a synthetic-data banner on every screen. PDF twins are generated from the same TXT by `python -m scripts.build_samples`, so the fixture provider's content fingerprint matches either format.

Evidence-status note from the problem statement: claims about the frequency of tenant overpayment are **unverified hypotheses**. This demo demonstrates a workflow, not a prevalence finding. The impact numbers are computed from the synthetic case and labelled as review-only estimates — never as recovered money.
