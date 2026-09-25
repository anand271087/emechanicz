# eMechanicz CRM

Sales portal for Emechanicz Test Solutions. The first module is the **quotation builder**: create a
quotation in the company's standard format, preview it, download it as PDF or Word, and email it to
the customer. Works on desktop and mobile browsers.

```
frontend/  React + Vite + TypeScript + Tailwind   (login via Supabase Auth, calls the API)
backend/   FastAPI (Python)                        (all data access, PDF/Word generation, email)
supabase/  SQL migrations for the Supabase Postgres database
```

The browser only uses Supabase to sign in. Every data request goes to the FastAPI backend with the
user's Supabase token. The backend verifies it against the project's public signing keys and talks
to Postgres with the service-role key. Row Level Security is on with no policies, so the public anon
key cannot read or write any table.

## Prerequisites

- Python 3.12+ and Node 20+
- Pango, for PDF generation: `brew install pango` (macOS) or `apt install libpango-1.0-0 libpangoft2-1.0-0` (Debian/Ubuntu)
- A Supabase project

## First-time setup

1. **Database.** In the Supabase dashboard, open SQL Editor, paste the contents of
   `supabase/migrations/001_initial_schema.sql`, and run it. It creates the tables and default
   settings (company details, terms, and quote numbering starting after ETS/P301).
2. **Turn off public sign-ups.** Authentication → Sign In / Providers → turn off "Allow new users to
   sign up". Team members are added by an admin under Settings. (The API also rejects any account
   that an admin didn't create, but switch this off so strangers can't create accounts at all.)
3. **Backend**
   ```bash
   cd backend
   cp .env.example .env        # then fill in the values below
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python -m scripts.seed_admin   # creates ADMIN_EMAIL / ADMIN_PASSWORD as admin
   ```
4. **Frontend**
   ```bash
   cd frontend
   cp .env.example .env        # then fill in the values below
   npm install
   ```

### backend/.env

| Variable | What it is |
|---|---|
| `SUPABASE_URL` | `https://<project-ref>.supabase.co` |
| `SUPABASE_ANON_KEY` | Project Settings → API keys → anon (used only by the admin seed check) |
| `SUPABASE_SERVICE_ROLE_KEY` | Project Settings → API keys → service_role. Secret: never put it in the frontend |
| `CORS_ORIGINS` | Allowed frontend origins, comma-separated, e.g. `https://crm.emechanicz.com`. `*` for local dev |
| `SMTP_HOST`, `SMTP_PORT` | Mail server of the sending mailbox. Port 587 uses STARTTLS; 465 uses SSL |
| `SMTP_USER`, `SMTP_PASSWORD` | Mailbox login. For Google Workspace or Zoho, use an app password |
| `SMTP_FROM` | Address quotations are sent from, e.g. `Sales@emechanicz.com` |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | First admin account created by `scripts.seed_admin` |

Common SMTP hosts: Google Workspace `smtp.gmail.com:587`, Zoho `smtp.zoho.in:587`,
Microsoft 365 `smtp.office365.com:587`.

### frontend/.env

| Variable | What it is |
|---|---|
| `VITE_SUPABASE_URL` | Same project URL as the backend |
| `VITE_SUPABASE_ANON_KEY` | The anon (public) key |
| `VITE_API_BASE_URL` | Where the backend runs, e.g. `http://localhost:8000` |

## Running locally

```bash
cd backend && ./run.sh          # API on http://localhost:8000 (docs at /docs)
cd frontend && npm run dev      # app on http://localhost:5173
```

To try it on your phone, run `npm run dev` and open the "Network" URL it prints (same Wi-Fi), and set
`VITE_API_BASE_URL` to your computer's LAN address, e.g. `http://192.168.1.20:8000`.

## Tests

```bash
cd backend && .venv/bin/pytest            # unit + API tests (in-memory DB)
cd backend && .venv/bin/pytest -m integration   # checks the live Supabase schema
cd frontend && npm test && npm run build
```

## How the quotation document is made

`backend/app/templates/quote.html` is the single source of the quotation layout. The PDF is rendered
from it by WeasyPrint, and the in-app preview shows the same HTML, so what you see is what the
customer gets. The Word file (`backend/app/services/docx_gen.py`) follows the same layout. The
font is Carlito, a free font with the same measurements as Calibri, bundled in `backend/app/static/fonts`.
Company details, default terms, and numbering are edited in the app under Settings (admin only).

Line items support two special cases from existing quotations:
- **Description-only rows**: leave qty and price blank (e.g. "Documentation & Training").
- **Shared price**: tick "Share one price with the row above" to merge rows under one qty/price cell.

## Adding a new CRM module

The code is organised so each module is self-contained:

1. **Database**: add `supabase/migrations/00N_<module>.sql` (enable RLS, no policies).
3. **Backend**: `app/schemas/<module>.py` (request models), `app/services/<module>.py` (logic and data
   access), `app/routers/<module>.py` (HTTP routes under `/api/v1/<module>`, with
   `Depends(get_current_user)`), then `app.include_router(...)` in `app/main.py`. Add tests in
   `backend/tests/` using `tests/fakes.py`.
4. **Frontend**: pages in `src/modules/<module>/`, one entry in `src/modules/registry.tsx` (sidebar and
   mobile tabs), and a route in `src/App.tsx`.

## Deploying

- **Backend**: any Python host with Pango (Render, Railway, Fly.io, a VPS). Start command:
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"`. Set the backend env vars there and
  `CORS_ORIGINS` to the frontend URL.
- **Frontend**: `npm run build` and host `frontend/dist` on Vercel or Netlify, with the three
  `VITE_*` variables set at build time. Configure the host to serve `index.html` for all routes.
