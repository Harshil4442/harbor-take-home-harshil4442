"""Safe arithmetic expression evaluator for pipeline transforms."""

import ast
import operator


SAFE_OPERATORS = {
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


def evaluate_expression(expr, context):
    """Evaluate an arithmetic expression with field references.

    Field names in the expression are resolved from the context
    dict. Missing fields resolve to 0.
    """
    try:
        tree = ast.parse(expr, mode="eval")
        return _eval_node(tree.body, context)
    except (SyntaxError, TypeError, ZeroDivisionError) as exc:
        raise ValueError(
            f"Failed to evaluate expression '{expr}': {exc}"
        ) from exc


def _eval_node(node, context):
    """Recursively evaluate an AST node."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(
            f"Unsupported constant type: "
            f"{type(node.value).__name__}"
        )

    if isinstance(node, ast.Name):
        return context.get(node.id, 0)

    if isinstance(node, ast.BinOp):
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(
                f"Unsupported operator: "
                f"{type(node.op).__name__}"
            )
        left = _eval_node(node.left, context)
        right = _eval_node(node.right, context)
        return op_func(left, right)

    if isinstance(node, ast.UnaryOp):
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(
                f"Unsupported unary operator: "
                f"{type(node.op).__name__}"
            )
        operand = _eval_node(node.operand, context)
        return op_func(operand)

    raise ValueError(
        f"Unsupported expression node: "
        f"{type(node).__name__}"
    )
