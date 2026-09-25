from typing import Literal

from pydantic import BaseModel, Field


class CompanySettings(BaseModel):
    name: str
    signatory_name: str = ""
    footer_address: str = ""
    phone: str = ""
    emails: str = ""
    gst_no: str = ""
    closing_line: str = ""
    system_generated_note: str = ""


class QuoteSeqSettings(BaseModel):
    prefix: str = Field(pattern=r"^[A-Za-z]{0,6}$")
    fy: str = Field(pattern=r"^\d{2}-\d{2}$")
    seq: int = Field(ge=0)


SETTING_MODELS = {
    "company": CompanySettings,
    "quote_seq": QuoteSeqSettings,
    "default_terms": list[str],
    "default_intro": str,
}


class SettingIn(BaseModel):
    value: object


class UserIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)
    role: Literal["admin", "user"] = "user"
