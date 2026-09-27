from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator

from app.deps import get_current_user, get_db
from app.services import item_descriptions as svc

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
def suggest(q: str = "", limit: int = Query(5, ge=1, le=200), db=Depends(get_db)):
    return svc.suggest(db, q, limit)


@router.put("/{did}")
def rename(did: str, body: DescriptionIn, db=Depends(get_db)):
    return svc.rename(db, did, body.description)


@router.delete("/{did}", status_code=204)
def delete(did: str, db=Depends(get_db)):
    svc.delete(db, did)
