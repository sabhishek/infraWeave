"""Resource API routes (CRUDL) scoped by tenant."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path, status, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_async_session
from ..models import Job, JobCreateSchema, JobSchema, Resource, ResourceCategory, ResourceCreateSchema, ResourceSchema
from ..workflows.job_workflow import JobWorkflow

router = APIRouter(prefix="/tenants/{tenant_id}/resources", tags=["resources"])


async def _start_job(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    category: str,
    job_type: str,
    payload: Dict[str, Any],
) -> Job:
    # Lazy import Temporal client and JobWorkflow when needed
    from temporalio.client import Client
    from ..workflows.job_workflow import JobWorkflow
    from ..main import get_temporal_client

    temporal: Client = await get_temporal_client()

    # Persist job row
    job = Job(
        tenant_id=tenant_id,
        resource_id=None,
        job_type=job_type,
        status="pending",
        input_payload=payload,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Kick off workflow
    await temporal.start_workflow(
        JobWorkflow.run,
        id=str(job.id),
        task_queue="gitops-jobs",
        args=[],
        kwargs={
            "job_id": str(job.id),
            "tenant_id": str(tenant_id),
            "category": category,
            "job_type": job_type,
            "payload": payload,
        },
    )
    return job


@router.post("/{category:path}", response_model=JobSchema, status_code=status.HTTP_202_ACCEPTED)
async def create_resource(
    tenant_id: uuid.UUID,
    category: str = Path(..., description="Resource category (e.g., compute/vms)"),
    body: ResourceCreateSchema = Body(...),
    db: AsyncSession = Depends(get_async_session),
):
    job = await _start_job(
        
        db=db,
        tenant_id=tenant_id,
        category=category,
        job_type="create",
        payload=body.payload,
    )
    return JobSchema.model_validate(job)


@router.get("/{category:path}", response_model=List[ResourceSchema])
async def list_resources(
    tenant_id: uuid.UUID,
    category: ResourceCategory,
    db: AsyncSession = Depends(get_async_session),
):
    stmt = select(Resource).where(Resource.tenant_id == tenant_id, Resource.category == category)
    resources = (await db.execute(stmt)).scalars().all()
    return [ResourceSchema.model_validate(r) for r in resources]


@router.get("/{category:path}/{resource_id}", response_model=ResourceSchema)
async def get_resource(
    tenant_id: uuid.UUID,
    category: ResourceCategory,
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    res = await db.get(Resource, resource_id)
    if not res or res.tenant_id != tenant_id or res.category != category:
        raise HTTPException(status_code=404, detail="Resource not found")
    return ResourceSchema.model_validate(res)
