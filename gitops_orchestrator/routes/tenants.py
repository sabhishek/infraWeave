"""Tenant API routes."""
from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_async_session
from ..models import Tenant, TenantSchema

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantSchema, status_code=status.HTTP_201_CREATED)
async def create_tenant(name: str, db: AsyncSession = Depends(get_async_session)) -> TenantSchema:  # noqa: D401
    tenant = Tenant(id=uuid4(), name=name)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return TenantSchema.model_validate(tenant)


@router.get("", response_model=list[TenantSchema])
async def list_tenants(db: AsyncSession = Depends(get_async_session)) -> list[TenantSchema]:  # noqa: D401
    tenants = (await db.execute(Tenant.__table__.select())).scalars().all()
    return [TenantSchema.model_validate(t) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantSchema)
async def get_tenant(tenant_id: UUID, db: AsyncSession = Depends(get_async_session)) -> TenantSchema:  # noqa: D401
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantSchema.model_validate(tenant)
