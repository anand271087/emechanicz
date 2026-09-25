from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import admin, customers, documents, email, quotes
from app.services.pdf import STATIC_DIR

app = FastAPI(title="eMechanicz CRM API")
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
