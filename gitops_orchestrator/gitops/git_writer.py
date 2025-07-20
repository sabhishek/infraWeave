"""Git interaction utilities (clone, commit, push, PR).

This module uses *GitPython* for simplicity. For production-grade workflows you
may swap to `dulwich`, `pygit2`, or invoke the platform API directly.
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
import textwrap
from pathlib import Path
from typing import Optional

from git import Repo  # type: ignore[import-not-found]

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GitOpsError(RuntimeError):
    """Raised on Git operation failure."""


async def commit_change(
    *,
    repo_url: str,
    relative_file_path: Path,
    file_content: str,
    commit_message: str,
    merge_strategy: str = "direct",
    branch_name: Optional[str] = None,
) -> str:
    """Clone (or reuse) *repo_url*, commit *file_content*, push.

    If *merge_strategy* is "pr", a branch is created and pushed; for now we
    return the branch name and leave PR creation to an out-of-band process.

    Returns the commit SHA (direct) or branch ref (pr).
    """

    # Work in a temp dir per invocation
    workdir = Path(tempfile.mkdtemp(prefix="gitops_"))
    logger.debug("Cloning %s into %s", repo_url, workdir)

    try:
        repo = Repo.clone_from(repo_url, workdir, env=_git_env())
        # Ensure we're on main
        if repo.head.is_detached:
            repo.git.checkout("-B", "main")

        if merge_strategy == "pr":
            branch_name = branch_name or f"gitops-{relative_file_path.stem}"
            repo.git.checkout("-B", branch_name)

        full_path = workdir / relative_file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(file_content)

        repo.index.add([str(full_path.relative_to(workdir))])
        repo.index.commit(commit_message)

        origin = repo.remotes.origin
        origin.push(refspec=f"HEAD:{repo.active_branch.name}")
        logger.info("Pushed changes to %s (%s)", repo_url, repo.active_branch)

        return repo.head.commit.hexsha if merge_strategy == "direct" else branch_name  # type: ignore[return-value]
    except Exception as exc:  # noqa: BLE001 – broad for wrapper
        logger.error("Git operation failed: %s", exc, exc_info=True)
        raise GitOpsError(str(exc)) from exc
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _git_env() -> dict[str, str]:
    """Return environment variables for Git auth."""
    env = os.environ.copy()
    if settings.git_pat:
        env["GIT_ASKPASS"] = ""  # prevent prompts
        env["GITHUB_TOKEN"] = settings.git_pat
    if settings.git_username:
        env["GIT_AUTHOR_NAME"] = settings.git_username
        env["GIT_COMMITTER_NAME"] = settings.git_username
    # Ensure non-interactive
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def format_commit_message(summary: str, details: Optional[str] = None) -> str:  # noqa: D401
    """Helper to produce conventional commit messages."""
    if details:
        return f"{summary}\n\n{textwrap.dedent(details).strip()}\n"
    return summary
