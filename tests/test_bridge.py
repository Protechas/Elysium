"""Tests for QML bridge models and filter logic."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from elysium.core.models import AppDefinition, AppLaunchConfig, AppLaunchType
from elysium.ui.models import AppListModel
from elysium.ui.icon_utils import to_icon_url
from elysium.ui.theme import status_colors


@pytest.fixture(scope="session")
def qt_app():
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def _sample_app(app_id: str, name: str, **kwargs) -> AppDefinition:
    return AppDefinition(
        id=app_id,
        name=name,
        description=kwargs.get("description", f"{name} description"),
        tags=kwargs.get("tags", ["tool"]),
        repo_url=kwargs.get("repo_url"),
        launch=AppLaunchConfig(type=AppLaunchType.SCRIPT, entry="run.ps1"),
    )


def test_item_from_app_includes_status_colors(tmp_path):
    icon_file = tmp_path / "dfr.ico"
    icon_file.write_bytes(b"icon")
    app = _sample_app("dfr", "DFR")
    item = AppListModel.item_from_app(app, icon_path=str(icon_file), status="Ready")
    bg, fg = status_colors("Ready")
    assert item["id"] == "dfr"
    assert item["name"] == "DFR"
    assert item["description"] == "DFR description"
    assert item["iconPath"] == to_icon_url(str(icon_file))
    assert item["status"] == "Ready"
    assert item["statusBg"] == bg
    assert item["statusFg"] == fg


def test_to_icon_url_empty_for_missing_file():
    assert to_icon_url("icons/missing.ico") == ""


def test_app_list_model_filter_by_name(qt_app):
    model = AppListModel()
    model.set_items([
        AppListModel.item_from_app(_sample_app("a", "Alpha"), icon_path="", status="Ready"),
        AppListModel.item_from_app(_sample_app("b", "Beta"), icon_path="", status="Ready"),
    ])
    assert model.rowCount() == 2
    model.setFilterText("beta")
    assert model.rowCount() == 1
    assert model.data(model.index(0), AppListModel.NameRole) == "Beta"


def test_app_list_model_filter_by_status(qt_app):
    model = AppListModel()
    model.set_items([
        AppListModel.item_from_app(_sample_app("flow", "Flow"), icon_path="", status="Needs Node"),
        AppListModel.item_from_app(_sample_app("dfr", "DFR"), icon_path="", status="Ready"),
    ])
    model.setFilterText("node")
    assert model.rowCount() == 1
    assert model.data(model.index(0), AppListModel.StatusRole) == "Needs Node"


def test_update_status_refreshes_role_data(qt_app):
    model = AppListModel()
    model.set_items([
        AppListModel.item_from_app(_sample_app("dfr", "DFR"), icon_path="", status="Updating"),
    ])
    model.update_status("dfr", "Ready")
    assert model.data(model.index(0), AppListModel.StatusRole) == "Ready"
    bg, fg = status_colors("Ready")
    assert model.data(model.index(0), AppListModel.StatusBgRole) == bg
    assert model.data(model.index(0), AppListModel.StatusFgRole) == fg


def test_count_by_status(qt_app):
    model = AppListModel()
    model.set_items([
        AppListModel.item_from_app(_sample_app("a", "Alpha"), icon_path="", status="Ready"),
        AppListModel.item_from_app(_sample_app("b", "Beta"), icon_path="", status="Updating"),
        AppListModel.item_from_app(_sample_app("c", "Gamma"), icon_path="", status="Ready"),
    ])
    assert model.total_count() == 3
    assert model.count_by_status("Ready") == 2
    assert model.count_by_status("Updating") == 1


def test_bubble_mode_property(qt_app):
    from elysium.ui.bridge import ElysiumBridge

    bridge = ElysiumBridge()
    assert bridge.bubbleMode is False
    bridge.setBubbleMode(True)
    assert bridge.bubbleMode is True
    bridge.setBubbleMode(False)
    assert bridge.bubbleMode is False


def test_on_updates_finished_preserves_failed_status(qt_app):
    from elysium.ui.bridge import ElysiumBridge

    bridge = ElysiumBridge()
    bridge._apps_model.set_items([
        AppListModel.item_from_app(
            _sample_app("flow", "Flow", repo_url="https://example.com/flow.git"),
            icon_path="",
            status="Failed",
        ),
        AppListModel.item_from_app(_sample_app("local", "Local"), icon_path="", status="Ready"),
    ])

    repo_app = _sample_app("flow", "Flow", repo_url="https://example.com/flow.git")
    local_app = _sample_app("local", "Local")

    class FakeRegistry:
        apps = [repo_app, local_app]

        def is_installed(self, app):
            return True

    bridge._registry = FakeRegistry()
    bridge._on_updates_finished()

    assert bridge._apps_model.data(bridge._apps_model.index(0), AppListModel.StatusRole) == "Failed"
    assert bridge._apps_model.data(bridge._apps_model.index(1), AppListModel.StatusRole) == "Ready"


def test_status_after_git_update_keeps_ready_when_installed(qt_app):
    from elysium.ui.bridge import status_after_git_update

    class FakeRegistry:
        def is_installed(self, app):
            return app.id == "analyzer_plus"

    app = _sample_app("analyzer_plus", "Analyzer+", repo_url="https://example.com/repo.git")
    registry = FakeRegistry()
    assert status_after_git_update(registry, app, ok=False) == "Ready"
    assert status_after_git_update(registry, _sample_app("missing", "Missing"), ok=False) == "Failed"


def test_launch_success_clears_failed_status(qt_app, monkeypatch):
    from elysium.ui.bridge import ElysiumBridge

    bridge = ElysiumBridge()
    bridge._apps_model.set_items([
        AppListModel.item_from_app(
            _sample_app("analyzer_plus", "Analyzer+"),
            icon_path="",
            status="Failed",
        ),
    ])
    monkeypatch.setattr(bridge._launcher, "launch", lambda name, extra_env=None: None)

    bridge.launchApp("analyzer_plus")

    assert bridge._apps_model.data(bridge._apps_model.index(0), AppListModel.StatusRole) == "Ready"
