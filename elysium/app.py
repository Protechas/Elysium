"""PySide6 QML application shell."""

from __future__ import annotations

import os
import sys

# Must configure DLL paths before importing PySide6 Qt modules.
import elysium.ui.qt_bootstrap  # noqa: F401

from PySide6.QtCore import QLibraryInfo, QUrl, qInstallMessageHandler
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from elysium.core.paths import get_base_dir
from elysium.ui.bridge import ElysiumBridge

_qml_messages: list[str] = []


def _qt_message_handler(mode, context, message) -> None:  # noqa: ANN001
    text = str(message)
    _qml_messages.append(text)
    if mode >= 2:  # QtWarningMsg and above
        print(text, file=sys.stderr)


def _configure_qml_engine_paths(engine: QQmlApplicationEngine) -> None:
    import PySide6

    root = os.path.dirname(os.path.abspath(PySide6.__file__))
    for path in (
        os.path.join(root, "qml"),
        QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath),
    ):
        if path and os.path.isdir(path):
            engine.addImportPath(path)

    qml_root = os.path.join(os.path.dirname(__file__), "ui", "qml")
    engine.addImportPath(qml_root)


def create_app(argv: list[str] | None = None) -> tuple[QApplication, QQmlApplicationEngine, ElysiumBridge]:
    global _qml_messages
    _qml_messages = []
    qInstallMessageHandler(_qt_message_handler)

    # QApplication (not QGuiApplication) — QGuiApplication + Text on Windows Store
    # Python can hit a native crash when Qt loads fonts for QML text.
    app = QApplication(argv or sys.argv)
    app.setApplicationName("Elysium")
    app.setOrganizationName("Protech")

    icon_path = os.path.join(get_base_dir(), "ELYSIUM_icon.ico")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    engine = QQmlApplicationEngine()
    _configure_qml_engine_paths(engine)

    bridge = ElysiumBridge()
    engine.rootContext().setContextProperty("Elysium", bridge)

    main_qml = os.path.join(os.path.dirname(__file__), "ui", "qml", "main.qml")
    engine.load(QUrl.fromLocalFile(main_qml))
    if not engine.rootObjects():
        details = "\n".join(_qml_messages[-12:]) if _qml_messages else "No QML diagnostics captured."
        raise RuntimeError(
            "Failed to load QML shell.\n"
            f"File: {main_qml}\n"
            f"{details}\n\n"
            "If you see qtquick2plugin.dll errors on Windows, try:\n"
            "  pip install --upgrade PySide6==6.6.1 shiboken6==6.6.1\n"
            "Or set use_qml_ui to false in settings.json to use ELYSIUM.py."
        )

    return app, engine, bridge


def run_qml_app() -> int:
    app, engine, bridge = create_app()
    # Keep engine and bridge alive until the event loop exits.
    app._elysium_engine = engine  # type: ignore[attr-defined]
    app._elysium_bridge = bridge  # type: ignore[attr-defined]
    return app.exec()
