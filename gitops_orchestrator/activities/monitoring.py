"""Temporal activity for emitting metrics / updating job state."""
from __future__ import annotations

import logging
from typing import Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def record_job_status(job_id: str, status: str, message: Optional[str] = None) -> None:  # noqa: D401
    """Stub to push job status metrics/logs.

    Replace with real monitoring/export later.
    """
    logger.info("[Metrics] job %s -> %s (%s)", job_id, status, message or "")
