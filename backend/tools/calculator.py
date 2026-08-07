"""
tools/calculator.py
===================
Safe arithmetic calculator tool.

Uses Python's AST parser — never calls eval() on raw strings.
Supports: +  -  *  /  //  %  **  ( )  unary minus/plus
"""

import ast
import operator
from typing import Any

NAME        = "calculator"
DESCRIPTION = "Evaluates arithmetic expressions accurately. Use for ANY math: ×, ÷, +, -, %, powers, percentages."
PARAMETERS  = '{"expression": "<math expression as string, e.g. 245*88 or (100+50)/3>"}'

# ── Safe AST evaluator ────────────────────────────────────────────────────────

_OPERATORS: dict[type, Any] = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod:  operator.mod,
    ast.Pow:  operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left  = _eval_node(node.left)
        right = _eval_node(node.right)
        return _OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def _safe_eval(expression: str) -> float:
    """Parse and evaluate a math expression safely using AST."""
    # Normalise common natural-language math characters
    expression = (
        expression
        .replace("×", "*")
        .replace("÷", "/")
        .replace("x", "*")   # e.g. "5 x 10"
        .strip()
    )
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


# ── Tool interface ────────────────────────────────────────────────────────────

async def execute(args: dict) -> dict:
    """
    Args
    ----
    args["expression"] : str — the math expression to evaluate

    Returns
    -------
    {"name": "calculator", "success": True,  "result": "21560"}
    {"name": "calculator", "success": False, "error":  "..."}
    """
    expression = args.get("expression", "").strip()
    if not expression:
        return {"name": NAME, "success": False, "error": "No expression provided."}

    try:
        raw_result = _safe_eval(expression)

        # Format: integer if whole number, else up to 6 decimal places
        if raw_result == int(raw_result):
            formatted = f"{int(raw_result):,}"
        else:
            formatted = f"{raw_result:,.6f}".rstrip("0").rstrip(".")

        return {"name": NAME, "success": True, "result": formatted}

    except ZeroDivisionError:
        return {"name": NAME, "success": False, "error": "Division by zero."}
    except Exception as exc:
        return {"name": NAME, "success": False, "error": f"Could not evaluate '{expression}': {exc}"}
