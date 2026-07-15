"""
core/history.py
Command history manager - fully compatible with the legacy history.log format
(plain newline-separated commands).
"""

from __future__ import annotations

import os
from typing import List

from core.config import ConfigManager


class HistoryManager:
    """Tracks executed commands, persisted to history.log."""

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._entries: List[str] = []
        self._cursor: int = 0
        self.load()

    def load(self) -> None:
        if not self._config.get("history_enabled", True):
            return
        path = self._config.get("history_path")
        self._entries.clear()
        try:
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if line:
                            self._entries.append(line)
        except Exception:
            pass
        self._cursor = len(self._entries)

    def add(self, command: str) -> None:
        if not self._config.get("history_enabled", True):
            return
        self._entries.append(command)
        max_len = int(self._config.get("history_max", 200))
        if max_len > 0 and len(self._entries) > max_len:
            self._entries.pop(0)
        self._cursor = len(self._entries)

        path = self._config.get("history_path")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(command + "\n")
        except Exception:
            pass

    def clear(self) -> None:
        self._entries.clear()
        self._cursor = 0
        path = self._config.get("history_path")
        try:
            with open(path, "w", encoding="utf-8"):
                pass
        except Exception:
            pass

    def all(self) -> List[str]:
        return list(self._entries)

    def previous(self) -> str | None:
        """Move cursor back (older command), for Up arrow support."""
        if not self._entries:
            return None
        self._cursor = max(0, self._cursor - 1)
        return self._entries[self._cursor]

    def next(self) -> str | None:
        """Move cursor forward (newer command), for Down arrow support."""
        if not self._entries:
            return None
        self._cursor = min(len(self._entries), self._cursor + 1)
        if self._cursor >= len(self._entries):
            return ""
        return self._entries[self._cursor]

    def reset_cursor(self) -> None:
        self._cursor = len(self._entries)
