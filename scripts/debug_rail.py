import os, sys
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.getcwd())
from PySide6.QtCore import QUrl, QTimer, qInstallMessageHandler
from PySide6.QtWidgets import QApplication
import elysium.ui.qt_bootstrap
from elysium.app import _configure_qml_engine_paths
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

def log(m,c,msg): print("QML:", msg, flush=True)
qInstallMessageHandler(log)
app = QApplication(sys.argv)
engine = QQmlApplicationEngine()
_configure_qml_engine_paths(engine)
from elysium.ui.bridge import ElysiumBridge
engine.rootContext().setContextProperty("Elysium", ElysiumBridge())
path = os.path.abspath("elysium/ui/qml/components/SidebarRail.qml")
print("component create", flush=True)
c = QQmlComponent(engine, QUrl.fromLocalFile(path))
if c.isError():
    for e in c.errors(): print(e.toString())
    sys.exit(1)
o = c.create()
print("created", o is not None, flush=True)
QTimer.singleShot(5000, app.quit)
app.exec()
