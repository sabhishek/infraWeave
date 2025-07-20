"""Bootstrap Temporal worker for GitOps orchestrator."""
from __future__ import annotations

import os
import asyncio
import logging

# Disable workflow sandbox entirely for local dev (Temporal SDK 1.3)
os.environ.setdefault("TEMPORAL_PYTHON_DISABLE_SANDBOX", "1")



from temporalio.client import Client
from temporalio.worker import Worker

from .activities import apis as apis_act
from .activities import gitops as gitops_act
from .activities import monitoring as mon_act
from .config import get_settings
from .workflows.job_workflow import JobWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


aSYNC_DEF_TIMEOUT = 60  # seconds


async def main() -> None:  # noqa: D401
    client = await Client.connect(f"{settings.temporal_host}:{settings.temporal_port}")

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[JobWorkflow],
        activities=[
            gitops_act.render_and_commit,
            apis_act.call_external_api,
            mon_act.record_job_status,
        ],
    )
    logger.info("Starting Temporal worker on queue '%s'", settings.temporal_task_queue)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
