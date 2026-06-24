"""Elysium QML entry point."""

from __future__ import annotations

import os
import subprocess
import sys

# Allow running this file directly (e.g. VS Code) as well as `python -m elysium.main`.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Configure Qt DLL paths before any PySide6 import chain.
import elysium.ui.qt_bootstrap  # noqa: F401
from elysium.app import run_qml_app
from elysium.core.paths import get_base_dir


def _run_legacy_fallback() -> int:
    elysium_py = os.path.join(get_base_dir(), "ELYSIUM.py")
    if not os.path.isfile(elysium_py):
        print(f"Legacy UI not found: {elysium_py}", file=sys.stderr)
        return 1
    print("QML UI unavailable — starting classic ELYSIUM.py...", file=sys.stderr)
    env = os.environ.copy()
    env["ELYSIUM_FORCE_LEGACY"] = "1"
    return subprocess.call([sys.executable, elysium_py], env=env)


def main() -> int:
    try:
        return run_qml_app()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return _run_legacy_fallback()


if __name__ == "__main__":
    sys.exit(main())
