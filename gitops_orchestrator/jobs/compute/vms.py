"""Job handler for compute/vms resources."""
from __future__ import annotations

from typing import Optional

from ..base import BaseJobHandler


class ComputeVMsJobHandler(BaseJobHandler):
    """Handle create/update/delete jobs for compute/vms resources."""

    async def pre_checks(self) -> None:
        # Placeholder validation: quota, naming, flavour check
        pass

    async def commit_to_git(self) -> Optional[str]:
        # VMs might not rely on GitOps by default; override if needed
        return None

    async def call_external_apis(self) -> Optional[dict]:
        # TODO: Integrate with VMware / cloud provider APIs
        return None
