"""
gui/theme.py
Central theme definition for Danrode Commander 0.1.0.
Dark glassmorphism only — light theme support is future-ready but unused.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    background: str = "#101114"
    glass: str = "rgba(255, 255, 255, 0.10)"
    glass_hover: str = "rgba(255, 255, 255, 0.14)"
    glass_pressed: str = "rgba(255, 255, 255, 0.07)"
    border: str = "rgba(255, 255, 255, 0.18)"
    border_soft: str = "rgba(255, 255, 255, 0.10)"
    accent: str = "#4DA3FF"
    accent_hover: str = "#6DB4FF"
    text: str = "#FFFFFF"
    text_dim: str = "rgba(255, 255, 255, 0.55)"
    text_faint: str = "rgba(255, 255, 255, 0.35)"
    success: str = "#4CD97B"
    error: str = "#FF6B6B"
    warning: str = "#FFC24D"

    font_family: str = '"Segoe UI Variable", "Segoe UI", sans-serif'


DARK = Theme()


def build_stylesheet(theme: Theme = DARK) -> str:
    """Global QSS applied at the application level."""
    return f"""
    * {{
        font-family: {theme.font_family};
        color: {theme.text};
        outline: none;
    }}

    QMainWindow, QDialog {{
        background: transparent;
    }}

    QWidget#RootPanel {{
        background-color: {theme.background};
        border-radius: 18px;
    }}

    QLabel#TitleLabel {{
        font-size: 15px;
        font-weight: 600;
        color: {theme.text};
        letter-spacing: 0.3px;
    }}

    QLabel#StatusLabel {{
        font-size: 12px;
        color: {theme.text_dim};
    }}

    QPushButton#AllCommandsButton {{
        background-color: {theme.glass};
        border: 1px solid {theme.border};
        border-radius: 14px;
        padding: 14px 20px;
        font-size: 14px;
        font-weight: 500;
        text-align: left;
        color: {theme.text};
    }}
    QPushButton#AllCommandsButton:hover {{
        background-color: {theme.glass_hover};
        border: 1px solid {theme.accent};
    }}
    QPushButton#AllCommandsButton:pressed {{
        background-color: {theme.glass_pressed};
    }}

    QLineEdit#CommandInput {{
        background-color: {theme.glass};
        border: 1px solid {theme.border};
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 14px;
        color: {theme.text};
    }}
    QLineEdit#CommandInput:focus {{
        border: 1px solid {theme.accent};
        background-color: {theme.glass_hover};
    }}

    QLineEdit#SearchInput {{
        background-color: {theme.glass};
        border: 1px solid {theme.border};
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 14px;
        color: {theme.text};
    }}
    QLineEdit#SearchInput:focus {{
        border: 1px solid {theme.accent};
    }}

    QWidget#GlassDialogPanel {{
        background-color: rgba(20, 21, 25, 0.92);
        border: 1px solid {theme.border};
        border-radius: 18px;
    }}

    QListWidget#CommandList {{
        background: transparent;
        border: none;
        font-size: 13px;
        padding: 4px;
    }}
    QListWidget#CommandList::item {{
        padding: 10px 12px;
        border-radius: 10px;
        margin: 2px 0px;
        color: {theme.text};
    }}
    QListWidget#CommandList::item:selected {{
        background-color: {theme.glass_hover};
        border: 1px solid {theme.accent};
    }}
    QListWidget#CommandList::item:hover {{
        background-color: {theme.glass};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {theme.border};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {theme.accent};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QWidget#StatusBar {{
        background-color: rgba(255, 255, 255, 0.04);
        border-top: 1px solid {theme.border_soft};
    }}

    QToolButton#CloseButton {{
        background: transparent;
        border: none;
        border-radius: 8px;
        color: {theme.text_dim};
        font-size: 13px;
    }}
    QToolButton#CloseButton:hover {{
        background-color: rgba(255, 90, 90, 0.25);
        color: white;
    }}

    QPlainTextEdit#OutputPanel {{
        background-color: {theme.glass};
        border: 1px solid {theme.border_soft};
        border-radius: 12px;
        padding: 10px;
        font-family: "Cascadia Code", "Consolas", monospace;
        font-size: 12.5px;
        color: {theme.text};
    }}
    """
