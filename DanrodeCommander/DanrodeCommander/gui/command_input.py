"""
gui/command_input.py
Bottom command input field: history navigation (Up/Down), autocomplete,
placeholder text, and Enter-to-execute.
"""

from __future__ import annotations

from typing import Callable, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCompleter, QLineEdit


class CommandInput(QLineEdit):
    commandSubmitted = Signal(str)

    def __init__(
        self,
        history_previous: Callable[[], str | None],
        history_next: Callable[[], str | None],
        history_reset: Callable[[], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CommandInput")
        self.setPlaceholderText("> Type command...")
        self.setClearButtonEnabled(False)

        self._history_previous = history_previous
        self._history_next = history_next
        self._history_reset = history_reset

        self.returnPressed.connect(self._on_submit)

    def set_autocomplete_words(self, words: List[str]) -> None:
        completer = QCompleter(words, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.InlineCompletion)
        self.setCompleter(completer)

    def _on_submit(self) -> None:
        text = self.text().strip()
        if not text:
            return
        self.commandSubmitted.emit(text)
        self.clear()
        self._history_reset()

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.key() == Qt.Key.Key_Up:
            prev = self._history_previous()
            if prev is not None:
                self.setText(prev)
                self.end(False)
            return
        if event.key() == Qt.Key.Key_Down:
            nxt = self._history_next()
            if nxt is not None:
                self.setText(nxt)
                self.end(False)
            return
        super().keyPressEvent(event)
