"""Temporal activities for external API calls.

These are placeholders; real integrations should replace the stubs.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def call_external_api(api_name: str, payload: Dict[str, object]) -> Optional[dict]:
    """Stub activity to call *api_name* with *payload*.

    Replace this stub with real SDK / HTTP calls.
    """
    logger.info("[API] Pretending to call %s with payload keys %s", api_name, list(payload.keys()))
    # Fake response
    return {"status": "ok", "api": api_name}
