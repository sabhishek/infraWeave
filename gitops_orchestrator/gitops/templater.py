"""Jinja2 template rendering helper."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

logger = logging.getLogger(__name__)

# Base directory where template files reside (can be overridden)
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    undefined=StrictUndefined,
    autoescape=select_autoescape(enabled_extensions=("yaml", "yml", "json")),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_template(template_name: str, context: Dict[str, Any], *, base_dir: Path | None = None) -> str:
    """Render *template_name* with *context* and return text.

    Raises ``jinja2.exceptions.TemplateError`` on failure.
    """
    logger.debug("Rendering template %s with context keys %s", template_name, list(context.keys()))
    env = _env if base_dir is None else Environment(
        loader=FileSystemLoader(str(base_dir)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("yaml", "yml", "json")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    return template.render(**context)
