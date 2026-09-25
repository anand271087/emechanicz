from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class QuoteItemIn(BaseModel):
    sl_no: int
    description: str
    qty: float | None = Field(None, ge=0)
    unit_price: float | None = Field(None, ge=0)
    group_id: int | None = None

    @model_validator(mode="after")
    def qty_and_price_together(self):
        if (self.qty is None) != (self.unit_price is None):
            raise ValueError(f"Row {self.sl_no}: enter both qty and price, or neither")
        return self

    @property
    def priced(self) -> bool:
        return self.qty is not None


class QuoteIn(BaseModel):
    ref_no: str
    customer_id: str
    kind_attn: str = ""
    quote_date: date
    issue_status: str = "1.1"
    intro: str = ""
    terms: list[str] = []
    items: list[QuoteItemIn] = []

    @field_validator("ref_no")
    @classmethod
    def ref_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ref no is required")
        return v.strip()

    @model_validator(mode="after")
    def groups_valid(self):
        seen_closed: set[int] = set()
        prev = None
        for it in self.items:
            g = it.group_id
            if g is not None and g != prev and g in seen_closed:
                raise ValueError(f"Merged-price rows (group {g}) must be consecutive")
            if prev is not None and g != prev:
                seen_closed.add(prev)
            prev = g
        for g in {i.group_id for i in self.items if i.group_id is not None}:
            if sum(1 for i in self.items if i.group_id == g and i.priced) > 1:
                raise ValueError(f"Merged-price group {g} can have only one priced row")
        return self
