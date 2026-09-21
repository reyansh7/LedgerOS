"""FastAPI main application for LedgerOS."""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import init_db
from apps.api.routes.dashboard import router as dashboard_router
from apps.api.routes.reconciliation import router as reconciliation_router
from apps.api.routes.investigations import router as investigations_router
from apps.api.routes.approvals import router as approvals_router
from apps.api.routes.audit import router as audit_router
from apps.api.routes.evaluations import router as evaluations_router
from apps.api.routes.razorpay import router as razorpay_router
from apps.api.routes.system import router as system_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield


app = FastAPI(
    title="LedgerOS API",
    description="Autonomous Finance Controller & Revenue Recovery Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(dashboard_router, prefix="/api")
app.include_router(reconciliation_router, prefix="/api")
app.include_router(investigations_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(razorpay_router, prefix="/api")
app.include_router(system_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "LedgerOS API", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "name": "LedgerOS",
        "description": "Autonomous Finance Controller & Revenue Recovery Platform",
        "docs": "/docs",
    }
