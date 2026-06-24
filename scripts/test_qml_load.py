"""Smoke-test QML shell load (dev helper)."""
from __future__ import annotations

import sys

from elysium.app import create_app


def main() -> int:
    app, engine, _bridge = create_app(sys.argv)
    count = len(engine.rootObjects())
    print(f"QML shell loaded ({count} root object(s))")
    return 0 if count else 1


if __name__ == "__main__":
    sys.exit(main())
