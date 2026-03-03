import ast
import operator
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool

SAFE_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return SAFE_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp):
        return SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


@register_tool("calculator")
class CalculatorTool(SynthTool):
    name: str = "calculator"
    description: str = "Evaluate a mathematical expression. Input: math expression string like '2 + 3 * 4'."

    def _run(self, expression: str) -> str:
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            result = _safe_eval(tree.body)
            return str(result)
        except Exception as e:
            return f"Calculation error: {e}"

    async def _arun(self, expression: str) -> str:
        return self._run(expression)
