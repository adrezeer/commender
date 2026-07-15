"""
main.py
Entry point for Danrode Commander 0.1.0.

Kept intentionally tiny: build the Qt application, wire the theme,
construct the CommandManager (backend) and MainWindow (GUI), run.
"""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

from core.command_manager import CommandManager  # noqa: E402
from gui.main_window import MainWindow  # noqa: E402
from gui.theme import DARK, build_stylesheet  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Danrode Commander")
    app.setStyleSheet(build_stylesheet(DARK))

    manager = CommandManager(APP_DIR)
    window = MainWindow(manager)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
