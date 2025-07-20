"""Job handler for k8s/service_mesh resources."""
from __future__ import annotations

from typing import Optional

from ..base import BaseJobHandler


class K8sServiceMeshJobHandler(BaseJobHandler):
    """Manage service mesh (e.g., Istio) manifests via GitOps."""

    async def pre_checks(self) -> None:
        # Validate mesh config
        pass

    async def commit_to_git(self) -> Optional[str]:
        # TODO: Render service mesh config & commit
        return "<commit-sha>"

    async def call_external_apis(self) -> Optional[dict]:
        return None
