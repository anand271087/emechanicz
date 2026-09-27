from fastapi import APIRouter, Depends

from app.deps import get_db, require_admin
from app.services import dashboard as svc

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"], dependencies=[Depends(require_admin)])


@router.get("")
def dashboard(period: svc.Period = "30d", db=Depends(get_db)):
    return svc.build(db, period)
