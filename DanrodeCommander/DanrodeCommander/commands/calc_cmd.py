"""
commands/calc_cmd.py
Safe expression evaluator for the calculator command.
"""

from __future__ import annotations

import math

from core.result import CommandResult

_SAFE_NAMESPACE = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
    "tan": math.tan, "log": math.log, "log10": math.log10,
    "abs": abs, "pi": math.pi, "e": math.e,
    "pow": pow, "round": round,
    "floor": math.floor, "ceil": math.ceil,
}


def evaluate(expression: str) -> CommandResult:
    try:
        expr = expression.replace("^", "**")
        result = eval(expr, {"__builtins__": {}}, _SAFE_NAMESPACE)
        return CommandResult.success(str(result), value=result, expression=expression)
    except Exception as e:
        return CommandResult.error(f"Error: {e}")
