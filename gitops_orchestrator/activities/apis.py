"""Temporal activities for external API calls.

These are placeholders; real integrations should replace the stubs.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def call_external_api(api_name: str, payload: Any) -> Optional[dict]:
    """Stub activity to call *api_name* with *payload*.

    Replace this stub with real SDK / HTTP calls.
    """
    logger.info("[API] Pretending to call %s with payload %s", api_name, payload)
    # Fake response
    return {"status": "ok", "api": api_name}


@activity.defn
async def lookup_tenant_name(tenant_id: str) -> str:  # noqa: D401
    """Return human-friendly tenant name for *tenant_id*.

    In real deployment this would query an internal service/DB. For now we just
    return the ID unchanged so templates/path remain deterministic.
    """
    logger.info("[API] Looking up name for tenant %s", tenant_id)
    from ..config import get_settings
    import asyncpg

    settings = get_settings()
    conn = await asyncpg.connect(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    try:
        row = await conn.fetchrow("SELECT name FROM tenants WHERE id = $1", tenant_id)
        return row["name"] if row else tenant_id
    finally:
        await conn.close()
