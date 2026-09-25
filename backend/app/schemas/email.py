import re

from pydantic import BaseModel, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check(addresses: list[str]) -> list[str]:
    cleaned = [a.strip() for a in addresses if a.strip()]
    bad = [a for a in cleaned if not EMAIL_RE.match(a)]
    if bad:
        raise ValueError(f"Invalid email address: {', '.join(bad)}")
    return cleaned


class SendEmailIn(BaseModel):
    to: list[str]
    cc: list[str] = []
    subject: str
    body: str
    attach_docx: bool = False

    @field_validator("to")
    @classmethod
    def to_valid(cls, v: list[str]) -> list[str]:
        v = _check(v)
        if not v:
            raise ValueError("At least one recipient is required")
        return v

    @field_validator("cc")
    @classmethod
    def cc_valid(cls, v: list[str]) -> list[str]:
        return _check(v)
