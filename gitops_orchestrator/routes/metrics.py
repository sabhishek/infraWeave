"""Tenant-level metrics endpoints."""
from __future__ import annotations

import uuid
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_async_session
from ..models import Job, JobStatus, Resource, ResourceCategory

router = APIRouter(prefix="/tenants/{tenant_id}", tags=["metrics"])


@router.get("/resources/summary")
async def resource_summary(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_async_session)) -> Dict[str, int]:  # noqa: D401
    stmt = (
        select(Resource.category, func.count())
        .where(Resource.tenant_id == tenant_id)
        .group_by(Resource.category)
    )
    rows = (await db.execute(stmt)).all()
    return {row[0]: row[1] for row in rows}


@router.get("/metrics")
async def tenant_metrics(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_async_session)) -> Dict[str, object]:  # noqa: D401
    # Job counts by status
    stmt_jobs = (
        select(Job.status, func.count())
        .where(Job.tenant_id == tenant_id)
        .group_by(Job.status)
    )
    job_rows = (await db.execute(stmt_jobs)).all()
    jobs_by_status = {row[0]: row[1] for row in job_rows}

    # Last job timestamp per resource type
    stmt_last = (
        select(Resource.category, func.max(Job.created_at))
        .join(Job, Resource.id == Job.resource_id)
        .where(Resource.tenant_id == tenant_id)
        .group_by(Resource.category)
    )
    last_rows = (await db.execute(stmt_last)).all()
    last_job_ts = {row[0]: row[1].isoformat() if row[1] else None for row in last_rows}

    return {
        "jobs": jobs_by_status,
        "last_job_ts": last_job_ts,
    }
