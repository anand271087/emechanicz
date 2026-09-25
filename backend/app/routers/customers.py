from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user, get_db
from app.schemas.customer import CustomerIn

router = APIRouter(prefix="/api/v1/customers", tags=["customers"],
                   dependencies=[Depends(get_current_user)])


@router.get("")
def list_customers(search: str = "", db=Depends(get_db)):
    q = db.table("customers").select("*").order("company_name")
    if search:
        q = q.ilike("company_name", f"%{search}%")
    return q.execute().data


@router.post("", status_code=201)
def create_customer(body: CustomerIn, db=Depends(get_db)):
    return db.table("customers").insert(body.model_dump()).execute().data[0]


@router.put("/{cid}")
def update_customer(cid: str, body: CustomerIn, db=Depends(get_db)):
    rows = db.table("customers").update(body.model_dump()).eq("id", cid).execute().data
    if not rows:
        raise HTTPException(404, "Customer not found")
    return rows[0]


@router.delete("/{cid}", status_code=204)
def delete_customer(cid: str, db=Depends(get_db)):
    if db.table("quotes").select("id").eq("customer_id", cid).limit(1).execute().data:
        raise HTTPException(409, "Customer has quotations and cannot be deleted")
    db.table("customers").delete().eq("id", cid).execute()
