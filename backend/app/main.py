from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import APP_VERSION, SLOT_MINUTES
from app.db import get_db
from app.routers import bookings, machines
from app.schemas import Stats
from app.service import build_stats

app = FastAPI(
    title="WashQ",
    version=APP_VERSION,
    description="Hostel laundry slots, so two people cannot claim the same machine.",
    # Under /api so they come through nginx and the ingress, which only
    # send /api to the backend. At the default /docs the React app catches
    # the route and the link in the footer goes nowhere.
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

# Nginx serves the frontend and proxies /api, so same origin in production.
# This is here for running vite on :5173 against the backend on :8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(machines.router)
app.include_router(bookings.router)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "version": APP_VERSION, "slot_minutes": SLOT_MINUTES}


@app.get("/health/ready", tags=["ops"])
def ready(db: Session = Depends(get_db)):
    """Separate from /health because readiness needs the database."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/api/stats", response_model=Stats, tags=["stats"])
def stats(db: Session = Depends(get_db)):
    return build_stats(db)


# Exposes /metrics in the format Prometheus scrapes.
Instrumentator().instrument(app).expose(app, include_in_schema=False)
