"""Job handler for k8s/pvs resources."""
from __future__ import annotations

from typing import Optional

from ..base import BaseJobHandler


class K8sPVsJobHandler(BaseJobHandler):
    """Manage PersistentVolume manifests via GitOps."""

    async def pre_checks(self) -> None:
        # Validate PVC size, storageClass, etc.
        pass

    async def commit_to_git(self) -> Optional[str]:
        # TODO: Render PV manifest & commit
        return "<commit-sha>"

    async def call_external_apis(self) -> Optional[dict]:
        return None
