from datetime import date

from fastapi import APIRouter, Depends, Query

from app.deps import CurrentUser, get_current_user, get_db
from app.schemas.quote import QuoteIn
from app.services import quotes as svc
from app.services.amount_words import amount_in_words

router = APIRouter(prefix="/api/v1/quotes", tags=["quotes"],
                   dependencies=[Depends(get_current_user)])


@router.get("/next-ref")
def next_ref(on: date | None = Query(None, alias="date"), db=Depends(get_db)):
    return {"ref_no": svc.suggest_ref(db, on)}


@router.get("/amount-words")
def words(amount: float):
    return {"words": amount_in_words(amount)}


@router.get("")
def list_quotes(search: str = "", status: str = "", db=Depends(get_db)):
    return svc.list_quotes(db, search, status)


@router.post("", status_code=201)
def create_quote(body: QuoteIn, db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    return svc.create_quote(db, body, user.id)


@router.get("/{qid}")
def get_quote(qid: str, db=Depends(get_db)):
    return svc.fetch_quote(db, qid)


@router.put("/{qid}")
def update_quote(qid: str, body: QuoteIn, db=Depends(get_db)):
    return svc.update_quote(db, qid, body)


@router.delete("/{qid}", status_code=204)
def delete_quote(qid: str, db=Depends(get_db)):
    svc.delete_quote(db, qid)


@router.post("/{qid}/duplicate", status_code=201)
def duplicate_quote(qid: str, db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    return svc.duplicate_quote(db, qid, user.id)
