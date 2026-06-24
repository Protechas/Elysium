"""Application settings load/save."""

from __future__ import annotations

import json
import os
from typing import Any

from elysium.core.paths import get_settings_path

DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "Dark",
    "log_level": "INFO",
    "check_updates_on_startup": True,
    "auto_update_apps": False,
    "use_isolated_envs": False,
    "isolated_env_apps": ["dfr"],
    "developer_mode": False,
    "use_qml_ui": True,
    "app_view_mode": "list",
    "window_width": 860,
    "window_height": 680,
    "window_x": None,
    "window_y": None,
}


def load_settings() -> dict[str, Any]:
    path = get_settings_path()
    if not os.path.isfile(path):
        return dict(DEFAULT_SETTINGS)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data)
        return merged
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> None:
    path = get_settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def get_setting(key: str, default: Any = None) -> Any:
    return load_settings().get(key, default)


def set_setting(key: str, value: Any) -> None:
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
