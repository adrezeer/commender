"""
core/logger.py
Lightweight application logger. Keeps a small in-memory ring buffer that the
GUI status bar / debug panel can subscribe to, plus optional file output.
"""

from __future__ import annotations

import datetime
import logging
import os
from collections import deque
from typing import Callable, Deque


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "history")
LOG_PATH = os.path.join(LOG_DIR, "dcmds.log")


class AppLogger:
    """Central logger with an in-memory buffer and subscriber callbacks."""

    def __init__(self, buffer_size: int = 500) -> None:
        os.makedirs(LOG_DIR, exist_ok=True)
        self._buffer: Deque[str] = deque(maxlen=buffer_size)
        self._subscribers: list[Callable[[str, str], None]] = []

        self._logger = logging.getLogger("DanrodeCommander")
        self._logger.setLevel(logging.DEBUG)
        if not self._logger.handlers:
            handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            self._logger.addHandler(handler)

    def subscribe(self, callback: Callable[[str, str], None]) -> None:
        """Callback receives (level, message)."""
        self._subscribers.append(callback)

    def _emit(self, level: str, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self._buffer.append(line)
        for cb in self._subscribers:
            try:
                cb(level, message)
            except Exception:
                pass

    def info(self, message: str) -> None:
        self._logger.info(message)
        self._emit("info", message)

    def success(self, message: str) -> None:
        self._logger.info(message)
        self._emit("success", message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)
        self._emit("warning", message)

    def error(self, message: str) -> None:
        self._logger.error(message)
        self._emit("error", message)

    @property
    def buffer(self) -> list[str]:
        return list(self._buffer)


# Single shared instance used across the app
logger = AppLogger()
