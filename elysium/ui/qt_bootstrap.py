"""Configure PySide6 DLL and plugin paths before any Qt imports (Windows)."""

from __future__ import annotations

import os
import sys


def configure_qt_runtime() -> None:
    """Ensure Qt/QML plugins resolve on Windows (especially Store Python)."""
    if sys.platform != "win32":
        return

    import PySide6

    root = os.path.dirname(os.path.abspath(PySide6.__file__))
    candidates = [
        root,
        os.path.join(root, "Qt", "bin"),
    ]

    path_entries: list[str] = []
    for folder in candidates:
        if os.path.isdir(folder):
            os.add_dll_directory(folder)
            path_entries.append(folder)

    plugins = os.path.join(root, "plugins")
    qml = os.path.join(root, "qml")
    platforms = os.path.join(plugins, "platforms")

    if os.path.isdir(plugins):
        os.environ.setdefault("QT_PLUGIN_PATH", plugins)
    if os.path.isdir(qml):
        os.environ.setdefault("QML2_IMPORT_PATH", qml)
    if os.path.isdir(platforms):
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", platforms)

    if path_entries:
        os.environ["PATH"] = os.pathsep.join(path_entries + [os.environ.get("PATH", "")])

    # Non-native style so Button/TextField background customization works in QML.
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

    fonts_dir = os.path.join(root, "lib", "fonts")
    if not os.path.isdir(fonts_dir):
        win_fonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        if os.path.isdir(win_fonts):
            try:
                os.makedirs(fonts_dir, exist_ok=True)
                for name in ("segoeui.ttf", "segoeuib.ttf", "arial.ttf"):
                    src = os.path.join(win_fonts, name)
                    dst = os.path.join(fonts_dir, name)
                    if os.path.isfile(src) and not os.path.exists(dst):
                        import shutil

                        shutil.copy2(src, dst)
            except OSError:
                pass


# Run immediately on import so early Qt users are covered.
configure_qt_runtime()
