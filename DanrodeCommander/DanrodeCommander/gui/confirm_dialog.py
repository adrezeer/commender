"""
gui/confirm_dialog.py
Small glass confirmation dialog for destructive/safe-mode-gated actions
(delete, cleanup, shutdown, restart, sleep).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from gui.animations import open_animation
from gui.glass_panel import GlassPanel, make_frameless_translucent
from gui.theme import DARK


class ConfirmDialog(QDialog):
    def __init__(self, prompt: str, parent=None) -> None:
        super().__init__(parent)
        make_frameless_translucent(self)
        self.setModal(True)
        self.resize(400, 170)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._panel = GlassPanel("GlassDialogPanel", self)
        outer.addWidget(self._panel)

        layout = QVBoxLayout(self._panel)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(18)

        label = QLabel(prompt)
        label.setWordWrap(True)
        label.setStyleSheet(f"font-size: 14px; color: {DARK.text};")
        layout.addWidget(label, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK.glass};
                border: 1px solid {DARK.border};
                border-radius: 10px;
                padding: 9px 18px;
                color: {DARK.text};
            }}
            QPushButton:hover {{ background-color: {DARK.glass_hover}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK.accent};
                border: none;
                border-radius: 10px;
                padding: 9px 18px;
                color: white;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {DARK.accent_hover}; }}
        """)
        confirm_btn.clicked.connect(self.accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(confirm_btn)
        layout.addLayout(buttons)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        open_animation(self._panel)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
