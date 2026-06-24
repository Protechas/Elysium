"""Debug ELYSIUM.py QML launch (dev only)."""
import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.getcwd())

print("Step 1: deps")
# minimal import chain
import importlib.util
spec = importlib.util.spec_from_file_location("elysium_entry", "ELYSIUM.py")
# Instead run pieces manually
from elysium.core.settings import load_settings
print("  use_qml_ui:", load_settings().get("use_qml_ui", True))
print("  FORCE_LEGACY:", os.environ.get("ELYSIUM_FORCE_LEGACY"))

print("Step 2: create_app")
import elysium.ui.qt_bootstrap  # noqa: F401
from elysium.app import create_app

app, engine, bridge = create_app(sys.argv)
print("  rootObjects:", len(engine.rootObjects()))
for obj in engine.rootObjects():
    print("  root:", obj, "visible:", getattr(obj, "isVisible", lambda: "?")())

print("Step 3: exec (close window to finish)")
app._elysium_engine = engine
app._elysium_bridge = bridge
code = app.exec()
print("Step 4: exec returned", code)
