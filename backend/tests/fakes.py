"""In-memory stand-in for the supabase-py query builder used by the API."""
import copy
import itertools
import re
from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import deps
from app.main import app
from app.services.ref_no import financial_year

# (table, embedded table) -> (cardinality, foreign key)
RELATIONS = {
    ("quotes", "customers"): ("one", "customer_id"),
    ("quotes", "quote_items"): ("many", "quote_id"),
}

_ids = itertools.count(1)


class FakeQuery:
    def __init__(self, db, table):
        self.db, self.table = db, table
        self.op, self.payload, self.embeds = "select", None, []
        self.filters, self._order, self._limit = [], None, None

    def select(self, cols="*"):
        self.embeds = re.findall(r"(\w+)\(([^)]*)\)", cols)
        return self

    def insert(self, rows):
        self.op, self.payload = "insert", rows
        return self

    def update(self, values):
        self.op, self.payload = "update", values
        return self

    def delete(self):
        self.op = "delete"
        return self

    def eq(self, col, val):
        self.filters.append(lambda r: str(r.get(col)) == str(val))
        return self

    def neq(self, col, val):
        self.filters.append(lambda r: str(r.get(col)) != str(val))
        return self

    def ilike(self, col, pattern):
        needle = pattern.strip("%").lower()
        self.filters.append(lambda r: needle in str(r.get(col, "")).lower())
        return self

    def order(self, col, desc=False):
        self._order = (col, desc)
        return self

    def limit(self, n):
        self._limit = n
        return self

    def _matches(self):
        return [r for r in self.db.tables[self.table] if all(f(r) for f in self.filters)]

    def _embed(self, row):
        row = copy.deepcopy(row)
        for name, _cols in self.embeds:
            kind, fk = RELATIONS[(self.table, name)]
            if kind == "one":
                row[name] = next((copy.deepcopy(r) for r in self.db.tables[name]
                                  if r["id"] == row.get(fk)), None)
            else:
                row[name] = [copy.deepcopy(r) for r in self.db.tables[name] if r[fk] == row["id"]]
        return row

    def execute(self):
        if self.db.fail_on and self.db.fail_on(self):
            raise RuntimeError("simulated db failure")
        rows = self.db.tables[self.table]
        if self.op == "insert":
            new = self.payload if isinstance(self.payload, list) else [self.payload]
            new = [{"id": f"id{next(_ids)}", **copy.deepcopy(r)} for r in new]
            rows.extend(new)
            data = new
        elif self.op == "update":
            data = self._matches()
            for r in data:
                r.update(copy.deepcopy(self.payload))
        elif self.op == "delete":
            data = self._matches()
            self.db.tables[self.table] = [r for r in rows if r not in data]
            if self.table == "quotes":
                gone = {r["id"] for r in data}
                self.db.tables["quote_items"] = [
                    i for i in self.db.tables["quote_items"] if i["quote_id"] not in gone]
        else:
            data = [self._embed(r) for r in self._matches()]
            if self._order:
                col, desc = self._order
                data.sort(key=lambda r: str(r.get(col, "")), reverse=desc)
            if self._limit is not None:
                data = data[: self._limit]
        return SimpleNamespace(data=copy.deepcopy(data))


class FakeDB:
    def __init__(self):
        self.tables = {"customers": [], "quotes": [], "quote_items": [], "app_settings": []}
        self.fail_on = None
        self.seed_settings()

    def table(self, name):
        return FakeQuery(self, name)

    def seed_settings(self):
        self.tables["app_settings"] = [
            {"key": "company", "value": {
                "name": "Emechanicz Test Solutions Pvt Ltd",
                "signatory_name": "EMechanicZ Test Solution Pvt ltd",
                "footer_address": "1st Floor, Ramamurthy Nagar, Bengaluru – 560016,",
                "phone": "+91 9844561185", "emails": "Sales@emechanicz.com",
                "gst_no": "29AADCE7362F1ZI",
                "closing_line": "Thanking you.", "system_generated_note": "System generated."}},
            {"key": "quote_seq", "value": {"prefix": "P", "fy": financial_year(date.today()),
                                           "seq": 301}},
            {"key": "default_intro", "value": "Dear Sir,"},
            {"key": "default_terms", "value": ["Delivery: 3-4 Weeks"]},
        ]


def make_client(role="user"):
    db = FakeDB()
    app.dependency_overrides[deps.get_db] = lambda: db
    app.dependency_overrides[deps.get_current_user] = lambda: deps.CurrentUser(
        id="u1", email="u@x.com", role=role)
    return TestClient(app), db
