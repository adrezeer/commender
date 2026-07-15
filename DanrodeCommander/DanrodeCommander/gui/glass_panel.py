"""
gui/glass_panel.py
Reusable frameless, rounded, shadowed "glass" panel used as the base
container for the main window and dialogs.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QVBoxLayout, QWidget


class GlassPanel(QWidget):
    """A rounded translucent panel with a soft drop shadow.

    Intended to be the single top-level child of a frameless window so the
    window itself can stay fully transparent while this widget draws the
    visible rounded/glass surface.
    """

    def __init__(self, object_name: str = "RootPanel", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self._apply_shadow()

    def _apply_shadow(self) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(48)
        shadow.setXOffset(0)
        shadow.setYOffset(12)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)


def make_frameless_translucent(window) -> None:
    """Apply the standard frameless/translucent flags used by our top-level windows."""
    window.setWindowFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowSystemMenuHint
        | Qt.WindowType.WindowMinMaxButtonsHint
    )
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
