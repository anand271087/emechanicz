import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import admin, customers, documents, email, quotes
from app.services.pdf import STATIC_DIR

log = logging.getLogger("emechanicz")

app = FastAPI(title="eMechanicz CRM API")


@app.middleware("http")
async def json_errors(request: Request, call_next):
    # Registered before CORS so CORS wraps it and error responses keep their CORS headers.
    try:
        return await call_next(request)
    except Exception:
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            {"detail": "Something went wrong on the server. Try again, or contact your admin."},
            status_code=500)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


app.include_router(customers.router)
app.include_router(quotes.router)
app.include_router(documents.router)
app.include_router(email.router)
app.include_router(admin.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
