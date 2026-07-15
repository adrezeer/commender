"""
core/command_manager.py
Central command registry + dispatcher.

This is the single entry point the GUI talks to: `CommandManager.execute(text)`.
It owns application state that used to be module-level globals in the legacy
script (current_path, camera session, etc.) and routes text commands to the
appropriate function in commands/.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from commands import calc_cmd, camera_cmd, dpa_cmd, filesystem, power, system_info
from core.config import ConfigManager
from core.history import HistoryManager
from core.logger import logger
from core.plugin_manager import PluginManager
from core.result import CommandResult


@dataclass
class CommandSpec:
    """One entry in the command palette ('All Commands' dialog)."""

    names: List[str]
    display: str
    description: str
    icon: str = "•"
    requires_arg: bool = False


# The canonical command list shown in the "All Commands" search dialog.
# Kept as data so the GUI never has to hardcode strings.
COMMAND_REGISTRY: List[CommandSpec] = [
    CommandSpec(["bc"], "bc", "Show all available drives", "💾"),
    CommandSpec(["cd"], "cd <folder>", "Enter specified folder", "📂"),
    CommandSpec([".."], "..", "Go back to parent folder", "⬆️"),
    CommandSpec(["ls"], "ls", "List files and folders", "📋"),
    CommandSpec(["tree"], "tree", "Display directory tree", "🌳"),
    CommandSpec(["tasks"], "tasks", "Show running processes", "⚙️"),
    CommandSpec(["end"], "end <pid>", "End task by PID", "❌", requires_arg=True),
    CommandSpec(["restart"], "restart <pid>", "Restart task by PID", "🔄", requires_arg=True),
    CommandSpec(["wifi"], "wifi", "Scan available WiFi networks", "📡"),
    CommandSpec(["wifipass"], "wifipass <name>", "Show saved WiFi password", "🔑", requires_arg=True),
    CommandSpec(["ip"], "ip", "Show network information", "🌐"),
    CommandSpec(["copy"], "copy <src> <dst>", "Copy a file", "📋", requires_arg=True),
    CommandSpec(["move"], "move <src> <dst>", "Move a file", "🚚", requires_arg=True),
    CommandSpec(["rename"], "rename <old> <new>", "Rename a file", "✏️", requires_arg=True),
    CommandSpec(["search"], "search <pattern>", "Search files by pattern", "🔍", requires_arg=True),
    CommandSpec(["info"], "info <file>", "Show file information", "ℹ️", requires_arg=True),
    CommandSpec(["cleanup"], "cleanup", "Clean temporary files", "🧹"),
    CommandSpec(["create"], "create <file>", "Create a new file", "✨", requires_arg=True),
    CommandSpec(["delete"], "delete <file>", "Delete a file", "🗑️", requires_arg=True),
    CommandSpec(["calc"], "calc <expr>", "Evaluate a math expression", "🧮", requires_arg=True),
    CommandSpec(["camera"], "camera", "Open camera preview", "📷"),
    CommandSpec(["take"], "take", "Take a photo", "📸"),
    CommandSpec(["vid"], "vid", "Start video recording", "🎥"),
    CommandSpec(["endvid"], "endvid", "Stop video recording", "⏹️"),
    CommandSpec(["debug"], "debug", "System diagnostics", "🔧"),
    CommandSpec(["dpa"], "dpa <file>", "Run a .dpa file", "🔐", requires_arg=True),
    CommandSpec(["encrypt"], "encrypt <file.py>", "Encrypt a .py into .dpa", "🔒", requires_arg=True),
    CommandSpec(["decrypt"], "decrypt <file.dpa>", "Decrypt a .dpa file", "🔓", requires_arg=True),
    CommandSpec(["shutdown"], "shutdown", "Shutdown computer", "🔴"),
    CommandSpec(["sleep"], "sleep", "Put computer to sleep", "😴"),
    CommandSpec(["restartsys"], "restart", "Restart computer", "🔄"),
    CommandSpec(["theme"], "theme", "List/set UI theme", "🎨"),
    CommandSpec(["safe"], "safe", "Toggle safe mode", "🛡️"),
    CommandSpec(["plugins"], "plugins", "List loaded plugins", "🧩"),
    CommandSpec(["history"], "history", "Show recent commands", "🧾"),
    CommandSpec(["help"], "help [command]", "Show help", "📚"),
]

SAFE_COMMANDS = {"shutdown", "restart", "restartsys", "sleep", "delete", "cleanup"}


@dataclass
class AppState:
    """Mutable state that used to be module-level globals in the legacy script."""

    current_path: Optional[str] = None
    web_mode: bool = False
    current_url: Optional[str] = None
    active_app: Optional[str] = None


class CommandManager:
    """Routes command strings to their handlers and owns app state."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        self.config = ConfigManager()
        self.history = HistoryManager(self.config)
        self.plugins = PluginManager(os.path.join(base_dir, "plugins"))
        self.plugins.load_all()
        self.state = AppState()
        self.camera = camera_cmd.CameraSession()
        self._status_callbacks: List[Callable[[str], None]] = []

    # ---- status wiring for the GUI status bar ----
    def on_status(self, callback: Callable[[str], None]) -> None:
        self._status_callbacks.append(callback)

    def _set_status(self, text: str) -> None:
        for cb in self._status_callbacks:
            try:
                cb(text)
            except Exception:
                pass

    # ---- safe mode gate ----
    def is_blocked(self, key: str) -> bool:
        return self.config.get("safe_mode", True) and key in SAFE_COMMANDS

    # ---- main dispatch ----
    def execute(self, raw_command: str) -> CommandResult:
        raw_command = raw_command.strip()
        if not raw_command:
            return CommandResult.info("")

        self.history.add(raw_command)
        self._set_status("Executing...")

        try:
            result = self._dispatch(raw_command)
        except Exception as e:
            logger.error(f"Command failed: {e}")
            result = CommandResult.error(f"Unexpected error: {e}")

        self._set_status("Ready")
        return result

    def _dispatch(self, cmd: str) -> CommandResult:
        lower = cmd.lower()
        parts = cmd.split()
        first = parts[0].lower() if parts else ""

        # Drive navigation
        if lower == "bc":
            drives = filesystem.list_drives()
            return CommandResult.output("Available drives", drives=drives)

        if len(cmd) == 1 and cmd.upper() + ":\\" in filesystem.list_drives():
            self.state.current_path = cmd.upper() + ":\\"
            return CommandResult.success(f"Current path set to: {self.state.current_path}")

        if lower.startswith("cd "):
            res = filesystem.change_directory(self.state.current_path, cmd[3:].strip())
            if res.level.value == "success":
                self.state.current_path = res.data["new_path"]
            return res

        if cmd == "..":
            res = filesystem.go_back(self.state.current_path)
            if res.level.value == "success":
                self.state.current_path = res.data["new_path"]
            return res

        if lower == "cdt":
            if self.state.current_path:
                return CommandResult.info(f"Current path: {self.state.current_path}")
            return CommandResult.error("No path selected")

        if lower == "ls":
            return filesystem.list_items(self.state.current_path)

        if lower == "tree":
            return filesystem.directory_tree(self.state.current_path)

        # Tasks
        if lower == "tasks":
            return system_info.get_tasks()
        if first == "end" and len(parts) > 1:
            if self.is_blocked("delete"):
                return CommandResult.warning("Safe mode is ON. Use 'safe off' to enable this command.")
            if parts[1].isdigit():
                return system_info.end_task(int(parts[1]))
            return CommandResult.error("Invalid PID. Must be a number.")
        if first == "restart" and len(parts) > 1 and parts[1].isdigit():
            if self.is_blocked("delete"):
                return CommandResult.warning("Safe mode is ON. Use 'safe off' to enable this command.")
            return system_info.restart_task(int(parts[1]))

        # Network
        if lower == "wifi":
            return system_info.scan_wifi()
        if lower.startswith("wifipass "):
            return system_info.wifi_password(cmd[9:].strip())
        if lower == "ip":
            return system_info.get_ip_info()

        # File ops
        if lower.startswith("copy "):
            args = cmd[5:].strip().split(maxsplit=1)
            if len(args) == 2:
                return filesystem.copy_file(*self._resolve_pair(args))
            return CommandResult.error("Usage: copy <source> <destination>")

        if lower.startswith("move "):
            args = cmd[5:].strip().split(maxsplit=1)
            if len(args) == 2:
                return filesystem.move_file(*self._resolve_pair(args))
            return CommandResult.error("Usage: move <source> <destination>")

        if lower.startswith("rename "):
            args = cmd[7:].strip().split(maxsplit=1)
            if len(args) == 2:
                return filesystem.rename_file(*self._resolve_pair(args))
            return CommandResult.error("Usage: rename <old_name> <new_name>")

        if lower.startswith("search "):
            return filesystem.search_files(self.state.current_path, cmd[7:].strip())

        if lower.startswith("info "):
            return filesystem.file_info(self.state.current_path, cmd[5:].strip())

        if lower.startswith("create "):
            return filesystem.create_file(self.state.current_path, cmd[7:].strip())

        if lower.startswith("delete "):
            if self.is_blocked("delete"):
                return CommandResult.warning("Safe mode is ON. Use 'safe off' to enable this command.")
            name = cmd[7:].strip()
            return CommandResult(
                level=CommandResult.error("").level,
                text=f"Delete '{name}'?",
                requires_confirmation=True,
                confirmation_prompt=f"Delete '{name}'? This cannot be undone.",
                data={"action": "delete_file", "name": name},
            )

        if lower == "cleanup":
            if self.is_blocked("cleanup"):
                return CommandResult.warning("Safe mode is ON. Use 'safe off' to enable this command.")
            return CommandResult(
                level=CommandResult.info("").level,
                text="Clean temporary files?",
                requires_confirmation=True,
                confirmation_prompt="Clean temporary files from Windows/User Temp folders?",
                data={"action": "cleanup"},
            )

        # Calculator
        if lower.startswith("calc "):
            return calc_cmd.evaluate(cmd[5:].strip())

        # DPA
        if first == "dpa" and len(parts) > 1:
            name = parts[1]
            key = parts[2] if len(parts) > 2 else None
            path = self._resolve(name)
            if not os.path.exists(path) and not name.lower().endswith(".dpa"):
                alt = path + ".dpa"
                if os.path.exists(alt):
                    path = alt
            return dpa_cmd.run_dpa(path, key, self.config.get("dpa_key"))

        if first == "encrypt" and len(parts) > 1:
            name = parts[1]
            key = parts[2] if len(parts) > 2 else None
            return dpa_cmd.encrypt_file(self._resolve(name), key)

        if first == "decrypt" and len(parts) > 1:
            name = parts[1]
            key = parts[2] if len(parts) > 2 else None
            return dpa_cmd.decrypt_file(self._resolve(name), key, self.config.get("dpa_key"))

        if lower.endswith(".dpa") and " " not in cmd:
            path = self._resolve(cmd)
            return dpa_cmd.run_dpa(path, None, self.config.get("dpa_key"))

        # System / debug
        if lower == "debug":
            return system_info.get_debug_info()

        # Power (all require confirmation — GUI must confirm before calling _confirmed_execute)
        if lower == "shutdown":
            if self.is_blocked("shutdown"):
                return CommandResult.warning("Safe mode is ON. Use 'safe off' to enable this command.")
            return CommandResult(
                level=CommandResult.info("").level, text="Shutdown computer?",
                requires_confirmation=True,
                confirmation_prompt="This will shut down your computer. Continue?",
                data={"action": "shutdown"},
            )
        if lower == "sleep":
            if self.is_blocked("sleep"):
                return CommandResult.warning("Safe mode is ON. Use 'safe off' to enable this command.")
            return CommandResult(
                level=CommandResult.info("").level, text="Sleep computer?",
                requires_confirmation=True,
                confirmation_prompt="Put the computer to sleep now?",
                data={"action": "sleep"},
            )
        if lower in ("restart", "restartsys"):
            if self.is_blocked("restart") or self.is_blocked("restartsys"):
                return CommandResult.warning("Safe mode is ON. Use 'safe off' to enable this command.")
            return CommandResult(
                level=CommandResult.info("").level, text="Restart computer?",
                requires_confirmation=True,
                confirmation_prompt="This will restart your computer. Continue?",
                data={"action": "restart"},
            )

        # Config / meta
        if lower == "safe":
            state = "ON" if self.config.get("safe_mode", True) else "OFF"
            return CommandResult.info(f"Safe mode is {state}")
        if lower in ("safe on", "safe off"):
            self.config.set("safe_mode", lower == "safe on")
            return CommandResult.success(f"Safe mode set to {'ON' if lower == 'safe on' else 'OFF'}")

        if lower == "plugins":
            return CommandResult.output("Loaded plugins", plugins=self.plugins.loaded)

        if lower == "history":
            return CommandResult.output("Command history", entries=self.history.all()[-20:])
        if lower == "history clear":
            self.history.clear()
            return CommandResult.success("History cleared")

        if lower.startswith("help"):
            topic = cmd.split(maxsplit=1)[1] if len(parts) > 1 else None
            return self._help(topic)

        # Plugin commands
        if self.plugins.has_command(first):
            self.plugins.execute(first, parts[1:], cmd)
            return CommandResult.success(f"Plugin command executed: {first}")

        # Bare filename / folder navigation
        if self.state.current_path:
            potential = os.path.join(self.state.current_path, cmd)
            if os.path.isdir(potential):
                self.state.current_path = potential
                return CommandResult.success(f"Entered folder: {potential}")
            if os.path.isfile(potential):
                ext = os.path.splitext(potential)[1].lower()
                if ext == ".dpa":
                    return dpa_cmd.run_dpa(potential, None, self.config.get("dpa_key"))
                return CommandResult.output("Open file with system default", path=potential, action="open_default")

        return CommandResult.error(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

    def confirmed_execute(self, action: str, data: dict) -> CommandResult:
        """Called by the GUI after the user confirms a destructive action."""
        if action == "delete_file":
            return filesystem.delete_file(self.state.current_path, data["name"])
        if action == "cleanup":
            return filesystem.system_cleanup()
        if action == "shutdown":
            return power.shutdown()
        if action == "sleep":
            return power.sleep()
        if action == "restart":
            return power.restart()
        return CommandResult.error("Unknown confirmation action")

    def _resolve(self, name: str) -> str:
        if os.path.isabs(name):
            return name
        if self.state.current_path:
            return os.path.join(self.state.current_path, name)
        return name

    def _resolve_pair(self, args: List[str]) -> tuple[str, str]:
        return self._resolve(args[0]), self._resolve(args[1])

    def _help(self, topic: Optional[str]) -> CommandResult:
        if not topic:
            entries = [
                {"names": c.names, "display": c.display, "desc": c.description, "icon": c.icon}
                for c in COMMAND_REGISTRY
            ]
            return CommandResult.output("Command reference", entries=entries)
        key = topic.lower()
        for c in COMMAND_REGISTRY:
            if key in [n.lower() for n in c.names]:
                return CommandResult.output(f"Help: {c.display}", description=c.description)
        return CommandResult.error(f"No help found for: {topic}")

    def all_command_names(self) -> List[str]:
        """Flat list of every command name, for the search dialog + autocomplete."""
        names: List[str] = []
        for c in COMMAND_REGISTRY:
            names.extend(c.names)
        names.extend(self.plugins.commands.keys())
        return sorted(set(names))
