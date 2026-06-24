"""Shared data models."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AppLaunchType(str, Enum):
    PYTHON = "python"
    SCRIPT = "script"


class AppState(str, Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    READY = "ready"
    UPDATE_AVAILABLE = "update_available"
    UPDATING = "updating"
    RUNNING = "running"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    NEEDS_REQUIREMENT = "needs_requirement"


class AppLaunchConfig(BaseModel):
    type: AppLaunchType = AppLaunchType.PYTHON
    entry: str


class AppEnvironmentConfig(BaseModel):
    type: str = "python"
    requirements: str = "requirements.txt"


class AppRequirementsConfig(BaseModel):
    node: bool = False


class AppDefinition(BaseModel):
    id: str
    name: str
    description: str = ""
    icon_url: str | None = None
    icon_path: str | None = None
    repo_url: str | None = None
    repo_name: str | None = None
    launch: AppLaunchConfig
    environment: AppEnvironmentConfig | None = None
    requirements: AppRequirementsConfig | None = None
    tags: list[str] = Field(default_factory=list)
    windows_supported: bool = True

    def folder_name(self) -> str:
        return self.repo_name or self.name

    def to_legacy_program_dict(self, install_root: str) -> dict[str, Any]:
        """Convert to the dict shape used by legacy ProgramUpdater."""
        info: dict[str, Any] = {
            "id": self.id,
            "description": self.description,
            "script": self.launch.entry,
            "repo_url": self.repo_url,
            "launch_type": self.launch.type.value,
            "tags": self.tags,
        }
        if self.repo_name:
            info["repo_name"] = self.repo_name
        if self.icon_url:
            info["icon_url"] = self.icon_url
        if self.icon_path:
            if not os.path.isabs(self.icon_path):
                info["icon_path"] = os.path.join(install_root, self.icon_path)
            else:
                info["icon_path"] = self.icon_path
        if self.requirements and self.requirements.node:
            info["requires_node"] = True
        return info
