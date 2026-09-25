# eMechanicz CRM — Quotation Builder: Design Spec

Date: 2026-09-25
Status: Approved approach (Option B: FastAPI + React + Supabase)

## 1. Purpose

First module of an eventual CRM for Emechanicz Test Solutions Pvt Ltd. Lets the
sales team create quotations matching the company's existing quote format,
export them as PDF or Word, and email them to customers — from desktop or
mobile browser.

Success criteria:
- A quote visually matching the existing "Yale" quote layout can be created,
  previewed, downloaded (PDF + DOCX), and emailed in one flow.
- Quotes and customers persist centrally; old quotes are searchable and
  duplicable.
- Works well on a phone browser.

## 2. Architecture (standard, three parts)

```
React (Vite) SPA  ──login──▶  Supabase Auth
       │
       └──REST (Bearer JWT)──▶  FastAPI backend ──▶ Supabase Postgres (via supabase-py)
                                     ├──▶ WeasyPrint  → PDF
                                     ├──▶ python-docx → DOCX
                                     └──▶ SMTP (Sales@emechanicz.com) → email
```

- **frontend/** — React + Vite + TypeScript, Tailwind CSS, responsive
  (mobile-first). Uses `@supabase/supabase-js` for auth only; all data goes
  through the backend API.
- **backend/** — FastAPI (Python 3.12), verifies Supabase JWT on each request,
  talks to Supabase Postgres with the service-role key, generates documents,
  sends email.
- **Supabase** — Auth (email+password), Postgres, Storage (logo, optional
  generated-file archive).

### Environment files
- `backend/.env` — `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
  `SUPABASE_JWT_SECRET` (for token verification), `SMTP_HOST`, `SMTP_PORT`,
  `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.
- `frontend/.env` — `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`,
  `VITE_API_BASE_URL`.
- Both git-ignored; `.env.example` committed for each.

## 3. Database schema (Supabase Postgres, created via SQL migration)

- `customers(id, company_name, contact_person, email, phone, address, gst_no, created_at)`
- `quotes(id, ref_no unique, customer_id FK, quote_date, issue_status text default '1.1',
  status enum[draft, sent], subtotal, amount_in_words, terms jsonb,
  created_by uuid, created_at, updated_at)`
- `quote_items(id, quote_id FK, sl_no, description, qty numeric nullable,
  unit_price numeric nullable, total numeric nullable, group_id int nullable)`
  - qty/price nullable → supports label-only rows ("Documentation & Training").
  - `group_id` lets consecutive rows share one merged price (Yale rows 18–19).
- `app_settings(key, value jsonb)` — company info, quote sequence counter,
  default terms, ref-no prefix/format.

Backend owns all table access (service-role key); RLS locked down so the anon
key can only authenticate.

## 4. Quote reference numbers

Format `ETS/<PREFIX><SEQ>/<FY>` e.g. `ETS/P302/26-27`. App suggests next
number from the sequence counter per financial year (Apr–Mar); field remains
editable; uniqueness enforced by DB constraint.

## 5. Amount in words

Indian numbering (lakh/crore), e.g. `INR Twenty One Lakh Thirty Eight
Thousand Only`. Computed in backend, shown live in frontend.

## 6. Document generation

- Single HTML/CSS template matching the Yale-format quote (logo, header with
  Customer/Kind Attn/Ref No/Issue Status/Date, item table, grand total,
  amount in words, numbered Terms & Conditions, "system generated" note,
  footer with addresses/GST/contacts).
- PDF: WeasyPrint renders that template → preview and PDF are identical.
- DOCX: python-docx builds the same structure programmatically.
- Logo stored in repo/Supabase storage (extract from existing PDF).

## 7. Email

Backend endpoint sends via SMTP using the Sales@emechanicz.com mailbox.
Compose screen pre-fills: to = customer email, subject =
`Quotation <ref_no> - Emechanicz Test Solutions`, editable body, PDF attached.
On success, quote status → `sent`.

## 8. Auth & roles

- Supabase email+password. Roles in `app_metadata.role`: `admin` | `user`.
- Seed script (`backend/scripts/seed_admin.py`) creates the admin account via
  Supabase Admin API using the service-role key.
- Admin-only: settings, user management. Users: quotes + customers.

## 9. API surface (FastAPI, `/api/v1`)

- `GET/POST/PUT/DELETE /customers`
- `GET/POST/PUT/DELETE /quotes` (+ `POST /quotes/{id}/duplicate`)
- `GET /quotes/next-ref`
- `GET /quotes/{id}/pdf`, `GET /quotes/{id}/docx`
- `POST /quotes/{id}/send-email`
- `GET/PUT /settings` (admin)
- `GET/POST /users` (admin, proxied to Supabase admin API)

## 10. Screens (React)

1. Login
2. Quote list (search, status filter, duplicate)
3. Quote builder (customer picker + inline add, ref no, date, items grid with
   auto totals, label-only & grouped rows, terms editor with defaults)
4. Preview + actions (PDF/Word download, send email dialog)
5. Customers directory
6. Settings (admin): company info, terms defaults, users

## 11. Error handling

- Backend returns structured JSON errors; frontend shows toasts.
- Duplicate ref no → clear inline error with suggested next number.
- SMTP failure → quote stays draft, error surfaced, retry possible.
- PDF/DOCX generation failures logged with quote id.

## 12. Testing

- Backend: pytest — amount-in-words converter, ref-no generator (FY
  rollover), quote totals, PDF/DOCX generation smoke tests, API auth checks.
- Frontend: builds cleanly; manual UAT on desktop + mobile viewport.

## 13. Out of scope (v1)

Multi-currency, GST line calculation on totals (GST stays a T&C line as
today), PO/invoice modules, approval workflows, analytics.
