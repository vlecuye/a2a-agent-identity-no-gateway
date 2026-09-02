"""Tools and capabilities for Agent B."""


def calculate_formula(formula: str) -> str:
    """Safely evaluates an arithmetic expression for mathematical calculations.

    Args:
        formula: A mathematical string expression (e.g. '42 * 10 / 2', '2 ** 8').

    Returns:
        The evaluated result as a string, or an error message.
    """
    allowed_chars = set("0123456789+-*/(). %^")
    if not all(c in allowed_chars for c in formula):
        return f"Error: Formula contains invalid characters: '{formula}'"
    try:
        # Evaluate simple arithmetic safely
        result = eval(formula, {"__builtins__": None}, {})
        return str(result)
    except Exception as exc:
        return f"Error calculating formula '{formula}': {exc}"
