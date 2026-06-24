import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("1 create_app")
from elysium.app import create_app

app, engine, bridge = create_app(sys.argv)
print("2 roots", len(engine.rootObjects()))
for m in engine.rootObjects():
    print(" ", m, "visible:", getattr(m, "isVisible", lambda: "?")())
print("3 exec (close window to finish)")
app._elysium_engine = engine
app._elysium_bridge = bridge
sys.exit(app.exec())