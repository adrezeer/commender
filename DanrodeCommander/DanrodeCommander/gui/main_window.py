"""
gui/main_window.py
Main window of Danrode Commander 0.1.0.

Layout is intentionally minimal:
  1. Title ("Danrode Commander") + status text
  2. One large "All Commands" button
  3. Command input at the bottom
  4. A slim status bar

No sidebar, no ribbon, no toolbar.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.command_manager import CommandManager
from core.result import CommandResult
from gui.animations import fade_in
from gui.command_dialog import CommandDialog
from gui.command_input import CommandInput
from gui.confirm_dialog import ConfirmDialog
from gui.glass_panel import GlassPanel, make_frameless_translucent
from gui.output_panel import OutputPanel
from gui.status_bar import StatusBar
from gui.theme import DARK


class MainWindow(QMainWindow):
    def __init__(self, command_manager: CommandManager) -> None:
        super().__init__()
        self.manager = command_manager
        self._drag_pos: QPoint | None = None

        self.setWindowTitle("Danrode Commander")
        make_frameless_translucent(self)
        self.resize(1100, 700)

        self._build_ui()
        self.manager.on_status(self._on_manager_status)

    # ---------------------------------------------------------------- UI

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("CentralHost")
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 16, 16, 16)

        self.panel = GlassPanel("RootPanel", central)
        outer.addWidget(self.panel)
        self.setCentralWidget(central)

        root = QVBoxLayout(self.panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_titlebar())
        root.addLayout(self._build_body(), 1)
        root.addWidget(self._build_status_bar())

    def _build_titlebar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setObjectName("TitleBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 12, 0)

        title = QLabel("Danrode Commander")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        for symbol, handler in (("—", self.showMinimized), ("✕", self.close)):
            btn = QToolButton()
            btn.setObjectName("CloseButton")
            btn.setText(symbol)
            btn.setFixedSize(32, 32)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        bar.mousePressEvent = self._titlebar_mouse_press
        bar.mouseMoveEvent = self._titlebar_mouse_move
        return bar

    def _build_body(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 8, 28, 20)
        layout.setSpacing(16)

        self.output_panel = OutputPanel()
        layout.addWidget(self.output_panel, 1)

        self.all_commands_btn = QPushButton("All Commands")
        self.all_commands_btn.setObjectName("AllCommandsButton")
        self.all_commands_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.all_commands_btn.setFixedHeight(52)
        self.all_commands_btn.clicked.connect(self._open_command_dialog)
        layout.addWidget(self.all_commands_btn)

        self.command_input = CommandInput(
            history_previous=self.manager.history.previous,
            history_next=self.manager.history.next,
            history_reset=self.manager.history.reset_cursor,
        )
        self.command_input.set_autocomplete_words(self.manager.all_command_names())
        self.command_input.commandSubmitted.connect(self._run_command)
        self.command_input.setFixedHeight(48)
        layout.addWidget(self.command_input)

        return layout

    def _build_status_bar(self) -> QWidget:
        self.status_bar = StatusBar()
        return self.status_bar

    # ------------------------------------------------------- interactions

    def _open_command_dialog(self) -> None:
        from core.command_manager import COMMAND_REGISTRY

        dialog = CommandDialog(COMMAND_REGISTRY, self)
        dialog.commandChosen.connect(self._on_command_chosen)
        dialog.exec()

    def _on_command_chosen(self, name: str) -> None:
        from core.command_manager import COMMAND_REGISTRY

        spec = next((c for c in COMMAND_REGISTRY if name in c.names), None)
        if spec and spec.requires_arg:
            self.command_input.setText(f"{name} ")
            self.command_input.setFocus()
            return
        self._run_command(name)

    def _run_command(self, text: str) -> None:
        result = self.manager.execute(text)

        if result.requires_confirmation:
            dialog = ConfirmDialog(result.confirmation_prompt, self)
            if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
                action = result.data.get("action", "")
                final = self.manager.confirmed_execute(action, result.data)
                self.output_panel.append_result(text, final)
            else:
                self.output_panel.append_result(text, CommandResult.info("Cancelled"))
            return

        self.output_panel.append_result(text, result)

        # current_path may have changed — nothing else to sync in v0.1.0's
        # minimal layout, but future panels (breadcrumb, explorer) hook here.

    def _on_manager_status(self, text: str) -> None:
        tone = "busy" if text == "Executing..." else "success"
        self.status_bar.set_status(text, tone, auto_reset_ms=0)

    # ------------------------------------------------------- window drag

    def _titlebar_mouse_press(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _titlebar_mouse_move(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        fade_in(self.panel, duration=220)
