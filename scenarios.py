"""Rehearsal scenarios use actual workbook rows and validated placement changes."""
from rules import apply_changes
from schemas import Change

SCENARIOS = ('Workbook baseline', 'Dragon challenge', 'Bluetooth fog challenge')

def load_scenario(products, name):
    baseline = [p.model_copy(update={'placement': p.original_placement}, deep=True) for p in products]
    if name == 'Workbook baseline': return baseline
    by_name = {p.item: p for p in baseline}
    targets = {
        'Dragon challenge': {'12 ft Giant Skeleton': 'Removed', '12 ft Reaper Inflatable': 'Removed', '14 ft Giant Animated Dragon': 'In Store'},
        'Bluetooth fog challenge': {'LED Fog Machine': 'Removed', 'Fog Machine w/ Bluetooth Sound': 'In Store'},
    }.get(name)
    if targets is None: raise ValueError('Unknown scenario.')
    if not set(targets).issubset(by_name): raise ValueError('This rehearsal scenario requires the bundled case workbook.')
    return apply_changes(baseline, [Change(product=n, from_placement=by_name[n].placement,
        to_placement=t, reason=name) for n, t in targets.items()], require_valid=True)
