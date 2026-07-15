"""
commands/power.py
Power control commands. Caller (GUI) must confirm with the user first —
these functions perform the action immediately when called.
"""

from __future__ import annotations

import os

from core.result import CommandResult


def shutdown(delay_seconds: int = 10) -> CommandResult:
    try:
        os.system(f"shutdown /s /t {delay_seconds}")
        return CommandResult.success(f"Shutdown initiated in {delay_seconds}s")
    except Exception as e:
        return CommandResult.error(f"Failed to shutdown: {e}")


def restart(delay_seconds: int = 10) -> CommandResult:
    try:
        os.system(f"shutdown /r /t {delay_seconds}")
        return CommandResult.success(f"Restart initiated in {delay_seconds}s")
    except Exception as e:
        return CommandResult.error(f"Failed to restart: {e}")


def sleep() -> CommandResult:
    try:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return CommandResult.success("Going to sleep mode...")
    except Exception as e:
        return CommandResult.error(f"Failed to sleep: {e}")


def cancel_scheduled_shutdown() -> CommandResult:
    try:
        os.system("shutdown /a")
        return CommandResult.success("Scheduled shutdown/restart cancelled")
    except Exception as e:
        return CommandResult.error(f"Failed to cancel: {e}")
