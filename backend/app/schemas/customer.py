from pydantic import BaseModel, field_validator


class CustomerIn(BaseModel):
    company_name: str
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    gst_no: str = ""

    @field_validator("company_name")
    @classmethod
    def name_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Company name is required")
        return v.strip()
