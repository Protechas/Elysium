"""App and launcher update operations (service layer stub for Phase 2)."""

from __future__ import annotations

import logging
import os
import subprocess

from elysium.core.models import AppDefinition
from elysium.core.paths import get_repo_sync_dir
from elysium.services.app_registry import AppRegistry
from elysium.services.git_service import git_command, is_git_installed
from elysium.windows.process_flags import no_window_flags

logger = logging.getLogger("Elysium.UpdateService")


class UpdateService:
    def __init__(self, registry: AppRegistry | None = None):
        self.registry = registry or AppRegistry()

    def pull_launcher_repo(self) -> bool:
        if not is_git_installed():
            return False
        base = get_repo_sync_dir()
        git_dir = os.path.join(base, ".git")
        try:
            if os.path.isdir(git_dir):
                result = subprocess.run(
                    git_command("-C", base, "pull", "--ff-only"),
                    capture_output=True,
                    text=True,
                    creationflags=no_window_flags(),
                )
            else:
                parent = os.path.dirname(base)
                folder = os.path.basename(base)
                result = subprocess.run(
                    git_command("clone", "https://github.com/Protechas/Elysium.git", folder),
                    cwd=parent,
                    capture_output=True,
                    text=True,
                    creationflags=no_window_flags(),
                )
            return result.returncode == 0
        except Exception as exc:
            logger.error("Launcher repo update failed: %s", exc)
            return False

    def update_app(self, app: AppDefinition) -> bool:
        if not app.repo_url or not is_git_installed():
            return False
        app_dir = self.registry.app_install_dir(app)
        try:
            if not os.path.exists(app_dir) or not os.listdir(app_dir):
                result = subprocess.run(
                    git_command(
                        "clone", "--depth", "1", "--single-branch",
                        app.repo_url, app_dir,
                    ),
                    capture_output=True,
                    text=True,
                    creationflags=no_window_flags(),
                )
            else:
                result = subprocess.run(
                    git_command("-C", app_dir, "pull", "--depth", "1", "--no-tags"),
                    capture_output=True,
                    text=True,
                    creationflags=no_window_flags(),
                )
            return result.returncode == 0
        except Exception as exc:
            logger.error("Update failed for %s: %s", app.name, exc)
            return False
