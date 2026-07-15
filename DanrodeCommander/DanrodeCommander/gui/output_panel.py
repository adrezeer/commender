"""
gui/output_panel.py
Read-only text panel that renders CommandResult objects into readable text.
Kept intentionally simple for v0.1.0 — richer per-command rendering
(tables, process lists, etc.) can be layered on later without touching
the rest of the GUI.
"""

from __future__ import annotations

from PySide6.QtWidgets import QPlainTextEdit

from core.result import CommandResult, ResultLevel


class OutputPanel(QPlainTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("OutputPanel")
        self.setReadOnly(True)
        self.setMaximumBlockCount(2000)

    def append_result(self, command_text: str, result: CommandResult) -> None:
        prefix = {
            ResultLevel.INFO: "ℹ",
            ResultLevel.SUCCESS: "✓",
            ResultLevel.ERROR: "✗",
            ResultLevel.WARNING: "⚠",
            ResultLevel.OUTPUT: "➤",
        }.get(result.level, "•")

        self.appendPlainText(f"> {command_text}")
        if result.text:
            self.appendPlainText(f"{prefix} {result.text}")

        for key, value in result.data.items():
            if key in ("action", "name"):
                continue
            self.appendPlainText(self._format_field(key, value))

        self.appendPlainText("")
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def _format_field(self, key: str, value) -> str:
        if isinstance(value, list):
            if not value:
                return f"  {key}: (none)"
            preview = ", ".join(str(v) for v in value[:10])
            more = f" (+{len(value) - 10} more)" if len(value) > 10 else ""
            return f"  {key}: {preview}{more}"
        if isinstance(value, dict):
            return f"  {key}: {value}"
        return f"  {key}: {value}"
