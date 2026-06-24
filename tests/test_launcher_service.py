"""Tests for launch command building."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from elysium.core.models import AppLaunchType
from elysium.services.app_registry import AppRegistry
from elysium.services.launcher_service import LauncherService


@pytest.fixture
def registry():
    return AppRegistry()


def test_build_python_launch_plan(registry, tmp_path, monkeypatch):
    app = registry.get("dfr")
    assert app is not None

    app_dir = tmp_path / "DFR"
    app_dir.mkdir()
    entry = app_dir / "DFR.py"
    entry.write_text("print('ok')", encoding="utf-8")

    monkeypatch.setattr(registry, "app_install_dir", lambda _app: str(app_dir))

    service = LauncherService(registry)
    with patch("elysium.services.launcher_service.resolve_python_for_app", return_value=r"C:\Python\python.exe"):
        plan = service.build_launch_plan("DFR", extra_env={"LAUNCHER_STYLE": "dark"})

    assert plan.command == [r"C:\Python\python.exe", str(entry)]
    assert plan.cwd == str(app_dir)
    assert plan.env["LAUNCHER_STYLE"] == "dark"
    assert plan.env["PYTHONPATH"] == str(app_dir)


def test_build_flow_vbs_launch_plan(registry, tmp_path, monkeypatch):
    app = registry.get("flow")
    assert app is not None
    assert app.launch.type == AppLaunchType.SCRIPT

    app_dir = tmp_path / "Flow"
    launcher_dir = app_dir / "launcher"
    launcher_dir.mkdir(parents=True)
    vbs = launcher_dir / "launch-flow.vbs"
    vbs.write_text("' stub", encoding="utf-8")

    monkeypatch.setattr(registry, "app_install_dir", lambda _app: str(app_dir))

    service = LauncherService(registry)
    plan = service.build_launch_plan("Flow")

    assert plan.command[0] == "wscript.exe"
    assert os.path.normpath(plan.command[1]) == os.path.normpath(str(vbs))
    assert plan.cwd == str(app_dir)


def test_build_launch_plan_missing_entry(registry, tmp_path, monkeypatch):
    app = registry.get("dfr")
    app_dir = tmp_path / "empty"
    app_dir.mkdir()
    monkeypatch.setattr(registry, "app_install_dir", lambda _app: str(app_dir))

    service = LauncherService(registry)
    with pytest.raises(FileNotFoundError):
        service.build_launch_plan("DFR")
