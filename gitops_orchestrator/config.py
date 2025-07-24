"""Configuration management for the Hybrid Infra Orchestrator.

All user-tunable settings are sourced from environment variables (optionally
loaded from a local `.env` file).  Sensible localhost defaults make the app
work out-of-the-box while every parameter can be overridden for production.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict, Literal, Optional

from pydantic import Field, ValidationError, computed_field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Centralised application settings.

    Attributes can be overridden via environment variables.  By default we load
    variables from a `.env` file (if present) using python-dotenv (implicitly
    through `BaseSettings`).
    """

    # ---------------------------------------------------------------------
    # Database (PostgreSQL)
    # ---------------------------------------------------------------------
    db_host: str = Field("localhost", env="DB_HOST")
    db_port: int = Field(5432, env="DB_PORT")
    db_name: str = Field("gitops_orchestrator", env="DB_NAME")
    db_user: str = Field("postgres", env="DB_USER")
    db_password: str = Field("postgres", env="DB_PASSWORD")

    # ---------------------------------------------------------------------
    # Temporal
    # ---------------------------------------------------------------------
    temporal_host: str = Field("localhost", env="TEMPORAL_HOST")
    temporal_port: int = Field(7233, env="TEMPORAL_PORT")
    temporal_namespace: str = Field("default", env="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field("gitops-jobs", env="TEMPORAL_TASK_QUEUE")

    # ---------------------------------------------------------------------
    # Git / GitHub
    # ---------------------------------------------------------------------
    git_pat: str = Field("", env="GIT_PAT", description="GitHub Personal Access Token")
    git_username: str = Field("", env="GIT_USERNAME")

    # ------------------------------------------------------------------
    # Git merge strategy controls
    # ------------------------------------------------------------------
    # Fallback merge strategy when a resource-specific one isn't provided.
    default_git_merge_strategy: Literal["direct", "pr"] = Field(
        "direct", env="GIT_MERGE_STRATEGY"
    )

    # JSON mapping of *resource category* ➜ merge strategy ("direct" or "pr").
    # Same keys as ``resource_repo_map_json`` so you can tune behaviour per repo.
    # Examples:
    #   '{"k8s/namespace": "pr", "k8s/pvs": "direct"}'
    #   '{"compute/osimages": "pr", "compute/vms": "direct"}'
    #   '{"enterprise_networking/lb": "pr", "enterprise_networking/fw": "pr"}'
    resource_merge_strategy_map_json: Optional[str] = Field(
        None, env="RESOURCE_MERGE_STRATEGY_MAP_JSON"
    )

    # JSON mapping of resource category ➜ repository clone URL
    # Examples:
    #   '{"k8s": "git@github.com:acme-org/ocp-resources-gitops.git"}'
    #   '{"compute": "git@github.com:acme-org/vm-resources-gitops.git"}'
    #   '{"compute/osimages": "git@github.com:acme-org/osimage-resources.git",
    #     "compute/vms": "git@github.com:acme-org/vm-resources.git",
    #     "k8s/namespace": "git@github.com:acme-org/ocp-resources.git",
    #     "k8s/pvs": "git@github.com:acme-org/ocp-pvs.git",
    #     "k8s/service_mesh": "git@github.com:acme-org/mesh-resources.git",
    #     "enterprise_networking/lb": "git@github.com:acme-org/net-lb.git",
    #     "enterprise_networking/cname": "git@github.com:acme-org/net-dns.git",
    #     "enterprise_networking/fw": "git@github.com:acme-org/net-fw.git",
    #     "misc": "git@github.com:acme-org/misc-resources.git"}'
    resource_repo_map_json: Optional[str] = Field(None, env="RESOURCE_REPO_MAP_JSON")

    # Template repositories per resource category
    template_repo_map_json: Optional[str] = Field(None, env="TEMPLATE_REPO_MAP_JSON")

    # External VM provider API
    vm_api_base: str = Field("", env="VM_API_BASE")
    vm_api_token: str = Field("", env="VM_API_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Permit env vars that don't correspond to explicit fields so optional
        # feature flags do not break startup (e.g., future vars).
        extra = "ignore"

    # ------------------------------------------------------------------
    # Derived / helper properties
    # ------------------------------------------------------------------
    @computed_field  # type: ignore[misc]
    @property
    def sqlalchemy_database_uri(self) -> str:  # noqa: D401 – returns URI string
        """Return an *async* SQLAlchemy connection URI."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"  # noqa: S608 – internal value
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def resource_repo_map(self) -> Dict[str, str]:
        """Parse :pyattr:`resource_repo_map_json` into a real dict."""
        if not self.resource_repo_map_json:
            return {}
        try:
            return json.loads(self.resource_repo_map_json)
        except (TypeError, json.JSONDecodeError) as exc:  # defensive
            raise ValidationError([{
                "loc": ("RESOURCE_REPO_MAP_JSON",),
                "msg": "Invalid JSON for RESOURCE_REPO_MAP_JSON",
                "type": "value_error.jsondecode",
            }]) from exc

    @computed_field  # type: ignore[misc]
    @property
    def template_repo_map(self) -> Dict[str, str]:
        """Parse :pyattr:`template_repo_map_json` into a real dict."""
        if not self.template_repo_map_json:
            return {}
        try:
            return json.loads(self.template_repo_map_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValidationError([
                {
                    "loc": ("TEMPLATE_REPO_MAP_JSON",),
                    "msg": "Invalid JSON for TEMPLATE_REPO_MAP_JSON",
                    "type": "value_error.jsondecode",
                }
            ]) from exc


@lru_cache()
def get_settings() -> AppSettings:
    """Return a singleton of :class:`AppSettings`."""
    return AppSettings()
