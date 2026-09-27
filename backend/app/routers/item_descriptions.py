from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, field_validator

from app.deps import get_current_user, get_db
from app.services import item_descriptions as svc
from app.services.item_import import NOT_EXCEL, read_descriptions

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

router = APIRouter(prefix="/api/v1/item-descriptions", tags=["item descriptions"],
                   dependencies=[Depends(get_current_user)])


class DescriptionIn(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description can't be empty")
        return v


@router.get("")
def suggest(q: str = "", limit: int = Query(5, ge=1, le=1000), sort: str = "recent", db=Depends(get_db)):
    return svc.suggest(db, q, limit, sort)


@router.post("", status_code=201)
def add(body: DescriptionIn, db=Depends(get_db)):
    return svc.add(db, body.description)


@router.post("/import")
async def import_excel(file: UploadFile = File(...), db=Depends(get_db)):
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(400, NOT_EXCEL)
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "The file is larger than 5 MB. Split it into smaller files.")
    texts, blanks = read_descriptions(content)
    return svc.import_descriptions(db, texts, blanks)


@router.put("/{did}")
def rename(did: str, body: DescriptionIn, db=Depends(get_db)):
    return svc.rename(db, did, body.description)


@router.delete("/{did}", status_code=204)
def delete(did: str, db=Depends(get_db)):
    svc.delete(db, did)
