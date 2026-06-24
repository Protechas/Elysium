"""Per-app isolated Python environments."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import venv

from elysium.core.paths import resolve_app_env_dir
from elysium.core.settings import get_setting
from elysium.windows.process_flags import no_window_flags

logger = logging.getLogger("Elysium.EnvironmentService")


def should_use_isolated_env(app_id: str) -> bool:
    if not get_setting("use_isolated_envs", False):
        return False
    allowed = get_setting("isolated_env_apps", ["dfr"])
    return app_id in allowed


def get_venv_python(app_id: str) -> str:
    env_dir = resolve_app_env_dir(app_id)
    if os.name == "nt":
        python_exe = os.path.join(env_dir, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(env_dir, "bin", "python")
    return python_exe


def ensure_venv(app_id: str) -> str:
    python_exe = get_venv_python(app_id)
    if os.path.isfile(python_exe):
        return python_exe

    env_dir = resolve_app_env_dir(app_id)
    logger.info("Creating virtual environment for %s at %s", app_id, env_dir)
    venv.create(env_dir, with_pip=True)
    if not os.path.isfile(python_exe):
        raise RuntimeError(f"Failed to create virtual environment for {app_id}")
    return python_exe


def install_requirements(app_id: str, requirements_file: str) -> bool:
    if not os.path.isfile(requirements_file):
        return True
    python_exe = ensure_venv(app_id)
    cmd = [python_exe, "-m", "pip", "install", "-r", requirements_file]
    logger.info("Installing requirements for %s: %s", app_id, requirements_file)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        creationflags=no_window_flags(),
    )
    if result.returncode != 0:
        logger.error("pip install failed for %s: %s", app_id, result.stderr)
        return False
    return True


def resolve_python_for_app(app_id: str, app_dir: str) -> str:
    if should_use_isolated_env(app_id):
        python_exe = ensure_venv(app_id)
        req = os.path.join(app_dir, "requirements.txt")
        install_requirements(app_id, req)
        return python_exe
    return sys.executable
