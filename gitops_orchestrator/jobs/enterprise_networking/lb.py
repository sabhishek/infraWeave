"""Job handler for enterprise_networking/lb resources."""
from __future__ import annotations

from typing import Optional

from ..base import BaseJobHandler


class EnterpriseNetworkingLBHandler(BaseJobHandler):
    """Manage load balancer configs via vendor APIs (stub)."""

    async def pre_checks(self) -> None:
        # Validate LB spec
        pass

    async def call_external_apis(self) -> Optional[dict]:
        # TODO: Integrate with F5/AVI/etc.
        return None
