"""Dual-path install resolution for Elysium 1.x and 2.x."""

from __future__ import annotations

import os
from functools import lru_cache

try:
    from platformdirs import user_documents_dir
except ImportError:
    user_documents_dir = None  # type: ignore

PROTECH_DIR_NAME = "Protech"
ELYSIUM_DIR_NAME = "Elysium"
LEGACY_FOLDER_NAME = "Elysium"

_BASE_DIR_CACHE: str | None = None


def get_new_default_base_dir() -> str:
    local_app = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(local_app, PROTECH_DIR_NAME, ELYSIUM_DIR_NAME)


def get_legacy_base_dir() -> str:
    if user_documents_dir is not None:
        try:
            docs = user_documents_dir()
            if docs:
                return os.path.join(docs, LEGACY_FOLDER_NAME)
        except Exception:
            pass
    return os.path.join(os.path.expanduser("~"), "Documents", LEGACY_FOLDER_NAME)


def _dir_has_elysium_data(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    markers = (
        "ELYSIUM.py",
        "settings.json",
        ".git",
        "DFR",
        "Flow",
        "logs",
        "apps",
    )
    try:
        entries = set(os.listdir(path))
    except OSError:
        return False
    return any(marker in entries for marker in markers)


def resolve_base_dir(*, prefer_new: bool = False) -> str:
    """
    Resolve the active Elysium base directory.

    Order:
    1. New path if it exists and has data (or prefer_new for fresh installs)
    2. Legacy Documents path if it exists and has data
    3. New default path (created on demand)
    """
    global _BASE_DIR_CACHE
    if _BASE_DIR_CACHE is not None:
        return _BASE_DIR_CACHE

    new_base = get_new_default_base_dir()
    legacy_base = get_legacy_base_dir()

    if prefer_new or (_dir_has_elysium_data(new_base) and not _dir_has_elysium_data(legacy_base)):
        _BASE_DIR_CACHE = new_base
    elif _dir_has_elysium_data(legacy_base):
        _BASE_DIR_CACHE = legacy_base
    elif _dir_has_elysium_data(new_base):
        _BASE_DIR_CACHE = new_base
    else:
        # Fresh install: prefer new layout; git bootstrap may still clone into legacy
        # until migration — legacy wins if ELYSIUM.py already lives there from EXE pull
        if os.path.isfile(os.path.join(legacy_base, "ELYSIUM.py")):
            _BASE_DIR_CACHE = legacy_base
        else:
            _BASE_DIR_CACHE = new_base

    return _BASE_DIR_CACHE


def reset_base_dir_cache() -> None:
    global _BASE_DIR_CACHE
    _BASE_DIR_CACHE = None


def get_base_dir() -> str:
    path = resolve_base_dir()
    os.makedirs(path, exist_ok=True)
    return path


def uses_legacy_layout() -> bool:
    return os.path.normcase(get_base_dir()) == os.path.normcase(get_legacy_base_dir())


def get_apps_dir() -> str:
    base = get_base_dir()
    if uses_legacy_layout():
        return base
    apps = os.path.join(base, "apps")
    os.makedirs(apps, exist_ok=True)
    return apps


def get_logs_dir() -> str:
    logs = os.path.join(get_base_dir(), "logs")
    os.makedirs(logs, exist_ok=True)
    return logs


def get_envs_dir() -> str:
    envs = os.path.join(get_base_dir(), "envs")
    os.makedirs(envs, exist_ok=True)
    return envs


def get_cache_dir() -> str:
    cache = os.path.join(get_base_dir(), "cache")
    os.makedirs(cache, exist_ok=True)
    return cache


def get_settings_path() -> str:
    return os.path.join(get_base_dir(), "settings.json")


def get_crash_log_path() -> str:
    return os.path.join(get_logs_dir(), "elysium_crash.log")


def get_launcher_log_path() -> str:
    return os.path.join(get_logs_dir(), "launcher.log")


def get_repo_sync_dir() -> str:
    """Directory targeted by git clone/pull for the Elysium launcher repo."""
    return get_base_dir()


@lru_cache(maxsize=64)
def resolve_app_dir(app_id: str, folder_name: str | None = None) -> str:
    folder = folder_name or app_id
    if uses_legacy_layout():
        return os.path.join(get_legacy_base_dir(), folder)
    return os.path.join(get_apps_dir(), folder)


def resolve_app_env_dir(app_id: str) -> str:
    env_dir = os.path.join(get_envs_dir(), app_id)
    os.makedirs(env_dir, exist_ok=True)
    return env_dir


def get_app_log_path(app_id: str) -> str:
    app_logs = os.path.join(get_logs_dir(), "apps")
    os.makedirs(app_logs, exist_ok=True)
    return os.path.join(app_logs, f"{app_id}.log")


def get_manifest_path() -> str:
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bundled = os.path.join(package_root, "manifests", "apps.yaml")
    if os.path.isfile(bundled):
        return bundled
    base_manifest = os.path.join(get_base_dir(), "manifests", "apps.yaml")
    if os.path.isfile(base_manifest):
        return base_manifest
    return bundled


def get_stop_flow_script_path() -> str | None:
    candidates = [
        os.path.join(get_base_dir(), "launcher", "stop-flow.ps1"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "launcher", "stop-flow.ps1"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None
