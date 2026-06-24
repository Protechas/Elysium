"""Diagnostics export for support."""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import sys
import zipfile
from datetime import datetime

from elysium import __version__
from elysium.core.paths import (
    get_base_dir,
    get_legacy_base_dir,
    get_logs_dir,
    get_manifest_path,
    get_settings_path,
    uses_legacy_layout,
)
from elysium.core.settings import load_settings
from elysium.services.app_registry import AppRegistry

logger = logging.getLogger("Elysium.DiagnosticsService")


def collect_system_info() -> dict:
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "launcher_version": __version__,
        "base_dir": get_base_dir(),
        "legacy_base_dir": get_legacy_base_dir(),
        "uses_legacy_layout": uses_legacy_layout(),
        "executable": sys.executable,
        "frozen": getattr(sys, "frozen", False),
    }


def collect_app_states(registry: AppRegistry | None = None) -> dict:
    registry = registry or AppRegistry()
    states = {}
    for app in registry.apps:
        states[app.id] = {
            "name": app.name,
            "installed": registry.is_installed(app),
            "install_dir": registry.app_install_dir(app),
        }
    return states


def export_diagnostics(output_dir: str | None = None) -> str:
    logs_dir = get_logs_dir()
    if output_dir is None:
        output_dir = logs_dir
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(output_dir, f"Elysium_Diagnostics_{timestamp}.zip")

    registry = AppRegistry()
    manifest_path = get_manifest_path()
    settings_path = get_settings_path()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isfile(settings_path):
            zf.write(settings_path, "settings.json")
        if os.path.isfile(manifest_path):
            zf.write(manifest_path, "manifests/apps.yaml")

        zf.writestr("system_info.json", json.dumps(collect_system_info(), indent=2))
        zf.writestr("installed_versions.json", json.dumps(collect_app_states(registry), indent=2))

        for root, _dirs, files in os.walk(logs_dir):
            for name in files:
                full = os.path.join(root, name)
                arc = os.path.relpath(full, logs_dir)
                zf.write(full, os.path.join("logs", arc))

    logger.info("Diagnostics exported to %s", zip_path)
    return zip_path
