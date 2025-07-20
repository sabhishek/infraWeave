"""Deprecated: `jobs/misc.py` is superseded by `jobs/misc.__init__`.

Kept for backward-compatibility; re-exports :class:`MiscJobHandler` from the
subpackage so existing imports continue to work.
"""
from __future__ import annotations

from .misc import MiscJobHandler  # noqa: F401 – re-export
