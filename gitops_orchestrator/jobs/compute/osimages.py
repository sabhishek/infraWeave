"""Job handler for build/publish OS images in compute category."""
from __future__ import annotations

from typing import Optional

from ..base import BaseJobHandler


class ComputeOSImagesJobHandler(BaseJobHandler):
    """Handle create/update/delete jobs for compute/osimages resources."""

    async def pre_checks(self) -> None:
        # TODO: Add validation logic e.g. image naming, base image availability
        await super().pre_checks() if hasattr(super(), "pre_checks") else None  # type: ignore[arg-type]

    async def commit_to_git(self) -> Optional[str]:
        # Stub: This resource may rely purely on API integrations (e.g., VMware image builder)
        return await super().commit_to_git()  # type: ignore[misc]

    async def call_external_apis(self) -> Optional[dict]:
        # TODO: Invoke image build pipeline / registry APIs
        return await super().call_external_apis()  # type: ignore[misc]
