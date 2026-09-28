from datetime import date

from pydantic import BaseModel, field_validator

from app.schemas.quote import QuoteItemIn


class ImportSaveIn(BaseModel):
    customer_name: str
    kind_attn: str = ""
    ref_no: str
    quote_date: date
    issue_status: str = "1.1"
    intro: str = ""
    terms: list[str] = []
    items: list[QuoteItemIn] = []
    owner_id: str | None = None

    @field_validator("customer_name", "ref_no")
    @classmethod
    def required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field is required")
        return v.strip()
