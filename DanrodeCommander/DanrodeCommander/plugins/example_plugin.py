"""
plugins/example_plugin.py
Example plugin demonstrating the legacy-compatible plugin API.

Any .py file placed in plugins/ that exposes a `register(register_command)`
function will be auto-loaded by core.plugin_manager.PluginManager.
"""

from core.logger import logger


def _hello_command(args: list[str], raw: str) -> None:
    name = args[0] if args else "there"
    logger.success(f"Hello, {name}! (from example_plugin)")


def register(register_command) -> None:
    register_command("hello", _hello_command, "Say hello — example plugin command")
