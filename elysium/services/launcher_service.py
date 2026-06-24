"""Build and execute app launch commands."""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass

from elysium.core.models import AppDefinition, AppLaunchType
from elysium.services.app_registry import AppRegistry
from elysium.services.environment_service import resolve_python_for_app
from elysium.windows.process_flags import no_window_flags

logger = logging.getLogger("Elysium.LauncherService")


@dataclass
class LaunchPlan:
    app_id: str
    app_name: str
    command: list[str]
    cwd: str
    env: dict[str, str]


class LauncherService:
    def __init__(self, registry: AppRegistry | None = None):
        self.registry = registry or AppRegistry()

    def build_launch_plan(
        self,
        app_name: str,
        *,
        extra_env: dict[str, str] | None = None,
    ) -> LaunchPlan:
        app = self.registry.get_by_name(app_name)
        if not app:
            raise ValueError(f"Unknown app: {app_name}")

        app_dir = self.registry.app_install_dir(app)
        entry_path = os.path.join(app_dir, app.launch.entry)
        if not os.path.exists(entry_path):
            raise FileNotFoundError(
                f"Could not find {app.launch.entry} in {app_dir}"
            )

        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        env.setdefault("PYTHONPATH", app_dir)

        if app.launch.type == AppLaunchType.SCRIPT:
            if entry_path.lower().endswith(".vbs"):
                command = ["wscript.exe", entry_path]
            else:
                command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", entry_path]
        else:
            python_exe = resolve_python_for_app(app.id, app_dir)
            command = [python_exe, entry_path]

        return LaunchPlan(
            app_id=app.id,
            app_name=app.name,
            command=command,
            cwd=app_dir,
            env=env,
        )

    def launch(
        self,
        app_name: str,
        *,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.Popen:
        plan = self.build_launch_plan(app_name, extra_env=extra_env)
        logger.info("Launching %s: %s", plan.app_name, plan.command)
        return subprocess.Popen(
            plan.command,
            cwd=plan.cwd,
            env=plan.env,
            creationflags=no_window_flags(),
        )
