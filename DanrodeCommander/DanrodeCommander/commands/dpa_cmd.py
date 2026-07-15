"""
commands/dpa_cmd.py
DPA file commands (run / encrypt / decrypt), wired to core.dpa_engine.
Captures exec() stdout so the GUI can display script output in a panel
instead of a console.
"""

from __future__ import annotations

import io
import os
from contextlib import redirect_stdout
from typing import Optional

from core import dpa_engine
from core.result import CommandResult


def run_dpa(filepath: str, key: Optional[str] = None, config_key: Optional[str] = None) -> CommandResult:
    if not os.path.exists(filepath):
        return CommandResult.error(f"File not found: {filepath}")

    try:
        source = dpa_engine.decrypt_dpa(filepath, key, config_key)
    except Exception as e:
        return CommandResult.error(
            f"Failed to decrypt .dpa file: {e}. "
            "Tip: ensure the correct key is set in config (dpa_key) or supplied explicitly."
        )

    dpa_type = dpa_engine.detect_dpa_type(filepath)
    ns = {"__name__": "__main__", "__file__": filepath}
    buffer = io.StringIO()

    try:
        compiled = compile(source, filepath, "exec")
        with redirect_stdout(buffer):
            exec(compiled, ns)
        return CommandResult.success(
            "Script finished successfully!",
            dpa_type=dpa_type,
            stdout=buffer.getvalue(),
        )
    except SystemExit:
        return CommandResult.info("Script called sys.exit().", dpa_type=dpa_type, stdout=buffer.getvalue())
    except SyntaxError as e:
        hint = dpa_engine.suggest_fix(source, e)
        return CommandResult.error(
            f"SyntaxError: {e.msg} (line {e.lineno})",
            dpa_type=dpa_type, stdout=buffer.getvalue(), hint=hint,
        )
    except Exception as e:
        hint = dpa_engine.suggest_fix(source, e)
        return CommandResult.error(
            f"{type(e).__name__}: {e}",
            dpa_type=dpa_type, stdout=buffer.getvalue(), hint=hint,
        )


def view_dpa_source(filepath: str, key: Optional[str] = None, config_key: Optional[str] = None) -> CommandResult:
    if not os.path.exists(filepath):
        return CommandResult.error(f"File not found: {filepath}")
    try:
        source = dpa_engine.decrypt_dpa(filepath, key, config_key)
        return CommandResult.output("DPA source", source=source, filename=os.path.basename(filepath))
    except Exception as e:
        return CommandResult.error(f"Failed to decrypt: {e}")


def encrypt_file(py_path: str, key: Optional[str] = None) -> CommandResult:
    if not os.path.exists(py_path):
        return CommandResult.error(f"File not found: {py_path}")
    try:
        out_path = dpa_engine.encrypt_to_dpa(py_path, None, key)
        return CommandResult.success(f"Encrypted → {out_path}", output_path=out_path)
    except Exception as e:
        return CommandResult.error(f"Encryption failed: {e}")


def decrypt_file(dpa_path: str, key: Optional[str] = None, config_key: Optional[str] = None) -> CommandResult:
    if not os.path.exists(dpa_path):
        return CommandResult.error(f"File not found: {dpa_path}")
    try:
        source = dpa_engine.decrypt_dpa(dpa_path, key, config_key)
        return CommandResult.success("Decryption successful!", source=source)
    except Exception as e:
        return CommandResult.error(f"Decryption failed: {e}")
