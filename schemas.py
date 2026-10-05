"""Typed contracts shared by ingestion, deterministic rules and model outputs."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Placement = Literal['In Store', 'Online Only', 'Removed']
Role = Literal['Financial', 'Customer and Merchandising', 'Operations and Channel']
ROLES = ('Financial', 'Customer and Merchandising', 'Operations and Channel')
PLACEMENTS = ('In Store', 'Online Only', 'Removed')
CATEGORIES = ('Giants & Animatronics', 'Inflatables', 'Decor & Accessories')

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Product(StrictModel):
    item: str = Field(min_length=1)
    category: str
    required_facings: int = Field(gt=0, strict=True)
    retail_price: float | None = Field(default=None, ge=0)
    unit_cost: float | None = Field(default=None, ge=0)
    gross_margin_dollars: float | None = None
    gross_margin_rate: float | None = None
    full_price_sell_through: float | None = Field(default=None, ge=0, le=1)
    star_rating: float | None = Field(default=None, ge=0, le=5)
    reviews: int | None = Field(default=None, ge=0)
    mandatory_purchase_quantity: int | None = Field(default=None, ge=0)
    licensed: bool | None = None
    merchant_notes: str | None = None
    vendor_says: str | None = None
    source_type: Literal['current', 'new_candidate']
    source_row: int = Field(gt=0)
    placement: Placement = 'Removed'
    original_placement: Placement = 'Removed'
    units_bought: int | None = Field(default=None, ge=0)
    units_sold_full_price: int | None = Field(default=None, ge=0)
    units_sold_clearance: int | None = Field(default=None, ge=0)
    store_units: int | None = Field(default=None, ge=0)
    online_units: int | None = Field(default=None, ge=0)
    total_sales: float | None = None
    historical_gm_per_facing: float | None = None

    @model_validator(mode='after')
    def historical_integrity(self):
        if self.source_type == 'new_candidate' and any(getattr(self, k) is not None for k in
                ('full_price_sell_through', 'star_rating', 'reviews', 'units_bought',
                 'units_sold_full_price', 'units_sold_clearance', 'store_units', 'online_units',
                 'total_sales', 'historical_gm_per_facing')):
            raise ValueError('New candidates cannot contain historical results.')
        return self

class ValidationResult(StrictModel):
    facings_valid: bool
    online_valid: bool
    categories_valid: bool
    placement_valid: bool
    data_valid: bool
    total_facings: int
    online_count: int
    categories: list[str]
    missing_categories: list[str]
    errors: list[str]
    @property
    def valid(self):
        return all((self.facings_valid, self.online_valid, self.categories_valid,
                    self.placement_valid, self.data_valid))

class Evidence(StrictModel):
    product: str
    field: str
    value: str

class Finding(StrictModel):
    claim: str
    evidence: list[Evidence] = Field(min_length=1)

class Change(StrictModel):
    product: str
    from_placement: Placement
    to_placement: Placement
    reason: str = Field(min_length=1)

class Perspective(StrictModel):
    verdict: Literal['support', 'support_with_changes', 'challenge']
    findings: list[Finding] = Field(min_length=3, max_length=5)
    primary_risk: str
    recommended_changes: list[Change]

class Review(StrictModel):
    role: Role
    decision: Literal['Agree', 'Modify', 'Disagree']
    comment: str = ''
    requested_changes: list[Change] = Field(default_factory=list)
    @model_validator(mode='after')
    def needs_explanation(self):
        if self.decision != 'Agree' and not self.comment.strip():
            raise ValueError('Modify and Disagree require an explanation with evidence.')
        if self.decision == 'Agree' and self.requested_changes:
            raise ValueError('Use Modify or Disagree to request placement changes.')
        return self

class ReviewResponse(StrictModel):
    role: Role
    decision: Literal['Agree', 'Modify', 'Disagree']
    comment: str
    disposition: str

class Synthesis(StrictModel):
    agreements: list[str]
    conflicts: list[str]
    risks: list[str]
    recommended_changes: list[Change]
    reviewer_responses: list[ReviewResponse]
    executive_rationale: str
    confidence_note: str

class MerchantDecision(StrictModel):
    decision: Literal['Accept', 'Modify', 'Override']
    rationale: str = ''
    @model_validator(mode='after')
    def needs_rationale(self):
        if self.decision != 'Accept' and not self.rationale.strip():
            raise ValueError('Modify and Override require a merchant rationale.')
        return self
