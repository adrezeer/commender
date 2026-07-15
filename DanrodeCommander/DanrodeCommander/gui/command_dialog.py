"""
gui/command_dialog.py
Floating glass "All Commands" dialog: search bar + scrollable, instantly
filtered command list. Arrow keys to navigate, Enter to execute, Escape
to close, mouse click also supported.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from core.command_manager import CommandSpec
from gui.animations import open_animation
from gui.glass_panel import GlassPanel, make_frameless_translucent
from gui.theme import DARK


class CommandDialog(QDialog):
    commandChosen = Signal(str)

    def __init__(self, commands: List[CommandSpec], parent=None) -> None:
        super().__init__(parent)
        self._commands = commands
        make_frameless_translucent(self)
        self.setModal(True)
        self.resize(560, 480)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._panel = GlassPanel("GlassDialogPanel", self)
        outer.addWidget(self._panel)

        layout = QVBoxLayout(self._panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("Search command...")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setObjectName("CommandList")
        self._list.itemActivated.connect(self._activate_item)
        self._list.itemClicked.connect(self._activate_item)
        layout.addWidget(self._list, 1)

        self._populate(self._commands)
        self._search.setFocus()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        open_animation(self._panel)

    def _populate(self, commands: List[CommandSpec]) -> None:
        self._list.clear()
        for spec in commands:
            item = QListWidgetItem(f"{spec.icon}   {spec.display}   —   {spec.description}")
            item.setData(Qt.ItemDataRole.UserRole, spec.names[0])
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _filter(self, text: str) -> None:
        text = text.strip().lower()
        if not text:
            self._populate(self._commands)
            return
        matches = [
            c for c in self._commands
            if text in c.display.lower()
            or text in c.description.lower()
            or any(text in n.lower() for n in c.names)
        ]
        self._populate(matches)

    def _activate_item(self, item: QListWidgetItem) -> None:
        name: Optional[str] = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.commandChosen.emit(name)
            self.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        if key == Qt.Key.Key_Down:
            row = min(self._list.currentRow() + 1, self._list.count() - 1)
            self._list.setCurrentRow(row)
            return
        if key == Qt.Key.Key_Up:
            row = max(self._list.currentRow() - 1, 0)
            self._list.setCurrentRow(row)
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            item = self._list.currentItem()
            if item:
                self._activate_item(item)
            return
        super().keyPressEvent(event)
