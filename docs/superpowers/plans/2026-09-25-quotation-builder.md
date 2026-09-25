# eMechanicz Quotation Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A responsive web app where the eMechanicz team logs in, builds quotations matching their existing format, downloads them as PDF/DOCX, and emails them to customers.

**Architecture:** React (Vite+TS) SPA authenticates against Supabase Auth and calls a FastAPI backend with the Supabase JWT; the backend verifies tokens via the project JWKS (ES256), owns all Postgres access through supabase-py with the service-role key, renders PDFs from an HTML template with WeasyPrint, builds DOCX with python-docx, and sends mail over SMTP.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, supabase-py, PyJWT[crypto], WeasyPrint, python-docx, Jinja2, pytest; React 18, Vite, TypeScript, Tailwind CSS, @supabase/supabase-js, react-router-dom.

**Spec:** `docs/superpowers/specs/2026-09-25-quotation-builder-design.md`

## Global Constraints

- Backend env comes ONLY from `backend/.env` (already exists, git-ignored): `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SMTP_*`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
- Frontend env from `frontend/.env`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`.
- Supabase project URL: `https://rtdesrjmyapfgxrownur.supabase.co`. JWTs are ES256 signed; verify via `<SUPABASE_URL>/auth/v1/.well-known/jwks.json`. Never verify with a shared secret.
- All API routes live under `/api/v1`. All money values are numeric(12,2) INR.
- Ref no format: `ETS/<prefix><seq>/<fy>` e.g. `ETS/P302/26-27`; FY is April–March.
- Company constants (footer, GST no) live in `app_settings`, not hardcoded in templates.
- Commit after every task with a `feat:`/`test:`/`chore:` message ending in the Co-Authored-By line from the session reminder.
- WeasyPrint on macOS needs system libs: `brew install pango` (document in README; if brew install fails, PDF tests may be skipped with `pytest -m "not pdf"`).

## Review Focus

1. Amounts ≥ 1 crore and decimal paise → `amount_in_words` must use crore wording and round to whole rupees (test in Task 3).
2. Quote dated 31-Mar vs 1-Apr → FY string and sequence reset must roll over (test in Task 4).
3. Manually edited ref no colliding with an existing quote → API returns 409 with `suggested_ref`, not a 500 (test in Task 7).
4. Label-only item rows (qty/price null, e.g. "Documentation & Training") → excluded from subtotal, rendered as blank cells (never "None") in PDF/DOCX (tests in Tasks 7, 8, 9).
5. SMTP failure while sending → quote stays `draft`, response is 502 with error detail, retry works (test in Task 10).

---

### Task 1: Backend scaffold, config, health endpoint

**Files:**
- Create: `backend/requirements.txt`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/main.py`, `backend/.env.example`, `backend/tests/__init__.py`, `backend/tests/test_health.py`, `backend/pytest.ini`

**Interfaces:**
- Produces: `app.config.settings` (pydantic-settings object with fields `supabase_url, supabase_anon_key, supabase_service_role_key, smtp_host, smtp_port, smtp_user, smtp_password, smtp_from, admin_email, admin_password`), FastAPI app factory `app.main:app` with CORS enabled.

- [ ] **Step 1: Create requirements and install**

`backend/requirements.txt`:
```
fastapi==0.115.*
uvicorn[standard]==0.30.*
pydantic-settings==2.*
supabase==2.*
PyJWT[crypto]==2.*
weasyprint==62.*
python-docx==1.*
jinja2==3.*
python-multipart==0.0.*
num2words==0.5.*
pytest==8.*
httpx==0.27.*
```
Run: `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`

- [ ] **Step 2: Write failing health test**

`backend/tests/test_health.py`:
```python
from fastapi.testclient import TestClient
from app.main import app

def test_health():
    client = TestClient(app)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```
`backend/pytest.ini`:
```ini
[pytest]
pythonpath = .
markers =
    pdf: needs weasyprint system libs
    integration: hits live Supabase
```
Run: `cd backend && .venv/bin/pytest tests/test_health.py -v` — Expected: FAIL (no app module).

- [ ] **Step 3: Implement config and app**

`backend/app/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    admin_email: str = "admin@emechanicz.com"
    admin_password: str = ""

settings = Settings()
```
`backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="eMechanicz CRM API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
```
`backend/.env.example`: same keys as `.env` with blank values.

- [ ] **Step 4: Run test — PASS.** `cd backend && .venv/bin/pytest -v`
- [ ] **Step 5: Commit** `git add backend && git commit -m "feat: backend scaffold with health endpoint"`

---

### Task 2: Database schema migration

**Files:**
- Create: `supabase/migrations/001_initial_schema.sql`, `backend/scripts/apply_migration.py`

**Interfaces:**
- Produces: tables `customers`, `quotes`, `quote_items`, `app_settings` in Supabase.

- [ ] **Step 1: Write migration SQL**

`supabase/migrations/001_initial_schema.sql`:
```sql
create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  company_name text not null,
  contact_person text default '',
  email text default '',
  phone text default '',
  address text default '',
  gst_no text default '',
  created_at timestamptz default now()
);

create table if not exists quotes (
  id uuid primary key default gen_random_uuid(),
  ref_no text not null unique,
  customer_id uuid references customers(id),
  quote_date date not null default current_date,
  issue_status text not null default '1.1',
  status text not null default 'draft' check (status in ('draft','sent')),
  subtotal numeric(14,2) not null default 0,
  amount_in_words text not null default '',
  terms jsonb not null default '[]',
  created_by uuid,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists quote_items (
  id uuid primary key default gen_random_uuid(),
  quote_id uuid not null references quotes(id) on delete cascade,
  sl_no int not null,
  description text not null,
  qty numeric(10,2),
  unit_price numeric(14,2),
  total numeric(14,2),
  group_id int
);

create table if not exists app_settings (
  key text primary key,
  value jsonb not null
);

alter table customers enable row level security;
alter table quotes enable row level security;
alter table quote_items enable row level security;
alter table app_settings enable row level security;

insert into app_settings (key, value) values
 ('company', '{"name":"Emechanicz Test Solutions Pvt Ltd","order_address":"No.190/3, Kalkere Village, Horamavu Post, Bangalore 560016","footer_address":"1st Floor, 1st Cross Adj to SBI ATM, Kodanda Rama Reddy Lyt, Ramamurthy Nagar, Bengaluru – 560016","gst_no":"29AADCE7362F1ZI","phone":"+91 9844561185, 9980592929","emails":"Sales@emechanicz.com ; Info@emechanicz.com"}'),
 ('quote_seq', '{"prefix":"P","fy":"26-27","seq":301}'),
 ('default_terms', '["Delivery: 3-4 Weeks from the date of PO & Confirmation","Payment Terms: Net 30 Days","Carriage: Delivery to - Customer site","Mode of Payment: Through ECS Transfer/Cheque","Order to be placed on: Emechanicz Test Solutions Pvt Ltd, No.190/3, Kalkere Village, Horamavu Post, Bangalore 560016","GST @ 18% or actuals extra (GST No. : 29AADCE7362F1ZI)","Validity of quotation: 30 Days from the date of proposal."]')
on conflict (key) do nothing;
```
(RLS enabled with no policies = anon key cannot touch data; service-role bypasses RLS. That is the intended lockdown.)

- [ ] **Step 2: Apply it.** Supabase's SQL can't be run via supabase-py directly; instruct the human (or use the dashboard SQL editor). `backend/scripts/apply_migration.py` prints the SQL and instructions:
```python
"""Prints migration SQL. Paste into Supabase Dashboard > SQL Editor > Run."""
from pathlib import Path
print(Path(__file__).parents[2].joinpath("supabase/migrations/001_initial_schema.sql").read_text())
```
Executor: run the SQL via the Supabase SQL editor if the human is available, otherwise via `postgrest` is not possible — use the Supabase Management API is out of scope; ASK the human to paste it, or use `psql` if a direct DB connection string is provided.

- [ ] **Step 3: Verify tables exist** (integration check):
```python
# backend/tests/test_schema_integration.py
import pytest
from supabase import create_client
from app.config import settings

@pytest.mark.integration
def test_tables_exist():
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
    for t in ["customers", "quotes", "quote_items", "app_settings"]:
        sb.table(t).select("*").limit(1).execute()  # raises if missing
```
Run: `cd backend && .venv/bin/pytest -m integration -v` — Expected: PASS after migration applied.

- [ ] **Step 4: Commit** `git add supabase backend && git commit -m "feat: initial database schema"`

---

### Task 3: Amount-in-words converter (Indian system)

**Files:**
- Create: `backend/app/services/__init__.py`, `backend/app/services/amount_words.py`, `backend/tests/test_amount_words.py`

**Interfaces:**
- Produces: `amount_in_words(amount: float | Decimal) -> str`, e.g. `2138000 -> "INR Twenty One Lakh Thirty Eight Thousand Only"`.

- [ ] **Step 1: Write failing tests**

```python
from app.services.amount_words import amount_in_words

def test_lakh():
    assert amount_in_words(1654200) == "INR Sixteen Lakh Fifty Four Thousand Two Hundred Only"

def test_thousand():
    assert amount_in_words(75200) == "INR Seventy Five Thousand Two Hundred Only"

def test_crore():
    assert amount_in_words(12345678) == "INR One Crore Twenty Three Lakh Forty Five Thousand Six Hundred Seventy Eight Only"

def test_rounds_paise():
    assert amount_in_words(100.49) == "INR One Hundred Only"

def test_zero():
    assert amount_in_words(0) == "INR Zero Only"
```
Run: `.venv/bin/pytest tests/test_amount_words.py -v` — FAIL (module missing).

- [ ] **Step 2: Implement** using `num2words` with `lang="en_IN"`, title-cased, "and"/commas/hyphens stripped:
```python
from decimal import Decimal, ROUND_HALF_UP
from num2words import num2words

def amount_in_words(amount) -> str:
    n = int(Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    words = num2words(n, lang="en_IN")
    words = words.replace(" and ", " ").replace(",", "").replace("-", " ")
    return f"INR {words.title()} Only"
```

- [ ] **Step 3: Run tests — PASS** (adjust replacements if num2words output differs; the tests are the contract).
- [ ] **Step 4: Commit** `git commit -am "feat: Indian amount-in-words converter"`

---

### Task 4: Ref number service (FY logic)

**Files:**
- Create: `backend/app/services/ref_no.py`, `backend/tests/test_ref_no.py`

**Interfaces:**
- Produces: `financial_year(d: date) -> str` (`"26-27"`), `format_ref(prefix: str, seq: int, fy: str) -> str`, `next_ref_state(state: dict, today: date) -> tuple[str, dict]` — pure function taking the `quote_seq` settings dict, returning (ref string for seq+1, updated state). FY mismatch resets seq to 1.

- [ ] **Step 1: Failing tests**
```python
from datetime import date
from app.services.ref_no import financial_year, next_ref_state

def test_fy_april_onward():
    assert financial_year(date(2026, 9, 1)) == "26-27"

def test_fy_jan_march():
    assert financial_year(date(2027, 3, 31)) == "26-27"
    assert financial_year(date(2027, 4, 1)) == "27-28"

def test_next_ref_increments():
    ref, state = next_ref_state({"prefix": "P", "fy": "26-27", "seq": 301}, date(2026, 9, 25))
    assert ref == "ETS/P302/26-27" and state["seq"] == 302

def test_next_ref_fy_rollover_resets():
    ref, state = next_ref_state({"prefix": "P", "fy": "26-27", "seq": 301}, date(2027, 4, 1))
    assert ref == "ETS/P1/27-28" and state == {"prefix": "P", "fy": "27-28", "seq": 1}
```

- [ ] **Step 2: Implement**
```python
from datetime import date

def financial_year(d: date) -> str:
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start % 100:02d}-{(start + 1) % 100:02d}"

def format_ref(prefix: str, seq: int, fy: str) -> str:
    return f"ETS/{prefix}{seq}/{fy}"

def next_ref_state(state: dict, today: date):
    fy = financial_year(today)
    seq = state["seq"] + 1 if state.get("fy") == fy else 1
    new = {"prefix": state.get("prefix", "P"), "fy": fy, "seq": seq}
    return format_ref(new["prefix"], seq, fy), new
```

- [ ] **Step 3: Run — PASS.**  **Step 4: Commit** `git commit -am "feat: quote ref number generator with FY rollover"`

---

### Task 5: Supabase client + auth dependency (JWKS ES256)

**Files:**
- Create: `backend/app/deps.py`, `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `get_db()` → cached supabase client (service role); `CurrentUser` pydantic model (`id: str, email: str, role: str`); `get_current_user(authorization: str = Header(...)) -> CurrentUser` FastAPI dependency; `require_admin(user=Depends(get_current_user))`.

- [ ] **Step 1: Failing tests** (unit-test the token path by monkeypatching the JWKS client; no live call):
```python
import jwt, time
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from app import deps
from app.main import app

KEY = ec.generate_private_key(ec.SECP256R1())

def make_token(role="user"):
    return jwt.encode(
        {"sub": "u1", "email": "a@b.c", "exp": time.time() + 600,
         "aud": "authenticated", "app_metadata": {"role": role}},
        KEY, algorithm="ES256")

def test_valid_token(monkeypatch):
    monkeypatch.setattr(deps, "_signing_key", lambda token: KEY.public_key())
    user = deps.decode_user(make_token("admin"))
    assert user.email == "a@b.c" and user.role == "admin"

def test_missing_header_rejected():
    client = TestClient(app)
    r = client.get("/api/v1/customers")
    assert r.status_code in (401, 403, 404)  # 404 until Task 6 adds the route
```

- [ ] **Step 2: Implement `backend/app/deps.py`**
```python
from functools import lru_cache
import jwt
from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from app.config import settings

class CurrentUser(BaseModel):
    id: str
    email: str = ""
    role: str = "user"

@lru_cache
def get_db() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

@lru_cache
def _jwks_client():
    return jwt.PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")

def _signing_key(token: str):
    return _jwks_client().get_signing_key_from_jwt(token).key

def decode_user(token: str) -> CurrentUser:
    try:
        claims = jwt.decode(token, _signing_key(token), algorithms=["ES256"],
                            audience="authenticated")
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Invalid token: {e}")
    return CurrentUser(id=claims["sub"], email=claims.get("email", ""),
                       role=(claims.get("app_metadata") or {}).get("role", "user"))

def get_current_user(authorization: str = Header("")) -> CurrentUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    return decode_user(authorization.removeprefix("Bearer "))

def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    return user
```

- [ ] **Step 3: Run — PASS.**  **Step 4: Commit** `git commit -am "feat: supabase client and JWKS auth dependency"`

---

### Task 6: Customers CRUD API

**Files:**
- Create: `backend/app/routers/__init__.py`, `backend/app/routers/customers.py`, `backend/tests/test_customers.py`
- Modify: `backend/app/main.py` (include router)

**Interfaces:**
- Consumes: `get_db`, `get_current_user` from Task 5.
- Produces: REST under `/api/v1/customers` — GET list (`?search=`), POST, PUT `/{id}`, DELETE `/{id}`. Pydantic `CustomerIn(company_name, contact_person, email, phone, address, gst_no)`.

- [ ] **Step 1: Failing tests** — override dependencies with fakes:
```python
from fastapi.testclient import TestClient
from app.main import app
from app import deps

class FakeTable:
    def __init__(self, store): self.store = store; self._f = None
    def select(self, *_): return self
    def ilike(self, *_): return self
    def order(self, *_ , **__): return self
    def insert(self, row): self.store.append({**row, "id": "c1"}); return self
    def update(self, row): self._f = row; return self
    def eq(self, k, v):
        if self._f: [r.update(self._f) for r in self.store if r["id"] == v]
        return self
    def delete(self): self.store.clear(); return self
    def execute(self): return type("R", (), {"data": self.store})

class FakeDB:
    def __init__(self): self.customers = []
    def table(self, name): return FakeTable(self.customers)

def client():
    db = FakeDB()
    app.dependency_overrides[deps.get_db] = lambda: db
    app.dependency_overrides[deps.get_current_user] = lambda: deps.CurrentUser(id="u1")
    return TestClient(app)

def test_create_and_list():
    c = client()
    r = c.post("/api/v1/customers", json={"company_name": "Yale Electronics"})
    assert r.status_code == 201
    assert c.get("/api/v1/customers").json()[0]["company_name"] == "Yale Electronics"
```

- [ ] **Step 2: Implement `customers.py`**
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.deps import get_db, get_current_user

router = APIRouter(prefix="/api/v1/customers", tags=["customers"],
                   dependencies=[Depends(get_current_user)])

class CustomerIn(BaseModel):
    company_name: str
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    gst_no: str = ""

@router.get("")
def list_customers(search: str = "", db=Depends(get_db)):
    q = db.table("customers").select("*").order("company_name")
    if search:
        q = q.ilike("company_name", f"%{search}%")
    return q.execute().data

@router.post("", status_code=201)
def create_customer(c: CustomerIn, db=Depends(get_db)):
    return db.table("customers").insert(c.model_dump()).execute().data[0]

@router.put("/{cid}")
def update_customer(cid: str, c: CustomerIn, db=Depends(get_db)):
    return db.table("customers").update(c.model_dump()).eq("id", cid).execute().data

@router.delete("/{cid}", status_code=204)
def delete_customer(cid: str, db=Depends(get_db)):
    db.table("customers").delete().eq("id", cid).execute()
```
In `main.py` add: `from app.routers import customers` … `app.include_router(customers.router)`.

- [ ] **Step 3: Run — PASS.**  **Step 4: Commit** `git commit -am "feat: customers CRUD API"`

---

### Task 7: Quotes API (CRUD, items, totals, next-ref, duplicate)

**Files:**
- Create: `backend/app/routers/quotes.py`, `backend/app/services/quote_logic.py`, `backend/tests/test_quote_logic.py`, `backend/tests/test_quotes_api.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: Tasks 3–5 (`amount_in_words`, `next_ref_state`, deps).
- Produces:
  - `QuoteItemIn(sl_no: int, description: str, qty: float|None, unit_price: float|None, group_id: int|None)`
  - `QuoteIn(ref_no: str, customer_id: str, quote_date: date, issue_status: str, terms: list[str], items: list[QuoteItemIn])`
  - `compute_totals(items: list[QuoteItemIn]) -> tuple[list[dict], Decimal]` — fills `total = qty*unit_price` (None when either is None; a group's price counts once), returns items + subtotal.
  - Routes: `GET /api/v1/quotes` (`?search=&status=`), `GET /{id}` (joined items+customer), `POST`, `PUT /{id}`, `DELETE /{id}`, `GET /next-ref`, `POST /{id}/duplicate`.
  - POST/PUT recompute subtotal + amount_in_words server-side; ref collision → 409 `{"detail": "...", "suggested_ref": "..."}`. `GET /next-ref` reads `quote_seq` from app_settings, POST bumps it when the created ref matches the suggestion.

- [ ] **Step 1: Failing unit tests for `compute_totals`**
```python
from app.services.quote_logic import compute_totals
from app.routers.quotes import QuoteItemIn

def test_totals_basic():
    items, subtotal = compute_totals([
        QuoteItemIn(sl_no=1, description="Rack", qty=2, unit_price=100.0),
    ])
    assert items[0]["total"] == 200.0 and subtotal == 200.0

def test_label_only_rows_ignored():
    items, subtotal = compute_totals([
        QuoteItemIn(sl_no=1, description="PC", qty=1, unit_price=500.0),
        QuoteItemIn(sl_no=2, description="Documentation & Training", qty=None, unit_price=None),
    ])
    assert items[1]["total"] is None and subtotal == 500.0

def test_grouped_rows_price_counted_once():
    items, subtotal = compute_totals([
        QuoteItemIn(sl_no=1, description="Installation", qty=None, unit_price=None, group_id=1),
        QuoteItemIn(sl_no=2, description="Training", qty=1, unit_price=40000.0, group_id=1),
    ])
    assert subtotal == 40000.0
```

- [ ] **Step 2: Implement `quote_logic.py`**
```python
from decimal import Decimal

def compute_totals(items):
    out, subtotal = [], Decimal("0")
    for it in items:
        d = it.model_dump()
        if it.qty is not None and it.unit_price is not None:
            total = Decimal(str(it.qty)) * Decimal(str(it.unit_price))
            d["total"] = float(total)
            subtotal += total
        else:
            d["total"] = None
        out.append(d)
    return out, subtotal
```

- [ ] **Step 3: Implement `quotes.py`** (shape; error handling shown):
```python
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.deps import get_db, get_current_user, CurrentUser
from app.services.amount_words import amount_in_words
from app.services.ref_no import next_ref_state
from app.services.quote_logic import compute_totals

router = APIRouter(prefix="/api/v1/quotes", tags=["quotes"])

class QuoteItemIn(BaseModel):
    sl_no: int
    description: str
    qty: float | None = None
    unit_price: float | None = None
    group_id: int | None = None

class QuoteIn(BaseModel):
    ref_no: str
    customer_id: str
    quote_date: date
    issue_status: str = "1.1"
    terms: list[str] = []
    items: list[QuoteItemIn] = []

def _get_seq(db):
    return db.table("app_settings").select("value").eq("key", "quote_seq").execute().data[0]["value"]

@router.get("/next-ref")
def next_ref(db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    ref, _ = next_ref_state(_get_seq(db), date.today())
    return {"ref_no": ref}

@router.post("", status_code=201)
def create_quote(q: QuoteIn, db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if db.table("quotes").select("id").eq("ref_no", q.ref_no).execute().data:
        ref, _ = next_ref_state(_get_seq(db), date.today())
        raise HTTPException(409, detail={"message": f"Ref {q.ref_no} already exists", "suggested_ref": ref})
    items, subtotal = compute_totals(q.items)
    row = {"ref_no": q.ref_no, "customer_id": q.customer_id,
           "quote_date": q.quote_date.isoformat(), "issue_status": q.issue_status,
           "terms": q.terms, "subtotal": float(subtotal),
           "amount_in_words": amount_in_words(subtotal), "created_by": user.id}
    quote = db.table("quotes").insert(row).execute().data[0]
    for it in items:
        it["quote_id"] = quote["id"]
    if items:
        db.table("quote_items").insert(items).execute()
    seq_ref, new_state = next_ref_state(_get_seq(db), date.today())
    if q.ref_no == seq_ref:
        db.table("app_settings").update({"value": new_state}).eq("key", "quote_seq").execute()
    return get_quote(quote["id"], db, user)

@router.get("")
def list_quotes(search: str = "", status: str = "", db=Depends(get_db),
                user: CurrentUser = Depends(get_current_user)):
    q = db.table("quotes").select("*, customers(company_name)").order("created_at", desc=True)
    if search: q = q.ilike("ref_no", f"%{search}%")
    if status: q = q.eq("status", status)
    return q.execute().data

@router.get("/{qid}")
def get_quote(qid: str, db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = db.table("quotes").select("*, customers(*), quote_items(*)").eq("id", qid).execute().data
    if not rows: raise HTTPException(404, "Quote not found")
    rows[0]["quote_items"].sort(key=lambda i: i["sl_no"])
    return rows[0]

@router.put("/{qid}")
def update_quote(qid: str, q: QuoteIn, db=Depends(get_db),
                 user: CurrentUser = Depends(get_current_user)):
    clash = db.table("quotes").select("id").eq("ref_no", q.ref_no).neq("id", qid).execute().data
    if clash:
        raise HTTPException(409, detail={"message": f"Ref {q.ref_no} already exists"})
    items, subtotal = compute_totals(q.items)
    db.table("quotes").update({
        "ref_no": q.ref_no, "customer_id": q.customer_id,
        "quote_date": q.quote_date.isoformat(), "issue_status": q.issue_status,
        "terms": q.terms, "subtotal": float(subtotal),
        "amount_in_words": amount_in_words(subtotal),
        "updated_at": "now()"}).eq("id", qid).execute()
    db.table("quote_items").delete().eq("quote_id", qid).execute()
    for it in items: it["quote_id"] = qid
    if items: db.table("quote_items").insert(items).execute()
    return get_quote(qid, db, user)

@router.delete("/{qid}", status_code=204)
def delete_quote(qid: str, db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    db.table("quotes").delete().eq("id", qid).execute()

@router.post("/{qid}/duplicate", status_code=201)
def duplicate_quote(qid: str, db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    src = get_quote(qid, db, user)
    ref, _ = next_ref_state(_get_seq(db), date.today())
    payload = QuoteIn(ref_no=ref, customer_id=src["customer_id"], quote_date=date.today(),
                      issue_status="1.1", terms=src["terms"],
                      items=[QuoteItemIn(**{k: i[k] for k in
                            ("sl_no", "description", "qty", "unit_price", "group_id")})
                             for i in src["quote_items"]])
    return create_quote(payload, db, user)
```
API tests in `test_quotes_api.py` use the FakeDB pattern from Task 6 extended with tables dict, asserting: create computes subtotal + words; duplicate ref → 409 with `suggested_ref`; duplicate endpoint creates a new draft. (Executor: extend FakeDB minimally to make these three assertions run; keep fakes in a shared `tests/fakes.py`.)

- [ ] **Step 4: Run all backend tests — PASS.**  **Step 5: Commit** `git commit -am "feat: quotes API with totals, ref sequencing, duplicate"`

---

### Task 8: PDF generation (WeasyPrint + Jinja2 template)

**Files:**
- Create: `backend/app/templates/quote.html`, `backend/app/services/pdf.py`, `backend/app/routers/documents.py` (PDF route), `backend/tests/test_pdf.py`, `backend/app/static/logo.png`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: quote dict shape from Task 7 `get_quote` (keys: ref_no, quote_date, issue_status, customers{company_name, contact_person}, quote_items[], subtotal, amount_in_words, terms[]), `company` settings dict from app_settings.
- Produces: `render_quote_html(quote: dict, company: dict) -> str`; `quote_pdf(quote: dict, company: dict) -> bytes`; route `GET /api/v1/quotes/{id}/pdf` returning `application/pdf` with `Content-Disposition: attachment; filename="Quote-<ref-with-dashes>.pdf"`.

- [ ] **Step 1: Extract logo from existing PDF**
Run: `cd backend && .venv/bin/pip install pymupdf && .venv/bin/python -c "
import fitz; d=fitz.open('../Quote-ETS-SS10-Yale Electronics Services Pvt Ltd.pdf')
for i,img in enumerate(d[0].get_images()):
    pix=fitz.Pixmap(d, img[0]); pix.save(f'app/static/logo{i}.png')"` then keep the logo image as `app/static/logo.png`, delete extras.

- [ ] **Step 2: Failing test**
```python
import pytest
from app.services.pdf import render_quote_html

QUOTE = {"ref_no": "ETS/SS10/26-27", "quote_date": "2026-05-23", "issue_status": "1.1",
         "subtotal": 40500.0, "amount_in_words": "INR Forty Thousand Five Hundred Only",
         "terms": ["Delivery: 10-12 Weeks"],
         "customers": {"company_name": "Yale Electronics", "contact_person": "Mr Jayashekar"},
         "quote_items": [
             {"sl_no": 1, "description": "Rack", "qty": 1, "unit_price": 40000.0, "total": 40000.0, "group_id": None},
             {"sl_no": 2, "description": "Documentation & Training", "qty": None, "unit_price": None, "total": None, "group_id": None},
             {"sl_no": 3, "description": "Misc", "qty": 1, "unit_price": 500.0, "total": 500.0, "group_id": None}]}
COMPANY = {"name": "Emechanicz Test Solutions Pvt Ltd", "gst_no": "29AADCE7362F1ZI",
           "footer_address": "addr", "order_address": "addr2", "phone": "M", "emails": "E"}

def test_html_renders_fields():
    html = render_quote_html(QUOTE, COMPANY)
    assert "ETS/SS10/26-27" in html and "Yale Electronics" in html
    assert "40,000.00" in html            # Indian-grouped money
    assert "None" not in html             # label rows render blank

@pytest.mark.pdf
def test_pdf_bytes():
    from app.services.pdf import quote_pdf
    assert quote_pdf(QUOTE, COMPANY)[:4] == b"%PDF"
```

- [ ] **Step 3: Implement.** `pdf.py`:
```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

_env = Environment(loader=FileSystemLoader(Path(__file__).parent.parent / "templates"))

def inr(v):
    if v is None: return ""
    s = f"{v:,.2f}"
    # convert western grouping to Indian (12,34,567.00)
    whole, dec = s.split("."); digits = whole.replace(",", "")
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:]); head = head[:-2]
        if head: groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{whole}.{dec}"

_env.filters["inr"] = inr

def render_quote_html(quote: dict, company: dict) -> str:
    logo = (Path(__file__).parent.parent / "static" / "logo.png").resolve()
    return _env.get_template("quote.html").render(q=quote, c=company, logo_path=f"file://{logo}")

def quote_pdf(quote: dict, company: dict) -> bytes:
    from weasyprint import HTML
    return HTML(string=render_quote_html(quote, company)).write_pdf()
```
`quote.html` reproduces the Yale layout: A4 page CSS, header row (title "Quotation" left, logo right), customer block left / ref-status-date right, bordered item table (Sl.No | Description | Qty | Unit Price | Total Price) with grouped rows sharing a `rowspan` price cell when consecutive rows share `group_id`, grand-total row, `INR <amount_in_words>`, numbered **Terms and Conditions**, "For EMechanicZ Test Solution Pvt ltd / Authorised Signatory / This is System generated document hence signature not required.", blue footer with `c.footer_address`, phone, emails, GST. Empty qty/price render `""` via the `inr` filter. Executor writes the full CSS/HTML matching the sample PDF at `Quote-ETS-SS10-... .pdf` (open it for visual reference).
`documents.py` route:
```python
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from app.deps import get_db, get_current_user
from app.routers.quotes import get_quote
from app.services.pdf import quote_pdf

router = APIRouter(prefix="/api/v1/quotes", tags=["documents"])

def _company(db):
    return db.table("app_settings").select("value").eq("key", "company").execute().data[0]["value"]

@router.get("/{qid}/pdf")
def download_pdf(qid: str, db=Depends(get_db), user=Depends(get_current_user)):
    quote = get_quote(qid, db, user)
    fname = "Quote-" + quote["ref_no"].replace("/", "-") + ".pdf"
    return Response(quote_pdf(quote, _company(db)), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})
```

- [ ] **Step 4: Run — PASS** (`pytest -m "not pdf"` if pango missing; otherwise all).  **Step 5: Commit** `git commit -am "feat: PDF quote generation"`

---

### Task 9: DOCX generation

**Files:**
- Create: `backend/app/services/docx_gen.py`, `backend/tests/test_docx.py`
- Modify: `backend/app/routers/documents.py`

**Interfaces:**
- Consumes: same quote/company dicts as Task 8, `inr` filter.
- Produces: `quote_docx(quote: dict, company: dict) -> bytes`; route `GET /api/v1/quotes/{id}/docx` (media type `application/vnd.openxmlformats-officedocument.wordprocessingml.document`).

- [ ] **Step 1: Failing test**
```python
import io
from docx import Document
from app.services.docx_gen import quote_docx
from tests.test_pdf import QUOTE, COMPANY

def test_docx_contains_data():
    doc = Document(io.BytesIO(quote_docx(QUOTE, COMPANY)))
    text = "\n".join(p.text for p in doc.paragraphs)
    table_text = "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    assert "ETS/SS10/26-27" in text + table_text
    assert "Documentation & Training" in table_text
    assert "None" not in table_text
```

- [ ] **Step 2: Implement** with python-docx: logo image top-right (`doc.add_picture`), "Quotation" heading, customer/ref paragraphs, one table (`style="Table Grid"`) with header row + item rows (blank strings for None), grand total row, amount-in-words paragraph, numbered terms, signature block, footer paragraphs (small, centered). Return `bytes` via `io.BytesIO`. Add `/docx` route mirroring the PDF route.

- [ ] **Step 3: Run — PASS.**  **Step 4: Commit** `git commit -am "feat: DOCX quote generation"`

---

### Task 10: Email sending

**Files:**
- Create: `backend/app/services/mailer.py`, `backend/app/routers/email.py`, `backend/tests/test_email.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `quote_pdf` (Task 8), quote fetch (Task 7).
- Produces: `send_mail(to: list[str], subject: str, body: str, attachment: tuple[str, bytes] | None)` raising `MailError` on failure; route `POST /api/v1/quotes/{id}/send-email` body `{"to": ["x@y.z"], "subject": "...", "body": "..."}` → 200 `{"sent": true}` and sets quote status `sent`; SMTP failure → 502, status unchanged.

- [ ] **Step 1: Failing tests** (monkeypatch `smtplib.SMTP`):
```python
from unittest.mock import MagicMock, patch
from tests.test_customers import client  # reuse fake-db client factory pattern

def test_send_marks_sent(...):  # patch smtplib.SMTP, POST send-email, assert 200 and status update called
def test_smtp_failure_keeps_draft(...):  # SMTP.send_message raises -> assert 502, no status update
```
(Executor: write these two tests fully against the shared fakes from `tests/fakes.py`.)

- [ ] **Step 2: Implement.** `mailer.py` uses `smtplib.SMTP(settings.smtp_host, settings.smtp_port)`, `starttls()`, `login`, `EmailMessage` with PDF attachment. Route builds default subject `Quotation {ref_no} - Emechanicz Test Solutions`, attaches the generated PDF, on success updates quote status to `sent`.

- [ ] **Step 3: Run — PASS.**  **Step 4: Commit** `git commit -am "feat: email quote with PDF attachment"`

---

### Task 11: Settings + users API, admin seed script

**Files:**
- Create: `backend/app/routers/settings.py`, `backend/scripts/seed_admin.py`, `backend/tests/test_settings.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `GET /api/v1/settings` (any user; returns company, default_terms, quote_seq), `PUT /api/v1/settings/{key}` (admin), `GET/POST /api/v1/users` (admin; proxies `db.auth.admin.list_users()` / `create_user(email, password, app_metadata={"role": ...}, email_confirm=True)`).
- `seed_admin.py`: idempotent — creates `settings.admin_email` with role admin if missing, prints credentials.

- [ ] **Step 1: Failing tests** — settings GET returns seeded keys (FakeDB), PUT rejected for non-admin (override `get_current_user` with role "user", expect 403).
- [ ] **Step 2: Implement routers + seed script**
```python
# backend/scripts/seed_admin.py
from supabase import create_client
from app.config import settings

sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
existing = [u for u in sb.auth.admin.list_users() if u.email == settings.admin_email]
if existing:
    print(f"Admin {settings.admin_email} already exists")
else:
    sb.auth.admin.create_user({"email": settings.admin_email,
                               "password": settings.admin_password,
                               "email_confirm": True,
                               "app_metadata": {"role": "admin"}})
    print(f"Created admin {settings.admin_email} / {settings.admin_password} — change password after first login")
```
Run: `cd backend && .venv/bin/python -m scripts.seed_admin` — Expected: "Created admin admin@emechanicz.com…". Re-run → "already exists".
- [ ] **Step 3: Run tests — PASS.**  **Step 4: Commit** `git commit -am "feat: settings/users API and admin seed script"`

---

### Task 12: Frontend scaffold, Supabase login, routing shell

**Files:**
- Create: `frontend/` via `npm create vite@latest frontend -- --template react-ts`, then `src/lib/supabase.ts`, `src/lib/api.ts`, `src/pages/Login.tsx`, `src/components/Layout.tsx`, `src/App.tsx` (router + auth guard), Tailwind config, `frontend/.env.example`

**Interfaces:**
- Produces: `supabase` client; `api<T>(path: string, init?: RequestInit): Promise<T>` that attaches `Authorization: Bearer <session.access_token>` and `VITE_API_BASE_URL`, throws `ApiError(status, detail)`; `<RequireAuth>` wrapper; routes `/login, /, /quotes/new, /quotes/:id, /customers, /settings`; responsive Layout (top bar on mobile, sidebar on ≥md) with nav + logout.

- [ ] **Step 1: Scaffold + deps**
Run: `npm create vite@latest frontend -- --template react-ts && cd frontend && npm i @supabase/supabase-js react-router-dom && npm i -D tailwindcss @tailwindcss/vite` (Tailwind v4: add `@import "tailwindcss";` to index.css and the vite plugin).
- [ ] **Step 2: Implement** supabase client from env; Login page (email/password → `supabase.auth.signInWithPassword`, error toast, redirect); `api.ts`:
```ts
import { supabase } from "./supabase";
const BASE = import.meta.env.VITE_API_BASE_URL;
export class ApiError extends Error { constructor(public status: number, public detail: unknown) { super(String(detail)); } }
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const r = await fetch(`${BASE}${path}`, { ...init, headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${data.session?.access_token ?? ""}`, ...init.headers } });
  if (!r.ok) throw new ApiError(r.status, (await r.json().catch(() => ({}))).detail ?? r.statusText);
  return r.status === 204 ? (undefined as T) : r.json();
}
```
- [ ] **Step 3: Verify** `npm run build` passes and `npm run dev` shows login page; logging in with the seeded admin reaches an empty dashboard.
- [ ] **Step 4: Commit** `git commit -am "feat: frontend scaffold with supabase login"`

---

### Task 13: Quote list + customers pages

**Files:**
- Create: `frontend/src/pages/QuoteList.tsx`, `frontend/src/pages/Customers.tsx`, `frontend/src/lib/types.ts`

**Interfaces:**
- Consumes: `api`, routes from Task 12; backend endpoints Tasks 6–7.
- Produces: `types.ts` mirrors backend models (`Customer`, `Quote`, `QuoteItem`). QuoteList: search box, status filter chips (All/Draft/Sent), card list on mobile / table on desktop (ref no, customer, date, subtotal in INR grouping, status badge), row actions View / Duplicate (calls `POST /quotes/{id}/duplicate` then navigates to `/quotes/{newId}`), "New Quote" button. Customers: list + add/edit modal + delete with confirm.

- [ ] **Step 1: Implement both pages.**
- [ ] **Step 2: Verify** `npm run build` passes; manual check on mobile viewport (Chrome devtools) — no horizontal scroll.
- [ ] **Step 3: Commit** `git commit -am "feat: quote list and customers pages"`

---

### Task 14: Quote builder page

**Files:**
- Create: `frontend/src/pages/QuoteBuilder.tsx`, `frontend/src/components/ItemsEditor.tsx`, `frontend/src/lib/inr.ts`

**Interfaces:**
- Consumes: `api`, `types.ts`; endpoints `GET /quotes/next-ref`, `GET/POST/PUT /quotes`, `GET /customers`, `GET /settings` (default terms).
- Produces: builder used for both `/quotes/new` and `/quotes/:id` (edit). `inr.ts` exports `formatINR(n: number): string` with Indian grouping (mirror of backend `inr` filter).

- [ ] **Step 1: Implement.** Sections: (a) customer select with inline "add new" mini-form; (b) ref no (prefilled from next-ref, editable), date, issue status; (c) ItemsEditor — rows with description (textarea autosize), qty, unit price, computed total, "label-only row" toggle that nulls qty/price, add/remove/reorder, running subtotal + live amount-in-words fetched on save response (client shows subtotal, words come from server response); (d) terms editor — default terms loaded from settings, each line editable/removable/addable; (e) Save (POST or PUT) → navigate to preview; 409 shows "Ref exists, suggested: X" with one-click apply.
- [ ] **Step 2: Verify** build passes; create a real quote end-to-end against the running backend (`uvicorn app.main:app --reload`) reproducing the Maxeye quote (1 line item, 12 qty, 137850) — subtotal must show 16,54,200.00.
- [ ] **Step 3: Commit** `git commit -am "feat: quote builder page"`

---

### Task 15: Preview + download + send email + settings page

**Files:**
- Create: `frontend/src/pages/QuotePreview.tsx`, `frontend/src/components/SendEmailDialog.tsx`, `frontend/src/pages/Settings.tsx`

**Interfaces:**
- Consumes: `GET /quotes/{id}`, `/pdf`, `/docx`, `POST /quotes/{id}/send-email`, settings/users endpoints (Task 11).
- Produces: Preview page renders the quote read-only in the same visual layout (HTML/Tailwind approximation), buttons: Edit, Download PDF, Download Word (both via authenticated fetch → blob → object-URL download), Send Email (dialog pre-filled to=customer email, subject `Quotation <ref> - Emechanicz Test Solutions`, editable body; success toast + status badge flips to Sent; failure shows server detail). Settings page (admin-only nav item): company fields, default terms, ref prefix/seq, user list + create user form.

- [ ] **Step 1: Implement pages.**
- [ ] **Step 2: Verify** full happy path manually: login → new quote → save → preview → download PDF (opens, matches layout) → download DOCX (opens in Word/Pages) → send email to your own address (once SMTP creds are in `.env`; otherwise verify the 502 error path shows cleanly and quote stays draft).
- [ ] **Step 3: Commit** `git commit -am "feat: preview, downloads, email dialog, settings"`

---

### Task 16: README + run scripts

**Files:**
- Create: `README.md`, `backend/run.sh` (`uvicorn app.main:app --reload --port 8000`), `frontend/` npm scripts already exist.

- [ ] **Step 1: Write README** — prerequisites (Python 3.12, Node 20, `brew install pango`), setup steps (venv, pip install, migration SQL via Supabase dashboard, seed_admin, npm i), env var tables for both `.env.example` files, how to run both servers, how to run tests.
- [ ] **Step 2: Final full test run**: `cd backend && .venv/bin/pytest -m "not integration" -v` and `cd frontend && npm run build` — all green.
- [ ] **Step 3: Commit** `git commit -am "chore: README and run scripts"`
