"""
core/plugin_manager.py
Loads legacy-style plugins from the plugins/ directory.
A plugin is any .py file exposing a `register(register_command)` function,
exactly like the original DCMDS plugin API.
"""

from __future__ import annotations

import importlib.util
import os
from typing import Callable, Dict, List

from core.logger import logger


PluginHandler = Callable[[List[str], str], None]


class PluginManager:
    def __init__(self, plugins_dir: str) -> None:
        self._plugins_dir = plugins_dir
        self._commands: Dict[str, PluginHandler] = {}
        self._command_help: Dict[str, str] = {}
        self._loaded: List[str] = []

    def _register_command(self, name: str, handler: PluginHandler, description: str = "") -> None:
        self._commands[name.lower()] = handler
        if description:
            self._command_help[name.lower()] = description

    def load_all(self) -> None:
        if not os.path.isdir(self._plugins_dir):
            return
        for filename in os.listdir(self._plugins_dir):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            path = os.path.join(self._plugins_dir, filename)
            mod_name = f"plugin_{os.path.splitext(filename)[0]}"
            try:
                spec = importlib.util.spec_from_file_location(mod_name, path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "register"):
                        mod.register(self._register_command)
                    self._loaded.append(filename)
            except Exception as e:
                logger.error(f"Plugin load failed ({filename}): {e}")

    @property
    def commands(self) -> Dict[str, PluginHandler]:
        return self._commands

    @property
    def command_help(self) -> Dict[str, str]:
        return self._command_help

    @property
    def loaded(self) -> List[str]:
        return list(self._loaded)

    def has_command(self, name: str) -> bool:
        return name.lower() in self._commands

    def execute(self, name: str, args: List[str], raw: str) -> None:
        self._commands[name.lower()](args, raw)
