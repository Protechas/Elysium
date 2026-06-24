"""Subprocess creation flags for Windows."""

import subprocess


def no_window_flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)
