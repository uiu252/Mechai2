# Merch AI verification report

Verified on September 17, 2026. **52 tests passed** in the latest automated run (`52 passed in 11.52s`), including workbook-restricted live citation schemas. A separate browser walkthrough verified all four screens, a Financial Modify review, valid synthesis, merchant Override and all three export controls.

## Specification acceptance criteria

| ID | Result | Verified behavior |
|---|---|---|
| AC1 | Pass | Actual supplied workbook loads 16 current products and 10 candidates with correct source labels and row provenance. |
| AC2 | Pass | A 15-facing assortment fails; synthesis and finalization are blocked. |
| AC3 | Pass | The workbook baseline passes at exactly 16 facings. |
| AC4 | Pass | A fifth online-only item fails the four-item limit. |
| AC5 | Pass | Removing a required category fails category coverage. |
| AC6 | Pass | Three distinct Pydantic-validated perspectives contain exact source evidence. |
| AC7 | Pass | Modify/Disagree preserves the comment, withholds that agent's original change set, and explains the review's effect on synthesis. Explicit replacement requests are processed. |
| AC8 | Pass | Missing API key, timeout, refusal and malformed evidence paths remain compatible with the complete offline demo. |
| AC9 | Pass | Override requires a merchant rationale, stores it and revalidates the final assortment. |
| AC10 | Pass | Final summary includes all 26 unique products, one placement each, totals and passing validation. JSON includes both reviewed and final snapshots. |

## Additional checks

- Dragon challenge uses real workbook metrics: $9,405,000 supplier potential, 45,000 mandatory units, four facings and 25% aisle share. Scenario placements total 16 facings.
- Bluetooth fog challenge compares $740,000 potential and 20,000 mandatory units with $48,500 historical realized fog GM and 32% sell-through. Scenario placements total 16 facings.
- Missing metrics remain null/Not available and do not crash offline analysis; retail-price cents remain intact.
- Evidence references reject unknown products, unknown fields and values that differ from the source.
- Duplicate items, invalid placements, non-integer or negative facings, stale changes and stale snapshots are rejected.
- Reviewer comments are required for Modify/Disagree; all three unique roles are required for synthesis.
- Explicit conflicting reviewer requests are withheld rather than silently resolved in favor of one reviewer.
- Invalid combined proposals are withheld; deterministic rules cannot be overridden.
- Accept must match synthesis. Modify requires changed placements and a rationale. Product metrics cannot be changed during finalization.
- Cache fingerprints cover every normalized product field and placement. Edited assortments use labeled rule-based analysis, not stale cache output.
- OpenAI adapter tests verify independent perspective payloads, human feedback in synthesis, JSON schema request serialization, Pydantic parsing, refusal handling and API errors. SDK serialization/parsing uses a local HTTP mock with no external network request.
- Streamlit AppTest exercises the full human-disagreement/override workflow, missing-comment blocking, API-failure recovery, and invalidation of analyses after an assortment edit.
- Regression coverage handles session model objects surviving a Streamlit code reload.
- Currency paragraphs were visually verified after escaping Streamlit's LaTeX dollar delimiters.
- Desktop browser review checked metric labels, product grid, evidence text, tabs, reviewer controls, synthesis dispositions, merchant controls and export buttons.
- CSV exports escape formula-like product names. JSON serialization rejects non-finite values.
- Original and copied workbook SHA-256 hashes match: `1A5478B08BC965F93437CB8224534B406D4A75F651E3BF4369B0B06ECBA08A7E`.

## Verified runtime

| Component | Version |
|---|---|
| Python | 3.12.14 |
| Streamlit | 1.44.0 |
| Pandas | 2.2.3 |
| openpyxl | 3.1.5 |
| Pydantic | 2.13.5 |
| OpenAI SDK | 2.54.0 |

## Verification limits

Automated API tests use mocked responses. The user has reported failed live attempts; a successful live run with the latest citation fix has not yet been verified. Credentials, model availability, latency and reasoning quality require live verification. Passing a JSON schema or exact evidence-reference check does not guarantee the correctness of every natural-language inference; the required human review is retained.

The browser walkthrough was a rehearsal and does not represent the user's assortment approval. The handoff starts with the original workbook baseline. Session changes persist only within the browser session; final downloads provide durable records. Public hosting, production authentication and concurrent multi-user operation are outside this local MVP's scope.
