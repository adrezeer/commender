"""
core/result.py
Unified result object returned by every command so the GUI can render it
without any command needing to know about Qt or the console.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResultLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    OUTPUT = "output"


@dataclass
class CommandResult:
    """Structured output of a command execution."""

    level: ResultLevel = ResultLevel.INFO
    text: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_prompt: str = ""

    @staticmethod
    def info(text: str, **data: Any) -> "CommandResult":
        return CommandResult(ResultLevel.INFO, text, data)

    @staticmethod
    def success(text: str, **data: Any) -> "CommandResult":
        return CommandResult(ResultLevel.SUCCESS, text, data)

    @staticmethod
    def error(text: str, **data: Any) -> "CommandResult":
        return CommandResult(ResultLevel.ERROR, text, data)

    @staticmethod
    def warning(text: str, **data: Any) -> "CommandResult":
        return CommandResult(ResultLevel.WARNING, text, data)

    @staticmethod
    def output(text: str, **data: Any) -> "CommandResult":
        return CommandResult(ResultLevel.OUTPUT, text, data)
