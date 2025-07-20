"""Job tracking API routes."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio.client import Client

from ..db.session import get_async_session
from ..models import Job, JobSchema, JobStatus
from ..workflows.job_workflow import JobWorkflow

router = APIRouter(prefix="/tenants/{tenant_id}/jobs", tags=["jobs"])


@router.get("", response_model=List[JobSchema])
async def list_jobs(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_async_session)) -> List[JobSchema]:  # noqa: D401
    stmt = select(Job).where(Job.tenant_id == tenant_id)
    jobs = (await db.execute(stmt)).scalars().all()
    return [JobSchema.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobSchema)
async def get_job(tenant_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_async_session)) -> JobSchema:  # noqa: D401
    job = await db.get(Job, job_id)
    if not job or job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobSchema.model_validate(job)


@router.post("/{job_id}/retry", response_model=JobSchema)
async def retry_job(
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
    temporal: Client = Depends(),
    db: AsyncSession = Depends(get_async_session),
):  # noqa: D401
    job = await db.get(Job, job_id)
    if not job or job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.failed:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")

    # Restart workflow with same parameters
    await temporal.start_workflow(
        JobWorkflow.run,
        id=str(uuid.uuid4()),  # new workflow ID
        task_queue="gitops-jobs",
        args=[],
        kwargs={
            "job_id": str(job.id),
            "tenant_id": str(tenant_id),
            "category": job.input_payload.get("category"),
            "job_type": job.job_type.value,
            "payload": job.input_payload,
        },
    )
    job.status = JobStatus.pending
    await db.commit()
    await db.refresh(job)
    return JobSchema.model_validate(job)
