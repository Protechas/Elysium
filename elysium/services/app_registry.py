"""Load and query app definitions from manifest."""

from __future__ import annotations

import os
from typing import Any

import yaml

from elysium.core.models import AppDefinition, AppLaunchType
from elysium.core.paths import get_base_dir, get_manifest_path, resolve_app_dir


class AppRegistry:
    def __init__(self, manifest_path: str | None = None, install_root: str | None = None):
        self.manifest_path = manifest_path or get_manifest_path()
        self.install_root = install_root or os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if os.path.isfile(os.path.join(repo_root, "ELYSIUM.py")):
            self.install_root = repo_root
        self._apps: list[AppDefinition] = []
        self._load()

    def _load(self) -> None:
        if not os.path.isfile(self.manifest_path):
            raise FileNotFoundError(f"App manifest not found: {self.manifest_path}")
        with open(self.manifest_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._apps = [AppDefinition.model_validate(item) for item in data.get("apps", [])]

    @property
    def apps(self) -> list[AppDefinition]:
        return list(self._apps)

    def get(self, app_id: str) -> AppDefinition | None:
        for app in self._apps:
            if app.id == app_id:
                return app
        return None

    def get_by_name(self, name: str) -> AppDefinition | None:
        for app in self._apps:
            if app.name == name:
                return app
        return None

    def legacy_programs_dict(self) -> dict[str, dict[str, Any]]:
        """Map display name -> legacy program info dict for ProgramUpdater."""
        programs: dict[str, dict[str, Any]] = {}
        for app in self._apps:
            programs[app.name] = app.to_legacy_program_dict(self.install_root)
        return programs

    def is_installed(self, app: AppDefinition) -> bool:
        app_dir = resolve_app_dir(app.id, app.folder_name())
        if not os.path.isdir(app_dir):
            return False
        entry = os.path.join(app_dir, app.launch.entry)
        return os.path.exists(entry)

    def app_install_dir(self, app: AppDefinition) -> str:
        return resolve_app_dir(app.id, app.folder_name())

    def is_script_launch(self, app: AppDefinition) -> bool:
        return app.launch.type == AppLaunchType.SCRIPT
