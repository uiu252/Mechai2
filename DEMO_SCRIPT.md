# Merch AI five-minute walkthrough

Start the app using `Launch Merch AI.cmd`. Keep Demo Mode selected. All demo actions are local decision-support actions; nothing purchases or orders products.

## 0:00 — Start with evidence and rules

Show the Assortment screen: 26 workbook products, 16 historical rows and 10 supplier candidates. Point out the separate Historical GM and Potential GM columns by scrolling the table horizontally. Open Product evidence to show a candidate's missing ratings and sell-through as Not available.

Say: “The workbook is normalized into one product table, but actuals and supplier estimates remain distinct. Python enforces exactly 16 facings, at most four online-only products, exclusive placements and all three categories.”

## 0:45 — Prove the constraint gate

Change LED Fog Machine from In Store to Removed and save. The facing count becomes 15/16. Open Executive synthesis to show that synthesis is blocked. Restore the workbook baseline from Data & demo scenarios.

## 1:15 — Compare three perspectives

Open Specialist review and load the demo perspectives. The label says Cached demo analysis, with provenance disclosed. Financial highlights Dragon purchase exposure and fog uncertainty; Customer and Merchandising compares ratings with sample sizes and price coverage; Operations and Channel emphasizes space and channel history.

Open a finding's evidence to show the product, exact metric and worksheet row.

Say: “These are prepared outputs for a reliable offline demonstration. Live mode uses one language model with three independent structured calls, followed by a separate synthesis call. We do not claim three different foundation models.”

## 2:15 — Show meaningful human disagreement

In the Financial tab, choose Modify and enter:

> Keep the 12 ft Reaper Inflatable for this review. Its 4.8 rating from 75 reviews supports retaining it while the Black Cat's supplier demand remains unproven. Do not apply the proposed replacement.

Save the review. Save Agree in the other two tabs. In Executive synthesis, click Synthesize recommendation.

Show that Financial's original Reaper-to-Black-Cat change is withheld. The exact comment appears in the conflict list and the reviewer disposition explains why no Financial placement change was included. The Customer review's compatible fog-to-pumpkin change remains proposed.

Say: “The human response changes the outcome. The system preserves the agent output and our response, explains the tradeoff, and checks the combined placement changes in code.”

## 3:15 — Let the merchant decide

Continue to Merchant decision. The final assortment still passes 16/16 facings, four online-only products and all three categories. Accept the recommendation, or demonstrate Override with an explicit rationale. Download the Markdown decision summary and JSON audit record. They preserve placements, validation, analyses, all human reviews, synthesis and merchant rationale.

To demonstrate Modify, switch the proposed Pumpkin Stack to Removed and Solar Pathway Ghosts to In Store, save the final placements, enter a rationale and click Finalize modified assortment. This one-facing exchange remains valid. These are rehearsal decisions, not an instruction to choose a particular assortment.

## 4:00 — Stress-test supplier upside

Load Dragon challenge in the sidebar and rerun the demo perspectives. It is labeled Rule-based offline analysis because placements changed. Financial cites $9.405 million supplier potential and a 45,000-unit mandatory purchase. Operations cites four of sixteen facings, or 25% of the aisle. This scenario removes the proven Skeleton and Reaper Inflatable to make room, making opportunity cost visible.

Load Bluetooth fog challenge. Financial compares the new candidate's $740,000 potential and 20,000 mandatory units with LED Fog Machine's $48,500 realized GM and 32% full-price sell-through. The upgrade does not prove demand.

## 4:45 — Close

Say: “Our team specializes in financial performance, customer merchandising and channel operations. Merch AI mirrors those perspectives, requires each specialist's review, and combines that judgment into an explainable recommendation. Code enforces the rules, and the merchant retains final authority.”

The live API route is implemented and adapter-tested; it needs an API key to demonstrate real model calls. The offline workflow requires no credentials or internet connection.
