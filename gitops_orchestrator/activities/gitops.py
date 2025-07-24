"""Temporal activities for GitOps operations."""
from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Dict, Any

from temporalio import activity


"""GitOps activities."""


logger = logging.getLogger(__name__)


@activity.defn(name="gitops_orchestrator.activities.gitops.render_and_commit")
async def render_and_commit(
    template_name: str,
    context: Dict[str, Any],
    repo_category: str,
    relative_path: str,
    merge_strategy: str | None = None,
) -> str:
    """Render *template_name* with *context* and commit to the Git repo.

    Returns commit SHA (direct) or branch name (PR).
    """
    logger.info("[GitOps] Rendering %s for repo category %s", template_name, repo_category)
    # Import heavy / env-dependent modules lazily so they run in the activity
    from ..config import get_settings
    from ..gitops.git_writer import commit_change, format_commit_message

    settings = get_settings()

    from ..gitops.templater import render_template
    manifest = render_template(template_name, context)

    repo_url = settings.resource_repo_map.get(repo_category)
    if not repo_url:
        raise RuntimeError(f"No Git repository configured for category '{repo_category}'")

    # Determine merge strategy preference hierarchy: explicit arg > per-category map > default
    per_category_strategy = None
    if settings.resource_merge_strategy_map_json:
        try:
            per_category_strategy = json.loads(settings.resource_merge_strategy_map_json).get(repo_category)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in RESOURCE_MERGE_STRATEGY_MAP_JSON env var – ignoring")

    strategy = merge_strategy or per_category_strategy or settings.default_git_merge_strategy

    commit_msg = format_commit_message(
        f"GitOps: update {relative_path}",
        details=f"Template: {template_name}\nResource category: {repo_category}",
    )



    result = await commit_change(
        repo_url=repo_url,
        relative_file_path=Path(relative_path),
        file_content=manifest,
        commit_message=commit_msg,
        merge_strategy=strategy,
    )
    return result
