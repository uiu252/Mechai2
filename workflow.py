"""Finalization and export require coherent snapshots and passing code-based rules."""
from datetime import datetime, timezone
import csv
import io
import json
from schemas import MerchantDecision, ROLES
from data_loader import fingerprint
from rules import validate_assortment, apply_changes, compare_placements
from agents import validate_reviews, validate_synthesis

def finalize(products, final_products, analyses, reviews, synthesis, decision,
             analysis_fingerprint, analysis_source, synthesis_source):
    if fingerprint(products) != analysis_fingerprint:
        raise ValueError('Analysis is stale. Run the perspectives again for this assortment.')
    if set(analyses) != set(ROLES): raise ValueError('All three analyses are required.')
    reviews = validate_reviews(reviews)
    validate_synthesis(synthesis, products, reviews)
    decision = MerchantDecision.model_validate(decision.model_dump() if hasattr(decision, 'model_dump') else decision)
    validation = validate_assortment(final_products)
    if not validation.valid: raise ValueError('Cannot finalize: ' + '; '.join(validation.errors))
    original = {p.item: p.model_dump(exclude={'placement'}) for p in products}
    final = {p.item: p.model_dump(exclude={'placement'}) for p in final_products}
    if original != final: raise ValueError('Finalization may change placements only, not product records.')
    proposed = apply_changes(products, synthesis.recommended_changes, require_valid=True)
    differences = compare_placements(proposed, final_products)
    if decision.decision == 'Accept' and differences:
        raise ValueError('Accept must match the synthesized assortment. Use Modify or Override.')
    if decision.decision == 'Modify' and not differences:
        raise ValueError('Modify must change at least one placement relative to synthesis.')
    return {
        'schema_version': 1, 'finalized_at': datetime.now(timezone.utc).isoformat(),
        'source': 'Student Data workbook', 'analysis_source': analysis_source,
        'synthesis_source': synthesis_source, 'analysis_fingerprint': analysis_fingerprint,
        'final_fingerprint': fingerprint(final_products),
        'reviewed_products': [p.model_dump() for p in products],
        'products': [p.model_dump() for p in final_products],
        'validation': {**validation.model_dump(), 'valid': validation.valid},
        'analyses': {role: a.model_dump() for role, a in analyses.items()},
        'human_reviews': [r.model_dump() for r in reviews],
        'synthesis': synthesis.model_dump(), 'merchant_decision': decision.model_dump(),
        'merchant_changes': [c.model_dump() for c in differences],
    }

def summary_markdown(record):
    v = record['validation']
    d = record['merchant_decision']
    lines = ['# Merch AI final assortment decision', '', f"Finalized: {record['finalized_at']}",
        f"Analysis: {record['analysis_source']}. Synthesis: {record['synthesis_source']}.", '',
        f"**Merchant decision: {d['decision']}**", d['rationale'] or 'Merchant accepted the recommendation.', '',
        f"**Validation: {v['total_facings']}/16 facings · {v['online_count']}/4 online-only items · All categories represented · Exclusive placements pass**", '',
        '## Executive rationale', record['synthesis']['executive_rationale'], '',
        '## Human review']
    for r in record['synthesis']['reviewer_responses']:
        lines.extend([f"- **{r['role']} — {r['decision']}**: {r['comment'] or 'No comment'}", f"  {r['disposition']}"])
    if record['merchant_changes']:
        lines.extend(['', '## Merchant changes relative to synthesis'])
        lines.extend(f"- {c['product']}: {c['from_placement']} → {c['to_placement']}" for c in record['merchant_changes'])
    lines.extend(['', '## Final placements', '', '| Product | Source | Placement | Aisle facings |', '|---|---|---|---:|'])
    for p in record['products']:
        name = p['item'].replace('|', '\\|').replace('\n', ' ')
        source = 'Historical actuals' if p['source_type'] == 'current' else 'Supplier estimate'
        facings = p['required_facings'] if p['placement'] == 'In Store' else 0
        lines.append(f"| {name} | {source} | {p['placement']} | {facings} |")
    lines.extend(['', '## Remaining risks', *['- ' + r for r in record['synthesis']['risks']], '',
                  record['synthesis']['confidence_note'], '',
                  'No purchases, orders or price changes have been executed.'])
    return '\n'.join(lines)

def placements_csv(record):
    stream = io.StringIO(newline='')
    fields = ['item', 'category', 'source_type', 'placement', 'required_facings', 'aisle_facings',
              'gross_margin_dollars', 'gross_margin_basis']
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for p in record['products']:
        row = {f: p.get(f) for f in fields}
        row['aisle_facings'] = p['required_facings'] if p['placement'] == 'In Store' else 0
        row['gross_margin_basis'] = 'Historical realized' if p['source_type'] == 'current' else 'Supplier full-price potential'
        # Prevent a source item name from becoming a spreadsheet formula in exported CSV.
        for k, value in row.items():
            if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r')): row[k] = "'" + value
        writer.writerow(row)
    return '\ufeff' + stream.getvalue()

def record_json(record):
    return json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False)
