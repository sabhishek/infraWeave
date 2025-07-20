"""Abstract job handler interface.

Each concrete resource handler (e.g. ``k8s/namespace``) implements this class
so that generic orchestration logic (Temporal workflow / dispatcher) can invoke
standardised lifecycle steps.
"""
from __future__ import annotations

import abc
import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseJobHandler(abc.ABC):
    """Shared interface for all resource job handlers."""

    def __init__(
        self,
        *,
        db: AsyncSession,
        job_id: str,
        tenant_id: str,
        payload: Dict[str, Any],
        settings: Any,
    ) -> None:
        self.db = db
        self.job_id = job_id
        self.tenant_id = tenant_id
        self.payload = payload
        self.settings = settings

    # ------------------------------------------------------------------
    # Lifecycle hooks – must be implemented by subclasses unless noted.
    # ------------------------------------------------------------------

    @abc.abstractmethod
    async def pre_checks(self) -> None:
        """Validate input, ensure prerequisites (e.g., quota, naming rules)."""

    async def commit_to_git(self) -> Optional[str]:  # noqa: D401
        """Render template & commit manifest to Git.

        Default implementation is a no-op for purely API-based resources.
        Should return the commit SHA or PR URL when applicable.
        """
        logger.debug("commit_to_git no-op for handler %s", self.__class__.__name__)
        return None

    async def call_external_apis(self) -> Optional[dict]:  # noqa: D401
        """Invoke vendor APIs (ServiceNow, VMware, etc.).

        Default is no-op for pure GitOps resources.
        """
        logger.debug("call_external_apis no-op for handler %s", self.__class__.__name__)
        return None

    async def wait_for_completion(self) -> None:  # noqa: D401
        """Poll for external workflow completion.

        Default immediate return; override for long-running tasks.
        """
        logger.debug("wait_for_completion immediate return for %s", self.__class__.__name__)

    async def post_actions(self) -> None:  # noqa: D401
        """Publish metrics, send notifications, update DB state."""
        logger.debug("post_actions no-op for handler %s", self.__class__.__name__)
