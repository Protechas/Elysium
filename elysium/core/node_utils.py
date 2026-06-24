"""Node.js detection helpers."""

from __future__ import annotations

import os
import shutil


def find_nodejs_bin_dir() -> str | None:
    npm_path = shutil.which("npm")
    if npm_path:
        return os.path.dirname(os.path.abspath(npm_path))

    candidates = [
        r"C:\Program Files\nodejs",
        r"C:\Program Files (x86)\nodejs",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "node"),
        os.path.join(os.path.expanduser("~"), "nodejs"),
    ]

    for candidate in candidates:
        if os.path.exists(os.path.join(candidate, "npm.cmd")):
            return candidate
        if os.path.isdir(candidate):
            try:
                for entry in os.listdir(candidate):
                    subdir = os.path.join(candidate, entry)
                    if os.path.isdir(subdir) and os.path.exists(os.path.join(subdir, "npm.cmd")):
                        return subdir
            except OSError:
                continue
    return None


def ensure_nodejs_path(env: dict[str, str]) -> bool:
    node_dir = find_nodejs_bin_dir()
    if not node_dir:
        return False
    current = env.get("PATH", "")
    if node_dir.lower() not in current.lower():
        env["PATH"] = node_dir + os.pathsep + current
    return True
