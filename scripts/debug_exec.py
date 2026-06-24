"""Full init path smoke test."""
import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.getcwd())

from PySide6.QtCore import QTimer
import elysium.ui.qt_bootstrap  # noqa: F401
from elysium.ui import bridge as bridge_mod

bridge_mod.apply_native_title_bar_theme = lambda *a, **k: None  # type: ignore[assignment]

from elysium.app import create_app

app, engine, bridge = create_app(sys.argv)
QTimer.singleShot(25000, app.quit)
print("full init path, 25s...", flush=True)
code = app.exec()
print("returned", code, flush=True)
