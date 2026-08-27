import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .bootstrap import bootstrap_database
from .config import settings
from .database import engine
from .api import audit, auth, dashboard, documents, evidence, inspections, ncrs, notifications, projects, punch, reports, risks, users, vendors

logger = logging.getLogger("qualicore")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        bootstrap_database()
    except Exception:
        logger.exception("Database bootstrap failed during startup")
    yield

app = FastAPI(
    title="QualiCore AI MVP API",
    version="0.3.4",
    description="Deployable Project Assurance MVP baseline for EPC quality workflows",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router, users.router, projects.router, inspections.router, ncrs.router,
    punch.router, dashboard.router, evidence.router, audit.router,
    notifications.router, documents.router, risks.router, vendors.router, reports.router,
):
    app.include_router(router, prefix="/v1")

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "qualicore-api", "version": "0.3.4"}

@app.get("/health/db", tags=["System"])
def health_db():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.exception("Database health check failed")
        return {
            "status": "error",
            "database": "unavailable",
            "error_type": type(exc).__name__,
        }
