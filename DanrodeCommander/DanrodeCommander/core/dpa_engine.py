"""
core/dpa_engine.py
DPA (Danrode Python App) encryption engine — XOR + Base64.
Ported 1:1 from the original DCMDS.py so existing .dpa files stay compatible.
"""

from __future__ import annotations

import base64
import os
import re
import traceback
from typing import Optional

from core.config import DEFAULT_DPA_KEY

DPA_HEADER_PLAIN = "#DPA-PLAIN"
DPA_HEADER_XOR = "#DPA-XOR2"

_COMMON_TYPOS = {
    "ptint": "print", "pritn": "print", "prnit": "print", "prin": "print",
    "prnt": "print", "prit": "print",
    "imput": "input", "inpt": "input",
    "improt": "import", "imort": "import", "imprort": "import",
    "retrun": "return", "retunr": "return", "reutrn": "return",
    "esle": "else", "eles": "else",
    "Tru": "True", "Flase": "False", "Fasle": "False", "ture": "True",
    "Non": "None", "none": "None",
}


def get_key_hint(key: str) -> str:
    """Public hint of the key (Base64 of first 3 chars)."""
    return base64.b64encode(key[:3].encode()).decode()


def xor_encode(plaintext: str, key: str) -> str:
    pb = plaintext.encode("utf-8")
    kb = key.encode("utf-8") or DEFAULT_DPA_KEY.encode("utf-8")
    out = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(pb))
    return base64.b64encode(out).decode("ascii")


def xor_decode(ciphertext: str, key: str) -> str:
    raw = base64.b64decode(ciphertext.encode("ascii"))
    kb = key.encode("utf-8") or DEFAULT_DPA_KEY.encode("utf-8")
    out = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw))
    return out.decode("utf-8")


def encrypt_to_dpa(py_path: str, dpa_path: Optional[str] = None, key: Optional[str] = None) -> str:
    key = key or DEFAULT_DPA_KEY
    with open(py_path, "r", encoding="utf-8") as f:
        source = f.read()
    if dpa_path is None:
        base, _ = os.path.splitext(py_path)
        dpa_path = base + ".dpa"
    encoded = xor_encode(source, key)
    hint = get_key_hint(key)
    chunks = [encoded[i:i + 76] for i in range(0, len(encoded), 76)]
    with open(dpa_path, "w", encoding="utf-8") as f:
        f.write(f"{DPA_HEADER_XOR} {hint}\n")
        f.write("\n".join(chunks) + "\n")
    return dpa_path


def decrypt_dpa(dpa_path: str, key: Optional[str] = None, config_key: Optional[str] = None) -> str:
    with open(dpa_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    if not lines:
        raise ValueError("Empty .dpa file")

    header = lines[0].strip()
    body = "\n".join(lines[1:])

    if header == DPA_HEADER_PLAIN:
        return body

    if header.startswith("#DPA-XOR"):
        parts = header.split()
        if len(parts) > 1 and not key:
            hint = parts[1]
            if hint == get_key_hint(DEFAULT_DPA_KEY):
                key = DEFAULT_DPA_KEY
            elif config_key and hint == get_key_hint(config_key):
                key = config_key
        if not key:
            key = config_key or DEFAULT_DPA_KEY
        encoded = "".join(body.split())
        return xor_decode(encoded, key)

    return content


def detect_dpa_type(dpa_path: str) -> str:
    try:
        with open(dpa_path, "r", encoding="utf-8") as f:
            first = f.readline().strip()
    except Exception:
        return "unknown"
    # Header may be "#DPA-XOR2" alone or "#DPA-XOR2 <keyhint>"
    if first == DPA_HEADER_PLAIN:
        return "plain"
    first_token = first.split()[0] if first else ""
    if first_token == DPA_HEADER_XOR:
        return "encrypted"
    return "legacy"


def suggest_fix(source: str, error: Exception) -> str:
    """Return a friendly fix hint string for common Python errors."""
    src_lines = source.splitlines()
    msg = str(error)
    hint_lines = []

    if isinstance(error, SyntaxError) and error.lineno:
        ln = error.lineno
        if 1 <= ln <= len(src_lines):
            bad = src_lines[ln - 1]
            hint_lines.append(f"Line {ln}: {bad}")
            if "unterminated" in msg.lower() or "EOL while scanning" in msg:
                fixed = bad
                if bad.count('"') % 2 == 1:
                    fixed = bad + '"'
                elif bad.count("'") % 2 == 1:
                    fixed = bad + "'"
                hint_lines.append(f"Try: {fixed}")
                return "\n".join(hint_lines)
            if bad.count("(") > bad.count(")"):
                hint_lines.append(f"Try: {bad + ')' * (bad.count('(') - bad.count(')'))}")
                return "\n".join(hint_lines)
            hint_lines.append("Check brackets, quotes, and colons on this line.")
            return "\n".join(hint_lines)

    if isinstance(error, NameError):
        m = re.search(r"name '([^']+)' is not defined", msg)
        if m:
            bad_name = m.group(1)
            if bad_name in _COMMON_TYPOS:
                fix = _COMMON_TYPOS[bad_name]
                hint_lines.append(f"'{bad_name}' is not a function. Did you mean: {fix}?")
                for i, ln in enumerate(src_lines, 1):
                    if bad_name in ln:
                        hint_lines.append(f"Line {i}: {ln}")
                        hint_lines.append(f"Try: {ln.replace(bad_name, fix)}")
                        break
                return "\n".join(hint_lines)
            hint_lines.append(f"'{bad_name}' is not defined. Check spelling or define it first.")
            return "\n".join(hint_lines)

    hint_lines.append(msg)
    return "\n".join(hint_lines)


def run_dpa_source(filepath: str, key: Optional[str] = None, config_key: Optional[str] = None) -> tuple[bool, str]:
    """
    Decrypt and execute a .dpa file.
    Returns (success, output_or_error_text). Execution output is captured via
    stdout redirection by the caller (see commands/dpa_cmd.py).
    """
    try:
        source = decrypt_dpa(filepath, key, config_key)
    except Exception as e:
        return False, f"Failed to decrypt .dpa file: {e}"

    ns = {"__name__": "__main__", "__file__": filepath}
    try:
        compiled = compile(source, filepath, "exec")
        exec(compiled, ns)
        return True, "Script finished successfully!"
    except SystemExit:
        return True, "Script called sys.exit()."
    except SyntaxError as e:
        hint = suggest_fix(source, e)
        return False, f"SyntaxError: {e.msg} (line {e.lineno})\n{hint}"
    except Exception as e:
        tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
        tb_text = "".join(tb_lines[-3:])
        hint = suggest_fix(source, e)
        return False, f"{type(e).__name__}: {e}\n{tb_text}\n{hint}"
