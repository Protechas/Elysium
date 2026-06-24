"""QObject bridge exposing Elysium services to QML."""

from __future__ import annotations

import logging
import os
import webbrowser

from PySide6.QtCore import QObject, Property, QThread, Signal, Slot, Qt

from elysium import __version__
from elysium.core.node_utils import ensure_nodejs_path, find_nodejs_bin_dir
from elysium.core.paths import get_logs_dir, resolve_app_dir
from elysium.core.settings import load_settings, save_settings, set_setting
from elysium.services.app_registry import AppRegistry
from elysium.services.diagnostics_service import export_diagnostics
from elysium.services.environment_service import should_use_isolated_env
from elysium.services.git_service import is_git_installed
from elysium.services.launcher_service import LauncherService
from elysium.services.process_service import close_stale_application_state, patch_flow_launcher, stop_flow_server
from elysium.services.update_service import UpdateService
from elysium.ui.icon_utils import download_icon, resolve_icon_path, to_icon_url
from elysium.ui.models import AppListModel
from elysium.windows.titlebar import apply_native_title_bar_theme

logger = logging.getLogger("Elysium.Bridge")


def status_after_git_update(registry: AppRegistry, app, ok: bool) -> str:
    """Git pull failure on an installed app should not block launch or show Failed."""
    if ok or registry.is_installed(app):
        return "Ready"
    return "Failed"


class InitWorker(QThread):
    progress = Signal(str, int)
    finished_ok = Signal()

    def run(self):
        try:
            self.progress.emit("Closing previous sessions...", 15)
            close_stale_application_state()
            self.progress.emit("Preparing workspace...", 55)
            AppRegistry()
            self.progress.emit("Finishing setup...", 85)
        except Exception as exc:
            logger.warning("Init worker issue: %s", exc)
        self.finished_ok.emit()


class UpdateWorker(QThread):
    app_status = Signal(str, str)
    all_finished = Signal()

    def __init__(self, app_ids: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.app_ids = app_ids
        self._registry = AppRegistry()
        self._updates = UpdateService(self._registry)

    def run(self):
        apps = self._registry.apps
        if self.app_ids:
            apps = [a for a in apps if a.id in self.app_ids and a.repo_url]
        else:
            apps = [a for a in apps if a.repo_url]

        for app in apps:
            self.app_status.emit(app.id, "Updating")
            ok = self._updates.update_app(app)
            self.app_status.emit(app.id, status_after_git_update(self._registry, app, ok))
        self.all_finished.emit()


class IconWorker(QThread):
    icon_ready = Signal(str, str)

    def __init__(self, app_id: str, icon_url: str, parent=None):
        super().__init__(parent)
        self.app_id = app_id
        self.icon_url = icon_url

    def run(self):
        path = download_icon(self.icon_url)
        if path:
            self.icon_ready.emit(self.app_id, path.replace("\\", "/"))


class ElysiumBridge(QObject):
    toastRequested = Signal(str, str)
    errorOccurred = Signal(str, str)
    initProgress = Signal(str, int)
    initFinished = Signal()
    darkModeChanged = Signal()
    settingsChanged = Signal()
    appStatusChanged = Signal(str, str)
    pageChanged = Signal(str)
    statusMessageChanged = Signal()
    statsChanged = Signal()
    settingsDrawerChanged = Signal()
    appViewModeChanged = Signal()
    bubbleModeChanged = Signal()
    bubbleMinimizeRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._registry = AppRegistry()
        self._launcher = LauncherService(self._registry)
        self._updates = UpdateService(self._registry)
        self._apps_model = AppListModel(self)
        self._user_name = self._resolve_user_name()
        settings = load_settings()
        self._dark_mode = settings.get("theme", "Dark") == "Dark"
        self._status_message = ""
        self._is_loading = True
        self._search_text = ""
        self._current_page = "loading"
        self._check_updates = bool(settings.get("check_updates_on_startup", True))
        self._use_isolated = bool(settings.get("use_isolated_envs", False))
        self._use_qml_ui = bool(settings.get("use_qml_ui", True))
        self._app_view_mode = settings.get("app_view_mode", "list")
        self._settings_drawer_open = False
        self._bubble_mode = False
        self._window_width = int(settings.get("window_width", 860))
        self._window_height = int(settings.get("window_height", 680))
        self._window_x = settings.get("window_x")
        self._window_y = settings.get("window_y")
        self._icon_threads: list[IconWorker] = []
        self._init_thread: InitWorker | None = None
        self._update_thread: UpdateWorker | None = None

    @Property(QObject, constant=True)
    def appsModel(self):
        return self._apps_model

    @Property(str, constant=True)
    def version(self):
        return __version__

    @Property(str, constant=True)
    def userName(self):
        return self._user_name

    @Property(bool, notify=darkModeChanged)
    def darkMode(self):
        return self._dark_mode

    @Property(str, notify=statusMessageChanged)
    def statusMessage(self):
        return self._status_message

    @Property(bool, notify=initFinished)
    def isLoading(self):
        return self._is_loading

    @Property(str, notify=pageChanged)
    def currentPage(self):
        return self._current_page

    @Property(str, notify=pageChanged)
    def searchText(self):
        return self._search_text

    @Property(bool, notify=settingsChanged)
    def checkUpdatesOnStartup(self):
        return self._check_updates

    @Property(bool, notify=settingsChanged)
    def useIsolatedEnvs(self):
        return self._use_isolated

    @Property(bool, notify=settingsChanged)
    def useQmlUi(self):
        return self._use_qml_ui

    @Property(int, constant=True)
    def initialWidth(self):
        return self._window_width

    @Property(int, constant=True)
    def initialHeight(self):
        return int(self._window_height)

    @Property(int, constant=True)
    def initialX(self):
        x = self._window_x
        return int(x) if x is not None else -1

    @Property(int, constant=True)
    def initialY(self):
        y = self._window_y
        return int(y) if y is not None else -1

    @Property(str, notify=appViewModeChanged)
    def appViewMode(self):
        return self._app_view_mode

    @Property(bool, notify=settingsDrawerChanged)
    def settingsDrawerOpen(self):
        return self._settings_drawer_open

    @Property(bool, notify=bubbleModeChanged)
    def bubbleMode(self):
        return self._bubble_mode

    @Property(int, notify=statsChanged)
    def totalAppCount(self):
        return self._apps_model.total_count()

    @Property(int, notify=statsChanged)
    def readyAppCount(self):
        return self._apps_model.count_by_status("Ready")

    @Property(int, notify=statsChanged)
    def updatingAppCount(self):
        return self._apps_model.count_by_status("Updating")

    def _emit_stats(self):
        self.statsChanged.emit()

    def _mark_app_status(self, app_id: str, status: str) -> None:
        self._apps_model.update_status(app_id, status)
        self.appStatusChanged.emit(app_id, status)
        self._emit_stats()

    def _resolve_user_name(self) -> str:
        try:
            display = os.environ.get("USERPROFILE", "").split("\\")[-1]
            if display:
                return display.split(" ")[0]
        except Exception:
            pass
        return os.environ.get("USERNAME", "User")

    def _app_status(self, app) -> str:
        if app.requirements and app.requirements.node and not find_nodejs_bin_dir():
            return "Needs Node"
        if not self._registry.is_installed(app):
            return "Not installed"
        return "Ready"

    def _build_app_items(self) -> list[dict]:
        items = []
        for app in self._registry.apps:
            icon = resolve_icon_path(app, self._registry.install_root)
            status = "Loading" if self._is_loading else self._app_status(app)
            items.append(AppListModel.item_from_app(app, icon_path=icon, status=status))
        return items

    @Slot()
    def startInit(self):
        self._is_loading = True
        self._current_page = "loading"
        self.pageChanged.emit(self._current_page)
        self._init_thread = InitWorker(self)
        self._init_thread.progress.connect(self.initProgress.emit)
        self._init_thread.finished_ok.connect(self._on_init_complete)
        self._init_thread.start()

    def _on_init_complete(self):
        self._apps_model.set_items(self._build_app_items())
        self._refresh_statuses()
        self._start_icon_downloads()
        self._is_loading = False
        self._current_page = "home"
        self.pageChanged.emit(self._current_page)
        self.initFinished.emit()
        self._emit_stats()
        if self._check_updates:
            self.updateAllApps()

    def _start_icon_downloads(self):
        for app in self._registry.apps:
            if not app.icon_url:
                continue
            if resolve_icon_path(app, self._registry.install_root):
                continue
            worker = IconWorker(app.id, app.icon_url, self)
            worker.icon_ready.connect(self._on_icon_ready)
            self._icon_threads.append(worker)
            worker.start()

    def _on_icon_ready(self, app_id: str, path: str):
        self._apps_model.update_icon(app_id, to_icon_url(path))

    @Slot()
    def refreshStatuses(self):
        self._refresh_statuses()

    def _refresh_statuses(self):
        for app in self._registry.apps:
            status = self._app_status(app)
            self._apps_model.update_status(app.id, status)
            self.appStatusChanged.emit(app.id, status)
        self._emit_stats()

    @Slot(str)
    def setSearchText(self, text: str):
        self._search_text = text or ""
        self._apps_model.setFilterText(self._search_text)
        self.pageChanged.emit(self._current_page)

    @Slot(str)
    def launchApp(self, app_id: str):
        app = self._registry.get(app_id)
        if not app:
            self.errorOccurred.emit("Launch failed", f"Unknown app: {app_id}")
            return

        if app.requirements and app.requirements.node and not find_nodejs_bin_dir():
            self.errorOccurred.emit(
                "Node.js Required",
                "Node.js is required for Flow. Install from https://nodejs.org and restart Elysium.",
            )
            return

        try:
            if app.id == "flow":
                flow_dir = resolve_app_dir(app.id, app.folder_name())
                patch_flow_launcher(flow_dir)
                stop_flow_server(self._registry)
                env = os.environ.copy()
                ensure_nodejs_path(env)
                self._launcher.launch(app.name, extra_env=env)
            else:
                self._launcher.launch(app.name)

            self._mark_app_status(app_id, "Ready")
            self.toastRequested.emit(f"Launching {app.name}...", "info")
            self._set_status(f"Launched {app.name}")
        except Exception as exc:
            logger.error("Launch failed for %s: %s", app_id, exc, exc_info=True)
            self._mark_app_status(app_id, "Failed")
            self.errorOccurred.emit("Launch failed", str(exc))

    @Slot(str)
    def updateApp(self, app_id: str):
        if not is_git_installed():
            self.errorOccurred.emit("Git Required", "Git is not installed.")
            return
        self._run_update_worker([app_id])

    @Slot()
    def updateAllApps(self):
        if not is_git_installed():
            self._set_status("Updates skipped (Git not installed)")
            return
        self._set_status("Checking for updates...")
        self._run_update_worker(None)

    def _run_update_worker(self, app_ids: list[str] | None):
        if self._update_thread and self._update_thread.isRunning():
            return
        self._update_thread = UpdateWorker(app_ids, self)
        self._update_thread.app_status.connect(self._on_app_update_status)
        self._update_thread.all_finished.connect(self._on_updates_finished)
        self._update_thread.start()

    def _on_app_update_status(self, app_id: str, status: str):
        self._apps_model.update_status(app_id, status)
        self.appStatusChanged.emit(app_id, status)
        self._emit_stats()

    def _on_updates_finished(self):
        for app in self._registry.apps:
            if not app.repo_url:
                status = self._app_status(app)
                self._apps_model.update_status(app.id, status)
                self.appStatusChanged.emit(app.id, status)
        self._emit_stats()
        self._set_status("All updates completed!")
        self.toastRequested.emit("Updates completed", "success")

    @Slot(str)
    def openAppFolder(self, app_id: str):
        app = self._registry.get(app_id)
        if not app:
            return
        folder = self._registry.app_install_dir(app)
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    @Slot()
    def exportDiagnostics(self):
        try:
            path = export_diagnostics()
            self.toastRequested.emit(f"Diagnostics saved to {path}", "success")
        except Exception as exc:
            self.errorOccurred.emit("Export failed", str(exc))

    @Slot()
    def openLogsFolder(self):
        os.startfile(get_logs_dir())

    @Slot()
    def openSettings(self):
        self._settings_drawer_open = True
        self.settingsDrawerChanged.emit()

    @Slot()
    def closeSettings(self):
        self._settings_drawer_open = False
        self.settingsDrawerChanged.emit()

    @Slot(str)
    def setAppViewMode(self, mode: str):
        mode = mode if mode in ("list", "grid") else "list"
        self._app_view_mode = mode
        set_setting("app_view_mode", mode)
        self.appViewModeChanged.emit()

    @Slot(bool)
    def setTheme(self, dark: bool):
        self._dark_mode = dark
        set_setting("theme", "Dark" if dark else "Light")
        self.darkModeChanged.emit()

    @Slot(bool)
    def setCheckUpdatesOnStartup(self, enabled: bool):
        self._check_updates = enabled
        set_setting("check_updates_on_startup", enabled)
        self.settingsChanged.emit()

    @Slot(bool)
    def setUseIsolatedEnvs(self, enabled: bool):
        self._use_isolated = enabled
        set_setting("use_isolated_envs", enabled)
        self.settingsChanged.emit()

    @Slot(bool)
    def setUseQmlUi(self, enabled: bool):
        self._use_qml_ui = enabled
        set_setting("use_qml_ui", enabled)
        self.settingsChanged.emit()

    @Slot()
    def updateElysium(self):
        if not is_git_installed():
            self.errorOccurred.emit("Git Required", "Git is required to update Elysium.")
            return
        self._set_status("Updating Elysium...")
        ok = self._updates.pull_launcher_repo()
        if ok:
            self.toastRequested.emit("Elysium updated. Restart to apply.", "success")
            self._set_status("Elysium update completed.")
        else:
            self.errorOccurred.emit("Update failed", "Could not update Elysium repository.")

    @Slot()
    def openNodeInstallPage(self):
        webbrowser.open("https://nodejs.org")

    @Slot(int, int, int, int)
    def saveWindowGeometry(self, x: int, y: int, width: int, height: int):
        settings = load_settings()
        settings["window_x"] = x
        settings["window_y"] = y
        settings["window_width"] = width
        settings["window_height"] = height
        save_settings(settings)

    @Slot(QObject)
    def applyTitleBar(self, window: QObject):
        try:
            apply_native_title_bar_theme(window, self._dark_mode)
        except Exception as exc:
            logger.debug("Title bar theme skipped: %s", exc)

    @Slot()
    def requestBubbleMinimize(self):
        self.bubbleMinimizeRequested.emit()

    @Slot(bool)
    def setBubbleMode(self, enabled: bool):
        if self._bubble_mode != enabled:
            self._bubble_mode = enabled
            self.bubbleModeChanged.emit()

    @Slot(QObject)
    def enterBubbleMode(self, window: QObject):
        try:
            window.setFlag(Qt.FramelessWindowHint, True)
            window.setFlag(Qt.WindowStaysOnTopHint, True)
            self.setBubbleMode(True)
        except Exception as exc:
            logger.debug("enterBubbleMode failed: %s", exc)

    @Slot(QObject)
    def exitBubbleMode(self, window: QObject):
        try:
            window.setFlag(Qt.FramelessWindowHint, False)
            window.setFlag(Qt.WindowStaysOnTopHint, False)
            self.setBubbleMode(False)
            apply_native_title_bar_theme(window, self._dark_mode)
        except Exception as exc:
            logger.debug("exitBubbleMode failed: %s", exc)

    @Slot(str, str)
    def showContextAction(self, app_id: str, action: str):
        if action == "launch":
            self.launchApp(app_id)
        elif action == "update":
            self.updateApp(app_id)
        elif action == "folder":
            self.openAppFolder(app_id)
        elif action == "node":
            self.openNodeInstallPage()

    def _set_status(self, message: str):
        self._status_message = message
        self.statusMessageChanged.emit()
