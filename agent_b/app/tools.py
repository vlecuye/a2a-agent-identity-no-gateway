"""Tools and capabilities for Agent B (ADK 2.0)."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

# Supported operators for safe AST evaluation
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_MATH_FUNCS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
}

_SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _eval_ast(node: ast.AST) -> float | int:
    """Recursively evaluates safe mathematical AST nodes."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _OPERATORS:
            left = _eval_ast(node.left)
            right = _eval_ast(node.right)
            return _OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _OPERATORS:
            operand = _eval_ast(node.operand)
            return _OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    if isinstance(node, ast.Name):
        if node.id in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[node.id]
        raise ValueError(f"Unknown constant: {node.id}")
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        func_name = node.func.id
        if func_name in _SAFE_MATH_FUNCS:
            args = [_eval_ast(arg) for arg in node.args]
            return _SAFE_MATH_FUNCS[func_name](*args)
        raise ValueError(f"Unsupported function call: {func_name}")
    raise ValueError(f"Unsupported AST expression node: {type(node).__name__}")


def calculate_formula(formula: str) -> dict[str, Any]:
    """Evaluates an arithmetic or mathematical formula securely using AST parsing.

    Args:
        formula: A mathematical string expression to evaluate (e.g. '42 * 10 / 2', '2 ** 8', 'sqrt(144) + 10').

    Returns:
        A dictionary containing 'status', 'formula', and 'result' or 'error'.
    """
    cleaned_formula = formula.strip()
    if not cleaned_formula:
        return {
            "status": "error",
            "formula": formula,
            "error": "Empty formula string provided.",
        }

    try:
        parsed_ast = ast.parse(cleaned_formula, mode="eval")
        result = _eval_ast(parsed_ast.body)
        return {
            "status": "success",
            "formula": cleaned_formula,
            "result": result,
        }
    except Exception as exc:
        return {
            "status": "error",
            "formula": cleaned_formula,
            "error": f"Failed to evaluate expression: {exc}",
        }

