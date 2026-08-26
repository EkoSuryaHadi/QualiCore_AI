from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .bootstrap import bootstrap_database
from .config import settings
from .api import audit, auth, dashboard, documents, evidence, inspections, ncrs, notifications, projects, punch, reports, risks, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_database()
    yield

app = FastAPI(
    title="QualiCore AI MVP API",
    version="0.3.1",
    description="Deployable Project Assurance MVP baseline for EPC quality workflows",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in (
    auth.router, users.router, projects.router, inspections.router, ncrs.router,
    punch.router, dashboard.router, evidence.router, audit.router,
    notifications.router, documents.router, risks.router, reports.router,
):
    app.include_router(router, prefix="/v1")

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "qualicore-api", "version": "0.3.1"}
