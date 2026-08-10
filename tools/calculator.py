import ast
import operator as op

from tools.base import BaseTool


class CalculatorTool(BaseTool):
    """Safe arithmetic evaluator. No eval()."""

    OPERATORS = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.FloorDiv: op.floordiv,
        ast.Mod: op.mod,
        ast.Pow: op.pow,
        ast.USub: op.neg,
        ast.UAdd: op.pos,
    }

    def execute(self, expression):
        expression = str(expression).strip()
        if not expression:
            return "No expression provided."
        if len(expression) > 200:
            raise ValueError("Expression too long")
        tree = ast.parse(expression, mode="eval")
        return self._evaluate(tree.body)

    def _evaluate(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.OPERATORS:
            return self.OPERATORS[type(node.op)](self._evaluate(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in self.OPERATORS:
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("Exponent too large")
            return self.OPERATORS[type(node.op)](left, right)
        raise ValueError("Only arithmetic expressions are allowed")
