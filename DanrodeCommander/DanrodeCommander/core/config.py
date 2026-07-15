"""
core/config.py
Configuration manager for Danrode Commander.
Keeps full backward compatibility with the original DCMDS config.json format.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any


APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(APP_DIR, "config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
HISTORY_DIR = os.path.join(APP_DIR, "history")
HISTORY_PATH = os.path.join(HISTORY_DIR, "history.log")

DEFAULT_DPA_KEY = "DanrodeDefaultKey2024"


@dataclass
class AppConfig:
    """Typed view over the legacy config.json structure."""

    safe_mode: bool = True
    theme: str = "dark"
    history_enabled: bool = True
    history_max: int = 200
    history_path: str = HISTORY_PATH
    dpa_key: str = DEFAULT_DPA_KEY

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConfigManager:
    """Loads, saves, and exposes application configuration."""

    def __init__(self, path: str = CONFIG_PATH) -> None:
        self._path = path
        self._data: dict[str, Any] = {}
        self._ensure_defaults()
        self.load()

    def _ensure_defaults(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        os.makedirs(HISTORY_DIR, exist_ok=True)
        if not os.path.exists(self._path):
            self._data = AppConfig().to_dict()
            self.save()

    def load(self) -> AppConfig:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            self._data = AppConfig().to_dict()

        defaults = AppConfig().to_dict()
        for key, value in defaults.items():
            self._data.setdefault(key, value)

        if not os.path.isabs(self._data["history_path"]):
            self._data["history_path"] = os.path.join(APP_DIR, self._data["history_path"])

        return self.as_config()

    def save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def as_config(self) -> AppConfig:
        return AppConfig(**{k: self._data.get(k, v) for k, v in AppConfig().to_dict().items()})

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    @property
    def raw(self) -> dict[str, Any]:
        return self._data
