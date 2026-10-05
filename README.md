# Merch AI

A working local Streamlit MVP for the Halloween line-review case. It loads the actual supplied workbook, checks the assortment with deterministic Python, runs three independent specialist perspectives, records human review, synthesizes a recommendation, and lets the merchant Accept, Modify or Override a valid final assortment.

## Start on this computer

Double-click **Launch Merch AI.cmd**. It opens the app at http://127.0.0.1:8501. The launcher's terminal must remain open while you use the app. If the app is already running, the launcher opens it instead of starting another server.

The current delivery includes the original workbook at `data/Halloween_Line_Review_Case_Study_Data.xlsx`. No API key is needed for the full demo workflow. The initial assortment is the workbook's current-channel baseline, not an invented team recommendation.

## Portable setup

To move to another laptop, clone this repository or extract `Merch_AI_MVP.zip`. The workbook is included. On Windows, install Python (3.12 recommended), then double-click **Launch Merch AI.cmd**; first launch installs the dependencies and needs internet access. On macOS/Linux, use the commands below. Keep the terminal open while using the app.

For live analysis, select **Live AI** and enter your API key in the sidebar on the new laptop. Never commit a key to GitHub. The new laptop starts a new session: existing live results and reviews are not transferred. Download your decision records on the original laptop before moving. Demo Mode runs without an API key.

Keep the repository private if the included workbook is not intended for public release.

Requires Python 3.10 or newer. From this folder on Windows:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

## Demo workflow

1. **Assortment:** the workbook baseline starts with 16 in-store facings, four online-only products and all three required categories. Change Placement in the table and click **Save placements & validate**. Invalid assortments can be edited but cannot be synthesized or finalized.
2. **Specialist review:** keep **Demo Mode** selected and click **Load demo perspectives**. Financial, Customer and Merchandising, and Operations and Channel outputs each contain three to five evidence-backed findings, a risk, and proposed placement changes or No change.
3. Save a human decision in each tab. **Modify** and **Disagree** require comments. The optional placement table captures explicit reviewer change requests. In offline mode, comments are preserved verbatim, but free text is not interpreted as a placement instruction. Modify/Disagree withhold that agent's original change set; explicit replacement requests take its place.
4. **Executive synthesis:** combine all three analyses and reviews. Each review has an explicit disposition. Conflicting or invalid change sets are withheld and explained. Synthesis never silently changes the working assortment.
5. **Merchant decision:** the final editor starts from the synthesized placements. Save any edits, then choose **Accept recommendation**, **Finalize modified assortment**, or **Override recommendation**. Modify/Override require a rationale; Accept must match synthesis; Modify must actually change placements. Every finalization validates all rules again.
6. Download the Markdown decision summary, CSV final placements, and complete JSON audit record. Session state is local to the current browser session; the downloads are the durable record.

Changing the workbook or working assortment clears downstream results. Rerunning analyses clears old human reviews; changing a saved review clears synthesis and the final decision. This prevents stale analysis from being finalized.

## Rehearsal scenarios

Open **Data & demo scenarios** in the sidebar:

- **Workbook baseline:** original current-channel placements; 16 facings, four online items.
- **Dragon challenge:** removes the Giant Skeleton and Reaper Inflatable, then adds the Giant Animated Dragon, preserving 16 facings. This is a challenge scenario, not a recommended assortment. The analysis flags $9,405,000 supplier potential, 45,000 mandatory units and four facings (25% of the aisle).
- **Bluetooth fog challenge:** replaces the LED Fog Machine with Fog Machine w/ Bluetooth Sound, preserving 16 facings. The financial analysis compares $48,500 historical realized GM and 32% sell-through against $740,000 supplier potential and a 20,000-unit mandatory buy.

See `DEMO_SCRIPT.md` for a five-minute presentation walkthrough.

## Optional live AI

Set `OPENAI_API_KEY` in your environment before starting the app, or enter it in the sidebar's password field. It is not saved to exports or disk. Do not put credentials in the project or workbook.

```powershell
$env:OPENAI_API_KEY = 'your-key'
$env:OPENAI_MODEL = 'gpt-5-nano'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Choose **Live AI**, confirm the model ID available to your account, and run the perspectives. One model is used for three separate role-specific Responses API calls, in parallel, and a fourth separate synthesis call. Each request has a 180-second network timeout and no automatic retries. Duplicate run buttons are disabled during work. The live integration uses the [official structured-output pattern](https://developers.openai.com/api/docs/guides/structured-outputs) with Pydantic and `responses.parse`.

Structured outputs are schema-checked. Live specialists select product and field references restricted to the loaded workbook; Python fills in their source values. This prevents invented citation names, but does not verify every reasoning claim in natural-language prose; human review remains necessary. The synthesis is also checked for exact reviewer comments, known product names, current placements, and a jointly valid result. Invalid or refused responses are not applied. API failures display a warning and let you switch to Demo Mode.

**Verification boundary:** the SDK adapter, independent prompts, feedback payloads, refusal/error paths, and response validation were tested with mocked model responses. No paid live OpenAI response was used to establish the test result. A valid API key and account model access are required to exercise live calls.

## Truthful offline behavior

`fallback_outputs.json` contains prepared deterministic outputs for the exact bundled baseline assortment. The UI calls them **Cached demo analysis** and discloses that they are not prior live API responses. A fingerprint covers all product fields and placements. If data or placements change, cached outputs are not replayed: the app computes **Rule-based offline analysis** from the current data instead.

Offline synthesis is labeled **Rule-based demo synthesis**. It deterministically reconciles specialist recommendations, reviewer decisions and explicit requested changes. It does not claim natural-language interpretation or live AI reasoning. This makes the whole demo usable without an API while preserving honest provenance.

To deliberately rebuild the baseline fixture after changing the bundled source workbook:

```powershell
.\.venv\Scripts\python.exe build_demo_cache.py
```

## Workbook contract and data handling

- Reads the `Student Data` worksheet, detecting the two header rows instead of relying on fixed row offsets.
- Supports the source typo `Mandatory Purchase Quanity` as well as corrected `Mandatory Purchase Quantity`.
- Loads 16 current products and 10 candidates from the included workbook. Preserves worksheet row numbers for traceability.
- Current products contain historical actuals. Candidate gross margin and unit-margin rate are supplier estimates; candidate historical ratings, reviews and sell-through stay null.
- Missing values are displayed as Not available in product details and evidence. Blank numeric grid cells mean Not available; they are not zeros.
- Product names must be unique. Facings must be positive whole numbers. Every item has exactly one of In Store, Online Only or Removed.
- In-store facings must equal 16; Online Only count must be at most four. Giants & Animatronics, Inflatables, and Decor & Accessories must all have in-store representation.
- Online-only and removed products consume zero aisle facings. Required Facings remains a product attribute when changing channel.
- Unknown category labels remain visible, cannot satisfy a required category, and produce a source note.
- The source's sitcom-character note claims the same footprint as the Reaper, but numeric Required Facings are two versus one. The app flags this and uses the numeric column.
- Historical GM across channels divided by required facings is labeled a comparison proxy, never incremental or attributable store profit. Historical and potential GM are not summed into a forecast.
- Workbook formulas must have cached results saved by Excel. The app does not recalculate source formulas; missing numeric results stay unavailable, while missing required facings block loading.

The original source workbook is copied unchanged. No historical metrics are hardcoded into the loader. The rehearsal presets refer to exact product names; all displayed metrics come from the parsed workbook.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

The tests cover AC1–AC10, the two required product challenges, human disagreement, explicit modifications, conflicting feedback, stale state, missing data, bad uploads, exact evidence matching, mocked live API behavior, CSV safety, and Streamlit's complete UI workflow. `TEST_REPORT.md` records the delivered verification result.

## Files

| File | Responsibility |
|---|---|
| `app.py` | Streamlit workspace, forms, state invalidation and exports |
| `data_loader.py` | Workbook section detection, normalization and source provenance |
| `rules.py` | Deterministic constraints and atomic placement changes |
| `schemas.py` | Pydantic product, perspective, review, synthesis and decision contracts |
| `agents.py` | Three specialist roles, evidence checks, API adapter and offline synthesis |
| `workflow.py` | Finalization gates and presentation/audit exports |
| `scenarios.py` | Validated baseline, Dragon and Bluetooth fog rehearsal placements |
| `fallback_outputs.json` | Fingerprinted, prepared baseline demo analyses |
| `tests/` | Business-rule, ingestion, model-boundary and UI tests |

## Scope

This is the local, single-session MVP specified in the brief. There is no production authentication, multi-user synchronization, purchasing, inventory ordering, pricing changes, SharePoint integration, vector database, or cross-model validation. It runs on loopback and is not a public hosted service. Optional fonts may load from Google Fonts; the interface falls back to local sans-serif fonts offline. No workbook data is sent externally in Demo Mode. Live mode sends the workbook records and reviewer feedback to the configured OpenAI API for the requested analysis.

