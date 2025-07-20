"""SQLAlchemy ORM models and matching Pydantic schemas."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator
from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db.session import Base


# -----------------------------------------------------------------------------
# Enumerations
# -----------------------------------------------------------------------------


class ResourceCategory(str, enum.Enum):
    compute_osimages = "compute/osimages"
    compute_vms = "compute/vms"
    k8s_namespace = "k8s/namespace"
    k8s_pvs = "k8s/pvs"
    k8s_service_mesh = "k8s/service_mesh"
    enterprise_networking_lb = "enterprise_networking/lb"
    enterprise_networking_cname = "enterprise_networking/cname"
    enterprise_networking_fw = "enterprise_networking/fw"
    storage_s3tenant = "storage/s3tenant"
    storage_s3bucket = "storage/s3bucket"
    misc = "misc"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class JobType(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    read = "read"


# -----------------------------------------------------------------------------
# SQLAlchemy Models
# -----------------------------------------------------------------------------


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # relationships
    resources: Mapped[list["Resource"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    jobs: Mapped[list["Job"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    category: Mapped[ResourceCategory] = mapped_column(Enum(ResourceCategory, name="resource_category"))
    name: Mapped[str] = mapped_column(String(200))
    last_observed_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="resources")
    jobs: Mapped[list["Job"]] = relationship(back_populates="resource", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("resources.id", ondelete="SET NULL"))
    job_type: Mapped[JobType] = mapped_column(Enum(JobType, name="job_type"))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"), default=JobStatus.pending)
    input_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    result_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="jobs")
    resource: Mapped[Optional["Resource"]] = relationship(back_populates="jobs")
    history: Mapped[list["JobHistory"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobHistory(Base):
    __tablename__ = "job_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status_history"))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    message: Mapped[Optional[str]] = mapped_column(Text)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # renamed from 'metadata' to avoid SQLAlchemy reserved name

    job: Mapped["Job"] = relationship(back_populates="history")


# -----------------------------------------------------------------------------
# Pydantic Schemas (API layer)
# -----------------------------------------------------------------------------


class TenantSchema(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResourceCreateSchema(BaseModel):
    name: str
    category: ResourceCategory
    payload: Dict[str, Any]


class ResourceSchema(ResourceCreateSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    last_observed_state: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobCreateSchema(BaseModel):
    job_type: JobType
    input_payload: Dict[str, Any]

    @field_validator("input_payload")
    def ensure_payload_not_empty(cls, v):  # noqa: N805
        if not v:
            raise ValueError("input_payload must not be empty")
        return v


class JobSchema(JobCreateSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    resource_id: Optional[uuid.UUID]
    status: JobStatus
    result_payload: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobHistorySchema(BaseModel):
    id: int
    job_id: uuid.UUID
    status: JobStatus
    timestamp: datetime
    message: Optional[str]
    extra_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True
