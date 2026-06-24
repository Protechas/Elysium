"""App icon path resolution."""

from __future__ import annotations

import os

import requests

from PySide6.QtCore import QUrl

from elysium.core.paths import get_base_dir, resolve_app_dir
from elysium.core.models import AppDefinition

ICON_DOWNLOAD_TIMEOUT = 8


def to_icon_url(path: str) -> str:
    """Return a QML-safe file URL for a local icon path."""
    if not path:
        return ""
    if path.startswith("file:"):
        return path
    normalized = os.path.normpath(path)
    if not os.path.isfile(normalized):
        return ""
    return QUrl.fromLocalFile(normalized).toString()


def download_icon(url: str, base_dir: str | None = None) -> str | None:
    try:
        filename = url.split("/")[-1]
        local_path = os.path.join(base_dir or get_base_dir(), filename)
        if os.path.exists(local_path):
            return local_path
        response = requests.get(url, timeout=ICON_DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)
        return local_path
    except requests.RequestException:
        return None


def resolve_icon_path(app: AppDefinition, install_root: str) -> str:
    if app.icon_path:
        path = app.icon_path
        if not os.path.isabs(path):
            path = os.path.join(install_root, path)
        if os.path.exists(path):
            return path.replace("\\", "/")

    base = get_base_dir()
    if app.icon_url:
        cached = os.path.join(base, os.path.basename(app.icon_url))
        if os.path.exists(cached):
            return cached.replace("\\", "/")
        app_dir = resolve_app_dir(app.id, app.folder_name())
        repo_icon = os.path.join(app_dir, os.path.basename(app.icon_url))
        if os.path.exists(repo_icon):
            return repo_icon.replace("\\", "/")

    for candidate in (
        os.path.join(base, "ELYSIUM_icon.ico"),
        os.path.join(install_root, "ELYSIUM_icon.ico"),
        os.path.join(install_root, "combiner_icon.ico"),
    ):
        if os.path.exists(candidate):
            return candidate.replace("\\", "/")
    return ""
