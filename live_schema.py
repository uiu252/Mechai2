"""Constrain model citations to real workbook records; source values come from code."""
from functools import lru_cache
from typing import Literal
from pydantic import create_model, Field
from schemas import StrictModel, Placement, Perspective

@lru_cache(maxsize=16)
def workbook_schema(names, fields):
    ProductName = Literal.__getitem__(names)
    MetricName = Literal.__getitem__(fields)
    Reference = create_model('WorkbookReference', __base__=StrictModel,
        product=(ProductName, ...), field=(MetricName, ...))
    Finding = create_model('WorkbookFinding', __base__=StrictModel,
        claim=(str, ...), evidence=(list[Reference], Field(min_length=1)))
    Change = create_model('WorkbookChange', __base__=StrictModel,
        product=(ProductName, ...), from_placement=(Placement, ...),
        to_placement=(Placement, ...), reason=(str, Field(min_length=1)))
    return create_model('WorkbookPerspective', __base__=StrictModel,
        verdict=(Literal['support', 'support_with_changes', 'challenge'], ...),
        findings=(list[Finding], Field(min_length=3, max_length=5)),
        primary_risk=(str, ...), recommended_changes=(list[Change], ...))

def schema_for(products):
    if not products: raise ValueError('No workbook products available.')
    return workbook_schema(tuple(p.item for p in products), tuple(type(products[0]).model_fields))

def hydrate_perspective(parsed, products):
    """The model selects references; Python resolves values, including nulls, from source."""
    from agents import canonical
    records = {p.item: p for p in products}
    data = parsed.model_dump()
    for finding in data['findings']:
        for reference in finding['evidence']:
            reference['value'] = canonical(getattr(records[reference['product']], reference['field']))
    return Perspective.model_validate(data)
