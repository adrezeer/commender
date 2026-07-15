"""
gui/status_bar.py
Minimal bottom status bar. Shows a single line of state:
Ready / Executing... / Finished / Plugin Loaded / etc.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from gui.theme import DARK


class StatusBar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)

        self._dot = QLabel("●")
        self._dot.setStyleSheet(f"color: {DARK.success}; font-size: 10px;")

        self._label = QLabel("Ready")
        self._label.setObjectName("StatusLabel")

        layout.addWidget(self._dot)
        layout.addSpacing(8)
        layout.addWidget(self._label)
        layout.addStretch(1)

        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._reset_to_ready)

    def set_status(self, text: str, tone: str = "info", auto_reset_ms: int = 0) -> None:
        color = {
            "info": DARK.text_dim,
            "success": DARK.success,
            "error": DARK.error,
            "warning": DARK.warning,
            "busy": DARK.accent,
        }.get(tone, DARK.text_dim)

        self._dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        self._label.setText(text)

        if auto_reset_ms > 0:
            self._reset_timer.start(auto_reset_ms)

    def _reset_to_ready(self) -> None:
        self.set_status("Ready", "success")
