"""Tests for settings persistence used by the QML shell."""

from __future__ import annotations

import json

import pytest

from elysium.core import settings as settings_module


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "get_settings_path", lambda: str(path))
    return path


def test_theme_round_trip(settings_file):
    settings_module.set_setting("theme", "Light")
    loaded = settings_module.load_settings()
    assert loaded["theme"] == "Light"
    assert settings_file.is_file()


def test_window_geometry_round_trip(settings_file):
    data = settings_module.load_settings()
    data["window_x"] = 120
    data["window_y"] = 80
    data["window_width"] = 720
    data["window_height"] = 900
    settings_module.save_settings(data)

    reloaded = settings_module.load_settings()
    assert reloaded["window_x"] == 120
    assert reloaded["window_y"] == 80
    assert reloaded["window_width"] == 720
    assert reloaded["window_height"] == 900


def test_qml_ui_flag_default_on(settings_file):
    assert settings_module.load_settings()["use_qml_ui"] is True


def test_app_view_mode_default_list(settings_file):
    assert settings_module.load_settings()["app_view_mode"] == "list"


def test_app_view_mode_persists(settings_file):
    settings_module.set_setting("app_view_mode", "grid")
    assert settings_module.load_settings()["app_view_mode"] == "grid"


def test_qml_ui_flag_persists(settings_file):
    settings_module.set_setting("use_qml_ui", True)
    assert settings_module.load_settings()["use_qml_ui"] is True
    raw = json.loads(settings_file.read_text(encoding="utf-8"))
    assert raw["use_qml_ui"] is True
