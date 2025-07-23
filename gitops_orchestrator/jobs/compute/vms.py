"""Job handler for compute/vms resources."""
from __future__ import annotations

from typing import Optional
import httpx

from ...config import get_settings
from ...gitops.template_fetcher import get_template_dir
from ...gitops.templater import render_template
from ...gitops.git_writer import commit_change, format_commit_message

from ..base import BaseJobHandler


class ComputeVMsJobHandler(BaseJobHandler):
    """Handle create/update/delete jobs for compute/vms resources."""

    async def pre_checks(self) -> None:
        # Placeholder validation: quota, naming, flavour check
        pass

    async def commit_to_git(self) -> Optional[str]:
        settings = get_settings()
        tpl_dir = get_template_dir("compute/vms")
        rendered = render_template(
            "compute/vms.yaml.j2",
            {"payload": self.payload, "tenant_id": self.tenant_id},
            base_dir=tpl_dir,
        )
        commit_msg = format_commit_message("Add VM", self.payload)
        sha = await commit_change(
            repo_url=settings.resource_repo_map["compute/vms"],
            file_path=f"{self.tenant_id}/{self.payload['name']}.yaml",
            content=rendered,
            commit_msg=commit_msg,
            merge_strategy=settings.resource_merge_strategy_map.get(
                "compute/vms", settings.default_git_merge_strategy
            ),
        )
        return sha

    async def call_external_apis(self) -> Optional[dict]:
        settings = get_settings()
        if not settings.vm_api_base:
            return None  # API not configured
        headers = {"Authorization": f"Bearer {settings.vm_api_token}"} if settings.vm_api_token else {}
        async with httpx.AsyncClient(base_url=settings.vm_api_base, headers=headers, timeout=30) as client:
            resp = await client.post("/v1/vms", json=self.payload)
            resp.raise_for_status()
            return resp.json()
