"""Load HomePage with real bridge after QApplication init."""
import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.getcwd())

from PySide6.QtCore import QUrl, QTimer, qInstallMessageHandler
from PySide6.QtWidgets import QApplication
import elysium.ui.qt_bootstrap  # noqa: F401
from elysium.app import _configure_qml_engine_paths
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent


def log(m, c, msg):
    print("QML:", msg, flush=True)


qInstallMessageHandler(log)
app = QApplication(sys.argv)
engine = QQmlApplicationEngine()
_configure_qml_engine_paths(engine)
from elysium.ui.bridge import ElysiumBridge

bridge = ElysiumBridge()
bridge._is_loading = False
engine.rootContext().setContextProperty("Elysium", bridge)

path = os.path.abspath("elysium/ui/qml/pages/HomePage.qml")
print("create HomePage", flush=True)
c = QQmlComponent(engine, QUrl.fromLocalFile(path))
if c.isError():
    for e in c.errors():
        print(e.toString())
    sys.exit(1)

container_qml = os.path.join(os.environ["TEMP"], "home_host.qml")
with open(container_qml, "w", encoding="utf-8") as f:
    f.write(
        "import QtQuick\nimport QtQuick.Controls\n"
        "ApplicationWindow { visible: true; width: 900; height: 700\n"
        "  Loader { anchors.fill: parent; source: 'file:///" + path.replace(chr(92), "/") + "' }\n}"
    )

engine.load(QUrl.fromLocalFile(container_qml))
print("roots", len(engine.rootObjects()), flush=True)
QTimer.singleShot(15000, app.quit)
print("exec...", flush=True)
sys.exit(app.exec())
