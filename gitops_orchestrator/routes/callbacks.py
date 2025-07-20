"""Webhook callback routes to update job status from external systems."""
from __future__ import annotations

import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_async_session
from ..models import Job, JobHistory, JobStatus, JobHistorySchema

router = APIRouter(prefix="/tenants/{tenant_id}/callbacks", tags=["callbacks"])


@router.post("/{job_id}", response_model=JobHistorySchema, status_code=status.HTTP_202_ACCEPTED)
async def post_callback(
    tenant_id: uuid.UUID,
    job_id: uuid.UUID = Path(...),
    payload: Dict[str, object] | None = None,
    db: AsyncSession = Depends(get_async_session),
):  # noqa: D401
    job = await db.get(Job, job_id)
    if not job or job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Job not found")

    status_str = str(payload.get("status", "")).lower()
    if status_str not in JobStatus.__members__:
        raise HTTPException(status_code=400, detail="Invalid status value")

    job.status = JobStatus[status_str]
    history = JobHistory(
        job_id=job.id,
        status=job.status,
        message=payload.get("external_id"),
        extra_metadata=payload.get("metadata"),
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return JobHistorySchema.model_validate(history)
