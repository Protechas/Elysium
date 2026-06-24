"""Shared design tokens for PyQt5 fallback and QML UI."""

from __future__ import annotations

UI_FONT = "Segoe UI"

THEME_DARK = {
    "bg_top": "#0a0f18",
    "bg_bottom": "#05070b",
    "surface": "#0f1623",
    "surface_hover": "#151f30",
    "surface_elevated": "#121c2b",
    "card_top": "#172231",
    "card_bottom": "#101822",
    "border": "#1e2a3d",
    "border_active": "#3ee0cf",
    "accent": "#3ee0cf",
    "accent_muted": "#0d9488",
    "text": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
}

THEME_LIGHT = {
    "bg_top": "#f8fafc",
    "bg_bottom": "#eef2f7",
    "surface": "#ffffff",
    "surface_hover": "#f8fafc",
    "surface_elevated": "#ffffff",
    "card_top": "#ffffff",
    "card_bottom": "#f1f5f9",
    "border": "#dbe3ee",
    "border_active": "#0d9488",
    "accent": "#0d9488",
    "accent_muted": "#14b8a6",
    "text": "#0f172a",
    "text_secondary": "#475569",
    "text_muted": "#64748b",
}

STATUS_STYLES = {
    "Ready": ("#14532d", "#4ade80"),
    "Loading": ("#1e293b", "#94a3b8"),
    "Updating": ("#78350f", "#fbbf24"),
    "Failed": ("#7f1d1d", "#f87171"),
    "Needs Node": ("#7c2d12", "#fb923c"),
    "Not installed": ("#334155", "#94a3b8"),
}

APP_CARD_PADDING = 10
APP_GRID_SPACING_H = 22
APP_GRID_SPACING_V = 20
APP_CARD_HEIGHT = 168
APP_CARD_WIDTH = 128
APP_GRID_COLUMNS = 3


def get_theme(dark: bool = True) -> dict[str, str]:
    return THEME_DARK if dark else THEME_LIGHT


def titlebar_colors(dark: bool = True) -> tuple[str, str, str]:
    t = get_theme(dark)
    return t["bg_top"], t["border"], t["text"]


def status_colors(status_text: str) -> tuple[str, str]:
    return STATUS_STYLES.get(status_text, ("#1e293b", "#94a3b8"))


def apps_grid_minimum_size(app_count: int, columns: int = APP_GRID_COLUMNS) -> tuple[int, int]:
    rows = max(1, (app_count + columns - 1) // columns)
    height = (
        (rows * APP_CARD_HEIGHT)
        + (max(0, rows - 1) * APP_GRID_SPACING_V)
        + (APP_CARD_PADDING * 2)
    )
    width = (
        (columns * APP_CARD_WIDTH)
        + (max(0, columns - 1) * APP_GRID_SPACING_H)
        + (APP_CARD_PADDING * 2)
    )
    return width, height


def build_scroll_stylesheet(dark: bool = True) -> str:
    t = get_theme(dark)
    return f"""
        QScrollArea#appsScroll {{
            background: transparent;
            border: none;
        }}
        QWidget#appsScrollViewport {{
            background-color: {t['surface']};
            border: none;
        }}
        QWidget#appsGridHost {{
            background: transparent;
        }}
    """


def build_main_stylesheet(dark: bool = True) -> str:
    t = get_theme(dark)
    panel_bg = (
        f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['surface_elevated']}, stop:1 {t['surface']})"
    )
    return f"""
        QWidget#elysiumMain {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {t['bg_top']}, stop:1 {t['bg_bottom']}
            );
            color: {t['text']};
            font-family: "{UI_FONT}";
            font-size: 13px;
        }}
        QFrame#headerFrame, QFrame#appsFrame, QFrame#footerFrame {{
            background: {panel_bg};
            border: 1px solid {t['border']};
            border-radius: 12px;
        }}
        QLabel#headerTitle {{
            font-size: 26px;
            font-weight: 700;
            color: {t['accent']};
            letter-spacing: 3px;
        }}
        QLabel#headerSubtitle {{
            font-size: 13px;
            color: {t['text_secondary']};
        }}
        QLabel#versionBadge {{
            font-size: 11px;
            color: {t['text_muted']};
            background-color: {t['bg_bottom'] if dark else '#eef2f7'};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 4px 10px;
        }}
        QLabel#statusLabel {{
            color: {t['text_muted']};
            font-size: 11px;
            letter-spacing: 0.3px;
        }}
        QProgressBar {{
            border: none;
            border-radius: 4px;
            background-color: {t['border'] if dark else '#e2e8f0'};
            min-height: 6px;
            max-height: 6px;
        }}
        QProgressBar::chunk {{
            background-color: {t['accent']};
            border-radius: 4px;
        }}
        QPushButton#primaryButton {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {t['accent_muted']}, stop:1 {t['accent']}
            );
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: 600;
            min-height: 36px;
        }}
        QPushButton#primaryButton:hover {{
            background: {t['accent']};
        }}
        QPushButton#secondaryButton {{
            background-color: {t['surface_hover']};
            color: {t['text_secondary']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 8px 14px;
            min-height: 36px;
        }}
        QPushButton#secondaryButton:hover {{
            border-color: {t['accent_muted']};
            color: {t['accent']};
            background-color: {t['surface_elevated']};
        }}
    """
