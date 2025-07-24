"""Temporal workflow orchestrating a resource job lifecycle."""
from __future__ import annotations

import logging
from typing import Dict, Optional, Any

from temporalio import workflow


from ..config import get_settings

logger = logging.getLogger(__name__)


@workflow.defn
class JobWorkflow:  # noqa: D101 – Temporal workflow class
    """Temporal workflow coordinating job execution steps."""

    def __init__(self) -> None:  # noqa: D401
        self._job_id: str | None = None

    @workflow.run
    async def run(
        self,
        params: Dict[str, Any],
    ) -> str:
        job_id = params["job_id"]
        tenant_id = params["tenant_id"]
        category = params["category"]
        job_type = params["job_type"]
        payload = params["payload"]
        self._job_id = job_id
        logger.info("[WF] Starting job %s (%s)", job_id, category)

        # Import activities lazily to avoid sandbox issues
        from ..activities import monitoring as mon_act
        from ..activities import apis as apis_act

        # Record pending -> running (avoid importing heavy dispatcher in workflow)
        await workflow.execute_activity(
            mon_act.record_job_status,
            job_id,
            "running",
            f"Category: {category}",
            schedule_to_close_timeout=60,
        )
        

        # Pre-checks via API activity
        await workflow.execute_activity(
            apis_act.call_external_api,
            "pre_checks",
            {"category": category, "payload": payload},
            schedule_to_close_timeout=60,
        )

        git_result: Optional[str] = None
        if "k8s" in category or "storage" in category or "compute" in category:
            # Assume GitOps path for these; in real dispatch we’d ask handler
            git_result = await workflow.execute_activity(
                "gitops_orchestrator.activities.gitops.render_and_commit",
                template_name=f"{category}.yaml.j2",
                context=payload,
                repo_category=category.split("/")[0],  # top-level group
                relative_path=f"{tenant_id}/{payload.get('name', 'resource')}.yaml",
                merge_strategy=None,
                schedule_to_close_timeout=300,
            )

        # External API calls if needed (stub)
        api_result = await workflow.execute_activity(
            apis_act.call_external_api,
            "resource_api",
            payload,
            schedule_to_close_timeout=300,
        )

        # Wait / poll – simulated by a monitoring activity
        await workflow.execute_activity(
            mon_act.record_job_status,
            job_id,
            "completed",
            str(api_result or git_result),
            schedule_to_close_timeout=60,
        )

        logger.info("[WF] Job %s completed", job_id)
        return "succeeded"
