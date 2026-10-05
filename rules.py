"""Business constraints are enforced here, never by a language model."""
from schemas import Product, ValidationResult, CATEGORIES, PLACEMENTS, Change

def validate_assortment(products):
    rows = [p.model_dump() if isinstance(p, Product) else dict(p) for p in products]
    errors = []
    names = [r.get('item') for r in rows]
    unique = bool(rows) and all(isinstance(n, str) and n.strip() for n in names) and len(names) == len(set(n.casefold() for n in names if isinstance(n, str)))
    placements_valid = unique and all(r.get('placement') in PLACEMENTS for r in rows)
    if not placements_valid: errors.append('Each unique product must have exactly one valid placement.')
    data_valid = bool(rows)
    for r in rows:
        try: Product.model_validate(r)
        except Exception: data_valid = False
    if not data_valid: errors.append('Product data is invalid; facings must be positive whole numbers and metrics must be valid.')
    store = [r for r in rows if r.get('placement') == 'In Store']
    total = sum(r['required_facings'] for r in store if type(r.get('required_facings')) is int and r['required_facings'] > 0)
    online = sum(r.get('placement') == 'Online Only' for r in rows)
    cats = sorted({str(r.get('category')) for r in store})
    missing = sorted(set(CATEGORIES) - set(cats))
    if total != 16: errors.append(f'In-store capacity is {total} facings; exactly 16 are required.')
    if online > 4: errors.append(f'{online} online-only items selected; maximum is 4.')
    if missing: errors.append('Missing in-store categories: ' + ', '.join(missing) + '.')
    return ValidationResult(facings_valid=total == 16, online_valid=online <= 4,
        categories_valid=not missing, placement_valid=placements_valid, data_valid=data_valid,
        total_facings=total, online_count=online, categories=cats, missing_categories=missing, errors=errors)

def apply_changes(products, changes, require_valid=False):
    mapping = {p.item: p.model_copy(deep=True) for p in products}
    touched = set()
    for raw in changes:
        # Streamlit hot reload can leave session objects from an older model class.
        c = Change.model_validate(raw.model_dump() if hasattr(raw, 'model_dump') else raw)
        if c.product not in mapping: raise ValueError(f'Unknown product: {c.product}')
        if c.product in touched: raise ValueError(f'Duplicate or conflicting change: {c.product}')
        if mapping[c.product].placement != c.from_placement:
            raise ValueError(f'Stale starting placement for {c.product}.')
        if c.from_placement == c.to_placement: raise ValueError('Change must use a different placement.')
        mapping[c.product].placement = c.to_placement
        touched.add(c.product)
    result = list(mapping.values())
    if require_valid and not validate_assortment(result).valid:
        raise ValueError('Proposed changes fail deterministic validation: ' + '; '.join(validate_assortment(result).errors))
    return result

def compare_placements(before, after):
    original = {p.item: p.placement for p in before}
    if set(original) != {p.item for p in after}: raise ValueError('Product universe changed.')
    return [Change(product=p.item, from_placement=original[p.item], to_placement=p.placement,
                   reason='Merchant placement decision') for p in after if original[p.item] != p.placement]
