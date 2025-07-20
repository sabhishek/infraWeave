"""Generic fallback job handler for uncategorised resources (misc)."""
from __future__ import annotations

from typing import Optional

from ..base import BaseJobHandler


class MiscJobHandler(BaseJobHandler):
    """Placeholder handler for miscellaneous resources."""

    async def pre_checks(self) -> None:
        # Basic validation placeholder
        pass

    async def commit_to_git(self) -> Optional[str]:
        # Unknown resource may not support GitOps
        return None

    async def call_external_apis(self) -> Optional[dict]:
        # Unknown resource may require manual integration
        return None
