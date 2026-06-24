"""Native Windows title bar theming via DWM."""

from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

from elysium.ui.theme import titlebar_colors

logger = logging.getLogger("Elysium.TitleBar")

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_USE_IMMERSIVE_DARK_MODE_LEGACY = 19
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36


def _colorref(hex_color: str) -> int:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return 0
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return (b << 16) | (g << 8) | r


def _dwm_set_int_attribute(hwnd: int, attribute: int, value: int) -> bool:
    try:
        attr = wintypes.DWORD(value)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(attribute),
            ctypes.byref(attr),
            ctypes.sizeof(attr),
        )
        return result == 0
    except Exception as exc:
        logger.debug("DwmSetWindowAttribute(%s) failed: %s", attribute, exc)
        return False


def apply_native_title_bar_theme(widget, dark: bool = True) -> None:
    """Apply dark/light native title bar colors on Windows 10/11."""
    if sys.platform != "win32":
        return

    try:
        hwnd = int(widget.winId())
    except Exception:
        return

    if hwnd <= 0:
        return

    dark_enabled = 1 if dark else 0
    if not _dwm_set_int_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, dark_enabled):
        _dwm_set_int_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_LEGACY, dark_enabled)

    caption, border, text = titlebar_colors(dark)
    _dwm_set_int_attribute(hwnd, DWMWA_CAPTION_COLOR, _colorref(caption))
    _dwm_set_int_attribute(hwnd, DWMWA_BORDER_COLOR, _colorref(border))
    _dwm_set_int_attribute(hwnd, DWMWA_TEXT_COLOR, _colorref(text))
