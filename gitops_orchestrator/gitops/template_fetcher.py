"""Clone & cache template repositories for resource categories."""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Root directory under the OS tmp dir to cache cloned template repos
_CACHE_ROOT = Path(tempfile.gettempdir()) / "template_repos"
_CACHE_ROOT.mkdir(exist_ok=True)


def get_template_dir(category: str) -> Path:
    """Return local path to template repository for *category*.

    Clones the repo on first request and then reuses the cached clone on
    subsequent calls. Raises ``KeyError`` if the category is not configured.
    """
    try:
        repo_url = settings.template_repo_map[category]
    except KeyError as err:
        raise KeyError(f"No template repo configured for category '{category}'") from err

    repo_name = repo_url.rsplit("/", 1)[-1].removesuffix(".git")
    target = _CACHE_ROOT / repo_name

    if target.exists():
        logger.debug("Using cached template repo for %s at %s", category, target)
        return target

    logger.info("Cloning template repo %s -> %s", repo_url, target)
    try:
        subprocess.check_call(["git", "clone", "--depth", "1", repo_url, str(target)])
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to clone template repo %s: %s", repo_url, exc)
        raise RuntimeError(f"Unable to clone template repo {repo_url}") from exc

    return target
