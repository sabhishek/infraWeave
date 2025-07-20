"""Temporal workflow orchestrating a resource job lifecycle."""
from __future__ import annotations

import logging
from typing import Dict, Optional

from temporalio import workflow


from ..config import get_settings
from ..dispatcher import get_handler_class

logger = logging.getLogger(__name__)
settings = get_settings()


@workflow.defn
class JobWorkflow:  # noqa: D101 – Temporal workflow class
    """Temporal workflow coordinating job execution steps."""

    def __init__(self) -> None:  # noqa: D401
        self._job_id: str | None = None

    @workflow.run
    async def run(
        self,
        *,
        job_id: str,
        tenant_id: str,
        category: str,
        job_type: str,
        payload: Dict[str, object],
    ) -> str:
        self._job_id = job_id
        logger.info("[WF] Starting job %s (%s)", job_id, category)

        # Instantiate handler (no DB session in workflow context; heavy logic in activities)
        HandlerCls = get_handler_class(category)
        handler_name = HandlerCls.__name__

        # Record pending -> running
        await workflow.execute_activity(
            mon_act.record_job_status,
            job_id,
            "running",
            message=f"Handler: {handler_name}",
            schedule_to_close_timeout=60,
        )

        # Import activities lazily to avoid loading non-deterministic libs during sandbox import
        from ..activities import apis as apis_act
        from ..activities import gitops as gitops_act
        from ..activities import monitoring as mon_act

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
                gitops_act.render_and_commit,
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
            message=str(api_result or git_result),
            schedule_to_close_timeout=60,
        )

        logger.info("[WF] Job %s completed", job_id)
        return "succeeded"
