"""FastAPI application entry point for Hybrid Infra Orchestrator."""
from __future__ import annotations

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from temporalio.client import Client

from .config import get_settings
from .db.session import get_async_session
from .routes import callbacks, jobs, metrics, resources, tenants

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="Hybrid Infra Orchestrator", version="0.1.0")

# CORS (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: Temporal client (singleton)
_temporal_client: Client | None = None


async def get_temporal_client() -> Client:  # noqa: D401
    global _temporal_client  # noqa: PLW0603 – module-level singleton
    if _temporal_client is None:
        _temporal_client = await Client.connect(f"{settings.temporal_host}:{settings.temporal_port}")
    return _temporal_client


# ------------------------------------------------------------------
# Include routers
# ------------------------------------------------------------------
app.include_router(tenants.router, prefix="/api/v1")
app.include_router(resources.router, prefix="/api/v1", dependencies=[Depends(get_temporal_client), Depends(get_async_session)])
app.include_router(jobs.router, prefix="/api/v1", dependencies=[Depends(get_temporal_client), Depends(get_async_session)])
app.include_router(callbacks.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1", dependencies=[Depends(get_async_session)])


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:  # noqa: D401
    """Simple health check."""
    return {"status": "ok"}
